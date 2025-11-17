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
消息格式化服务

本模块负责将 GitHub Webhook 事件格式化为可发送的消息。

作者：AptS:1547
版本：0.2.0
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

from typing import List, Dict, Any

from app.models.message import MessageSegment
from app.models.webhook_event import (
    PushEventData,
    PullRequestEventData,
    IssueEventData,
    ReleaseEventData,
    IssueCommentEventData
)


class MessageFormatter:
    """
    消息格式化器。

    负责将各类 GitHub Webhook 事件数据格式化为 OneBot 消息。
    """

    @staticmethod
    def format_push_event(event: PushEventData) -> List[Dict[str, Any]]:
        """
        格式化 Push 事件消息。

        Args:
            event: Push 事件数据

        Returns:
            List[Dict[str, Any]]: 消息段列表
        """
        message = [
            MessageSegment.text("📢 GitHub 推送通知\n"),
            MessageSegment.text(f"仓库：{event.repo_name}\n"),
            MessageSegment.text(f"分支：{event.branch}\n"),
            MessageSegment.text(f"推送者：{event.pusher}\n"),
            MessageSegment.text(f"提交数量：{event.commit_count}\n\n"),
            MessageSegment.text("最新提交：\n")
        ]

        # 最多展示3条最新提交
        for commit in event.commits[:3]:
            short_id = commit.id[:7]
            commit_message = commit.message.split("\n")[0]  # 只取第一行
            author = commit.author.name

            message.append(
                MessageSegment.text(
                    f"[{short_id}] {commit_message} (by {author})\n"
                )
            )

        return message

    @staticmethod
    def format_pull_request_event(
        event: PullRequestEventData
    ) -> List[Dict[str, Any]]:
        """
        格式化 Pull Request 事件消息。

        Args:
            event: Pull Request 事件数据

        Returns:
            List[Dict[str, Any]]: 消息段列表
        """
        # 针对不同动作定制消息内容
        action_text_map = {
            "opened": "创建了",
            "closed": "关闭了",
            "reopened": "重新打开了",
            "assigned": "被分配了",
            "unassigned": "被取消分配了",
            "review_requested": "请求审核",
            "review_request_removed": "取消审核请求",
            "labeled": "被添加了标签",
            "unlabeled": "被移除了标签",
            "synchronize": "同步了",
        }

        # 特殊处理 closed 事件
        if event.action == "closed" and event.pull_request.merged:
            action_text = "合并了"
        else:
            action_text = action_text_map.get(event.action, event.action)

        message = [
            MessageSegment.text(f"📢 GitHub Pull Request {action_text}\n"),
            MessageSegment.text(f"仓库：{event.repo_name}\n"),
            MessageSegment.text(
                f"PR #{event.pull_request.number}: {event.pull_request.title}\n"
            ),
            MessageSegment.text(f"用户：{event.user}\n"),
            MessageSegment.text(f"状态：{event.pull_request.state}\n")
        ]

        # 添加分支信息
        if event.pull_request.base_branch and event.pull_request.head_branch:
            message.append(
                MessageSegment.text(
                    f"目标分支：{event.pull_request.base_branch} "
                    f"← {event.pull_request.head_branch}\n"
                )
            )

        # 添加链接
        if event.pull_request.html_url:
            message.append(
                MessageSegment.text(f"链接：{event.pull_request.html_url}\n")
            )

        return message

    @staticmethod
    def format_issue_event(event: IssueEventData) -> List[Dict[str, Any]]:
        """
        格式化 Issue 事件消息。

        Args:
            event: Issue 事件数据

        Returns:
            List[Dict[str, Any]]: 消息段列表
        """
        # 针对不同动作定制消息内容
        action_text_map = {
            "opened": "创建了",
            "closed": "关闭了",
            "reopened": "重新打开了",
            "assigned": "被分配了",
            "unassigned": "被取消分配了",
            "labeled": "被添加了标签",
            "unlabeled": "被移除了标签",
        }

        action_text = action_text_map.get(event.action, event.action)

        message = [
            MessageSegment.text(f"📢 GitHub Issue {action_text}\n"),
            MessageSegment.text(f"仓库：{event.repo_name}\n"),
            MessageSegment.text(
                f"Issue #{event.issue.number}: {event.issue.title}\n"
            ),
            MessageSegment.text(f"用户：{event.user}\n"),
            MessageSegment.text(f"状态：{event.issue.state}\n")
        ]

        # 添加标签信息
        if event.issue.labels:
            label_names = ", ".join(event.issue.labels)
            message.append(MessageSegment.text(f"标签：{label_names}\n"))

        # 添加链接
        if event.issue.html_url:
            message.append(
                MessageSegment.text(f"链接：{event.issue.html_url}\n")
            )

        return message

    @staticmethod
    def format_release_event(event: ReleaseEventData) -> List[Dict[str, Any]]:
        """
        格式化 Release 事件消息。

        Args:
            event: Release 事件数据

        Returns:
            List[Dict[str, Any]]: 消息段列表
        """
        # 针对不同动作定制消息内容
        action_text_map = {
            "published": "发布了",
            "created": "创建了",
            "edited": "编辑了",
            "deleted": "删除了",
            "prereleased": "预发布了",
            "released": "正式发布了",
        }

        action_text = action_text_map.get(event.action, event.action)

        message = [
            MessageSegment.text(f"📢 GitHub Release {action_text}\n"),
            MessageSegment.text(f"仓库：{event.repo_name}\n"),
            MessageSegment.text(
                f"版本：{event.release.name} ({event.release.tag_name})\n"
            ),
            MessageSegment.text(f"发布者：{event.user}\n")
        ]

        # 添加预发布信息
        if event.release.prerelease:
            message.append(MessageSegment.text("类型：预发布\n"))

        # 添加发布时间
        if event.release.published_at:
            message.append(
                MessageSegment.text(f"发布时间：{event.release.published_at}\n")
            )

        # 添加链接
        if event.release.html_url:
            message.append(
                MessageSegment.text(f"链接：{event.release.html_url}\n")
            )

        return message

    @staticmethod
    def format_issue_comment_event(
        event: IssueCommentEventData
    ) -> List[Dict[str, Any]]:
        """
        格式化 Issue/PR 评论事件消息。

        Args:
            event: Issue Comment 事件数据

        Returns:
            List[Dict[str, Any]]: 消息段列表
        """
        # 针对不同动作定制消息内容
        action_text_map = {
            "created": "发表了",
            "edited": "编辑了",
            "deleted": "删除了",
        }

        action_text = action_text_map.get(event.action, event.action)

        # 判断是PR还是Issue
        issue_type = "PR" if event.is_pull_request else "Issue"

        message = [
            MessageSegment.text(f"📢 GitHub {issue_type}评论 {action_text}\n"),
            MessageSegment.text(f"仓库：{event.repo_name}\n"),
            MessageSegment.text(f"{issue_type} #{event.issue_number}\n"),
            MessageSegment.text(f"用户：{event.user}\n")
        ]

        # 添加评论内容预览
        if event.comment.body and event.action != "deleted":
            # 截取评论内容，最多显示100个字符
            preview = event.comment.body[:100]
            if len(event.comment.body) > 100:
                preview += "..."
            preview = preview.replace("\n", " ")
            message.append(MessageSegment.text(f"内容：{preview}\n"))

        # 添加链接
        if event.comment.html_url:
            message.append(
                MessageSegment.text(f"链接：{event.comment.html_url}\n")
            )

        return message
