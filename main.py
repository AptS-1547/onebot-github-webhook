# Copyright 2025 AptS-1547
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
OneBot GitHub Webhook 入口文件
本文件用于接收 GitHub Webhook 事件，并将其转发到配置的 OneBot 目标。
作者：AptS:1547
版本：0.1.0-alpha
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException

from app.models.config import Config
from app.core.onebot import text
from app.core.onebot import OneBotWebSocketClient, OneBotHTTPClient
from app.core.github import verify_signature, find_matching_webhook, extract_push_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载配置
config = Config().from_yaml()

ONEBOT_CLIENT = None

@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    管理应用程序生命周期的上下文管理器
    在应用启动时初始化资源，在应用关闭时释放资源
    """

    global ONEBOT_CLIENT       # pylint: disable=global-statement

    # 创建 OneBot 客户端
    if config.ONEBOT_TYPE == "ws":
        ONEBOT_CLIENT = OneBotWebSocketClient(config.ONEBOT_URL, config.ONEBOT_ACCESS_TOKEN)

        # 启动 WebSocket 连接
        logger.info("正在初始化 WebSocket 连接...")
        try:
            await ONEBOT_CLIENT.manager.start()
            logger.info("WebSocket 连接已成功建立")
        except Exception as e:  # pylint: disable=broad-except
            logger.error("建立 WebSocket 连接失败: %s", e)
            sys.exit(1)
    elif config.ONEBOT_TYPE == "http":
        ONEBOT_CLIENT = OneBotHTTPClient(config.ONEBOT_URL, config.ONEBOT_ACCESS_TOKEN)

    yield  # 这里是应用程序运行的地方

    # 清理资源
    if isinstance(ONEBOT_CLIENT, OneBotWebSocketClient):
        logger.info("正在关闭 WebSocket 连接...")
        try:
            await ONEBOT_CLIENT.manager.stop()
            logger.info("WebSocket 连接已成功关闭")
        except Exception as e:  # pylint: disable=broad-except
            logger.error("关闭 WebSocket 连接时出错: %s", e)


app = FastAPI(lifespan=lifespan)


@app.post("/github-webhook")
async def github_webhook(request: Request):      # pylint: disable=too-many-return-statements
    """处理 GitHub webhook 请求"""

    content_type = request.headers.get("Content-Type")
    if content_type != "application/json":
        logger.info("收到非 JSON 格式的请求，忽略")
        return {"status": "ignored", "message": "只处理 application/json 格式的请求"}

    event_type = request.headers.get("X-GitHub-Event", "")
    if not event_type:
        logger.info("缺少 X-GitHub-Event 头，忽略")
        return {"status": "ignored", "message": "缺少 X-GitHub-Event 头"}

    try:
        await verify_signature(
            request,
            config.GITHUB_WEBHOOK,
            request.headers.get("X-Hub-Signature-256")
        )
    except HTTPException as e:
        logger.info("签名验证失败: %s", e.detail)
        return {"status": "ignored", "message": f"签名验证失败: {e.detail}"}

    payload = await request.json()
    if not payload:
        logger.info("请求体为空，忽略")
        return {"status": "ignored", "message": "请求体为空"}

    repo_name = payload.get("repository", {}).get("full_name")
    branch = payload.get("ref", "").replace("refs/heads/", "")

    matched_webhook = find_matching_webhook(
        repo_name,
        branch,
        event_type,
        config.GITHUB_WEBHOOK
    )

    if not matched_webhook:
        logger.info("找不到匹配的 webhook 配置: 仓库 %s, 分支 %s, 事件类型 %s", repo_name, branch, event_type)
        return {"status": "ignored", "message": "找不到匹配的 webhook 配置"}

    # 处理不同类型的事件，暂时只支持 push 事件
    if event_type == "push":
        push_data = extract_push_data(payload)

        logger.info("发现新的 push 事件，来自 %s 仓库", push_data["repo_name"])
        logger.info("分支: %s，推送者: %s，提交数量: %s",
                   push_data["branch"],
                   push_data["pusher"],
                   push_data["commit_count"])

        # 向配置的所有 OneBot 目标发送通知
        for target in matched_webhook.ONEBOT:
            logger.info("正在发送消息到 QQ %s %s", target.type, target.id)

            message = format_github_push_message(
                repo_name=push_data["repo_name"],
                branch=push_data["branch"],
                pusher=push_data["pusher"],
                commit_count=push_data["commit_count"],
                commits=push_data["commits"]
            )

            # 使用已有的客户端发送消息
            await ONEBOT_CLIENT.send_message(target.type, target.id, message)

        return {"status": "success", "message": "处理 push 事件成功"}

    logger.info("收到 %s 事件，但尚未实现处理逻辑", event_type)
    return {"status": "ignored", "message": f"暂不处理 {event_type} 类型的事件"}


def format_github_push_message(repo_name, branch, pusher, commit_count, commits):
    """格式化 GitHub 推送消息"""

    message = [
        text("📢 GitHub 推送通知\n"),
        text(f"仓库：{repo_name}\n"),
        text(f"分支：{branch}\n"),
        text(f"推送者：{pusher}\n"),
        text(f"提交数量：{commit_count}\n\n"),
        text("最新提交：\n")
    ]

    # 最多展示3条最新提交
    for commit in commits[:3]:
        short_id = commit["id"][:7]
        commit_message = commit["message"].split("\n")[0]  # 只取第一行
        author = commit.get("author", {}).get("name", "未知")

        message.append(text(f"[{short_id}] {commit_message} (by {author})\n"))

    return message


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
