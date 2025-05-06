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
async def github_webhook(request: Request):
    """处理 GitHub webhook 请求"""
    # TODO: 为了后期使用自定义模版，作为临时过渡，需要完全重构

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

    payload = await request.json()
    if not payload:
        logger.info("请求体为空，忽略")
        return {"status": "ignored", "message": "请求体为空"}

    try:
        await GitHubWebhookHandler.verify_signature(
            request,
            config.GITHUB_WEBHOOK,
            request.headers.get("X-Hub-Signature-256")
        )
    except HTTPException as e:
        logger.info("签名验证失败: %s", e.detail)
        return {"status": "ignored", "message": f"签名验证失败: {e.detail}"}

    repo_name = payload.get("repository", {}).get("full_name")

    # 根据事件类型获取分支/PR/Issue信息用于匹配
    match_info = {}
    if event_type == "push":
        match_info["branch"] = payload.get("ref", "").replace("refs/heads/", "")

    matched_webhook = GitHubWebhookHandler.find_matching_webhook(
        repo_name,
        match_info.get("branch", ""),
        event_type,
        config.GITHUB_WEBHOOK
    )

    if not matched_webhook:
        logger.info("找不到匹配的 webhook 配置: 仓库 %s, 事件类型 %s", repo_name, event_type)
        return {"status": "ignored", "message": "找不到匹配的 webhook 配置"}

    message = None

    # 处理不同类型的事件
    if event_type == "push":
        push_data = GitHubWebhookHandler.extract_push_data(payload)

        logger.info("发现新的 push 事件，来自 %s 仓库", push_data["repo_name"])
        logger.info("分支: %s，推送者: %s，提交数量: %s",
                   push_data["branch"],
                   push_data["pusher"],
                   push_data["commit_count"])

        message = format_github_push_message(
            repo_name=push_data["repo_name"],
            branch=push_data["branch"],
            pusher=push_data["pusher"],
            commit_count=push_data["commit_count"],
            commits=push_data["commits"]
        )

    elif event_type == "pull_request":
        pr_data = GitHubWebhookHandler.extract_pull_request_data(payload)

        logger.info("发现新的 pull_request 事件，来自 %s 仓库", pr_data["repo_name"])
        logger.info("PR #%s, 操作: %s, 用户: %s",
                   pr_data["pull_request_number"],
                   pr_data["action"],
                   pr_data["user"])

        message = format_github_pull_request_message(
            repo_name=pr_data["repo_name"],
            action=pr_data["action"],
            pull_request=pr_data["pull_request"],
            user=pr_data["user"]
        )

    elif event_type == "issues":
        issue_data = GitHubWebhookHandler.extract_issue_data(payload)

        logger.info("发现新的 issue 事件，来自 %s 仓库", issue_data["repo_name"])
        logger.info("Issue #%s, 操作: %s, 用户: %s",
                   issue_data["issue_number"],
                   issue_data["action"],
                   issue_data["user"])

        message = format_github_issue_message(
            repo_name=issue_data["repo_name"],
            action=issue_data["action"],
            issue=issue_data["issue"],
            user=issue_data["user"]
        )

    elif event_type == "release":
        release_data = GitHubWebhookHandler.extract_release_data(payload)

        logger.info("发现新的 release 事件，来自 %s 仓库", release_data["repo_name"])
        logger.info("版本: %s, 操作: %s, 用户: %s", 
                   release_data["release_tag"], 
                   release_data["action"], 
                   release_data["user"])

        message = format_github_release_message(
            repo_name=release_data["repo_name"],
            action=release_data["action"],
            release=release_data["release"],
            user=release_data["user"]
        )

    elif event_type == "issue_comment":
        comment_data = GitHubWebhookHandler.extract_issue_comment_data(payload)

        logger.info("发现新的 issue_comment 事件，来自 %s 仓库", comment_data["repo_name"])
        logger.info("Issue #%s, 操作: %s, 用户: %s",
                   comment_data["issue_number"],
                   comment_data["action"],
                   comment_data["user"])

        message = format_github_issue_comment_message(
            repo_name=comment_data["repo_name"],
            action=comment_data["action"],
            comment=comment_data["comment"],
            issue_number=comment_data["issue_number"],
            user=comment_data["user"]
        )
    else:
        logger.info("收到 %s 事件，但尚未实现处理逻辑", event_type)
        return {"status": "ignored", "message": f"暂不处理 {event_type} 类型的事件"}

    if message:
        # 向配置的所有 OneBot 目标发送通知
        for target in matched_webhook.ONEBOT:
            logger.info("正在发送消息到 QQ %s %s", target.type, target.id)
            await onebot_client.send_message(target.type, target.id, message)

        return {"status": "success", "message": f"处理 {event_type} 事件成功"}

    return {"status": "failed", "message": "处理事件时发生错误"}


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

def format_github_pull_request_message(repo_name, action, pull_request, user):
    """格式化 GitHub Pull Request 消息"""

    # 针对不同动作定制消息内容
    action_text = {
        "opened": "创建了",
        "closed": "关闭了" if not pull_request.get("merged") else "合并了",
        "reopened": "重新打开了",
        "assigned": "被分配了",
        "unassigned": "被取消分配了",
        "review_requested": "请求审核",
        "review_request_removed": "取消审核请求",
        "labeled": "被添加了标签",
        "unlabeled": "被移除了标签",
        "synchronize": "同步了",
    }.get(action, action)

    message = [
        MessageSegment.text(f"📢 GitHub Pull Request {action_text}\n"),
        MessageSegment.text(f"仓库：{repo_name}\n"),
        MessageSegment.text(f"PR #{pull_request.get('number')}: {pull_request.get('title')}\n"),
        MessageSegment.text(f"用户：{user}\n"),
        MessageSegment.text(f"状态：{pull_request.get('state')}\n")
    ]

    # 添加分支信息
    base = pull_request.get("base", {}).get("ref", "")
    head = pull_request.get("head", {}).get("ref", "")
    if base and head:
        message.append(MessageSegment.text(f"目标分支：{base} ← {head}\n"))

    # 添加链接
    if pull_request.get("html_url"):
        message.append(MessageSegment.text(f"链接：{pull_request.get('html_url')}\n"))

    return message

def format_github_issue_message(repo_name, action, issue, user):
    """格式化 GitHub Issue 消息"""

    # 针对不同动作定制消息内容
    action_text = {
        "opened": "创建了",
        "closed": "关闭了",
        "reopened": "重新打开了",
        "assigned": "被分配了",
        "unassigned": "被取消分配了",
        "labeled": "被添加了标签",
        "unlabeled": "被移除了标签",
    }.get(action, action)

    message = [
        MessageSegment.text(f"📢 GitHub Issue {action_text}\n"),
        MessageSegment.text(f"仓库：{repo_name}\n"),
        MessageSegment.text(f"Issue #{issue.get('number')}: {issue.get('title')}\n"),
        MessageSegment.text(f"用户：{user}\n"),
        MessageSegment.text(f"状态：{issue.get('state')}\n")
    ]

    # 添加标签信息
    labels = issue.get("labels", [])
    if labels:
        label_names = [label.get("name", "") for label in labels]
        message.append(MessageSegment.text(f"标签：{', '.join(label_names)}\n"))

    # 添加链接
    if issue.get("html_url"):
        message.append(MessageSegment.text(f"链接：{issue.get('html_url')}\n"))

    return message

def format_github_release_message(repo_name, action, release, user):
    """格式化 GitHub Release 消息"""

    # 针对不同动作定制消息内容
    action_text = {
        "published": "发布了",
        "created": "创建了",
        "edited": "编辑了",
        "deleted": "删除了",
        "prereleased": "预发布了",
        "released": "正式发布了",
    }.get(action, action)

    tag_name = release.get("tag_name", "")
    name = release.get("name", tag_name) if release.get("name") else tag_name

    message = [
        MessageSegment.text(f"📢 GitHub Release {action_text}\n"),
        MessageSegment.text(f"仓库：{repo_name}\n"),
        MessageSegment.text(f"版本：{name} ({tag_name})\n"),
        MessageSegment.text(f"发布者：{user}\n")
    ]

    # 添加预发布信息
    if release.get("prerelease"):
        message.append(MessageSegment.text("类型：预发布\n"))

    # 添加发布时间
    if release.get("published_at"):
        published_time = release.get("published_at")
        message.append(MessageSegment.text(f"发布时间：{published_time}\n"))

    # 添加链接
    if release.get("html_url"):
        message.append(MessageSegment.text(f"链接：{release.get('html_url')}\n"))

    return message

def format_github_issue_comment_message(repo_name, action, comment, issue_number, user):
    """格式化 GitHub Issue/PR 评论消息"""

    # 针对不同动作定制消息内容
    action_text = {
        "created": "发表了",
        "edited": "编辑了",
        "deleted": "删除了",
    }.get(action, action)

    # 判断是PR还是Issue
    issue_type = "PR" if comment.get("pull_request") else "Issue"

    message = [
        MessageSegment.text(f"📢 GitHub {issue_type}评论 {action_text}\n"),
        MessageSegment.text(f"仓库：{repo_name}\n"),
        MessageSegment.text(f"{issue_type} #{issue_number}\n"),
        MessageSegment.text(f"用户：{user}\n")
    ]

    # 添加评论内容预览
    body = comment.get("body", "")
    if body and action != "deleted":
        # 截取评论内容，最多显示100个字符
        preview = body[:100] + "..." if len(body) > 100 else body
        preview = preview.replace("\n", " ")
        message.append(MessageSegment.text(f"内容：{preview}\n"))

    # 添加链接
    if comment.get("html_url"):
        message.append(MessageSegment.text(f"链接：{comment.get('html_url')}\n"))

    return message
