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
GitHub Webhook 路由模块
本模块用于处理 GitHub Webhook 事件，并将其转发到配置的 OneBot 目标。
作者：AptS:1547
版本：0.1.0-alpha
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

import logging
from fastapi import APIRouter, Request, HTTPException

from app.core import GitHubWebhookHandler
from app.botclient import BotClient
from app.models import MessageSegment
from app.models.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)

config = get_settings()

@router.post("")
async def github_webhook(
    request: Request,
):      # pylint: disable=too-many-return-statements
    """处理 GitHub webhook 请求"""

    onebot_client = BotClient.get_client("onebot")

    if not onebot_client:
        logger.error("OneBot 客户端未初始化，无法处理请求")
        raise HTTPException(status_code=503, detail="OneBot 客户端未初始化")

    content_type = request.headers.get("Content-Type")
    if content_type != "application/json":
        logger.info("收到非 JSON 格式的请求，忽略")
        return {"status": "ignored", "message": "只处理 application/json 格式的请求"}

    event_type = request.headers.get("X-GitHub-Event", "")
    if not event_type:
        logger.info("缺少 X-GitHub-Event 头，忽略")
        return {"status": "ignored", "message": "缺少 X-GitHub-Event 头"}

    try:
        await GitHubWebhookHandler.verify_signature(
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

    matched_webhook = GitHubWebhookHandler.find_matching_webhook(
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
        push_data = GitHubWebhookHandler.extract_push_data(payload)

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
            await onebot_client.send_message(target.type, target.id, message)

        return {"status": "success", "message": "处理 push 事件成功"}

    logger.info("收到 %s 事件，但尚未实现处理逻辑", event_type)
    return {"status": "ignored", "message": f"暂不处理 {event_type} 类型的事件"}


def format_github_push_message(repo_name, branch, pusher, commit_count, commits):
    """格式化 GitHub 推送消息"""

    message = [
        MessageSegment.text("📢 GitHub 推送通知\n"),
        MessageSegment.text(f"仓库：{repo_name}\n"),
        MessageSegment.text(f"分支：{branch}\n"),
        MessageSegment.text(f"推送者：{pusher}\n"),
        MessageSegment.text(f"提交数量：{commit_count}\n\n"),
        MessageSegment.text("最新提交：\n")
    ]

    # 最多展示3条最新提交
    for commit in commits[:3]:
        short_id = commit["id"][:7]
        commit_message = commit["message"].split("\n")[0]  # 只取第一行
        author = commit.get("author", {}).get("name", "未知")

        message.append(MessageSegment.text(f"[{short_id}] {commit_message} (by {author})\n"))

    return message
