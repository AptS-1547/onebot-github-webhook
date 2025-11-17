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
Webhook 服务层

本模块提供 GitHub Webhook 事件的处理编排逻辑。

作者：AptS:1547
版本：0.2.0
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

from typing import Dict, Any

from app.botclient.manager import BotClientManager
from app.models.config import Config, WebhookConfig
from app.models.webhook_event import (
    PushEventData,
    PullRequestEventData,
    IssueEventData,
    ReleaseEventData,
    IssueCommentEventData
)
from app.services.message_formatter import MessageFormatter
from app.utils.logger import StructuredLogger
from app.exceptions import BotClientError

logger = StructuredLogger(__name__)


class WebhookService:
    """
    Webhook 服务类。

    负责处理 GitHub Webhook 事件，包括解析事件、格式化消息和发送通知。

    Attributes:
        config: 应用配置实例
        formatter: 消息格式化器实例
    """

    def __init__(self, config: Config) -> None:
        """
        初始化 Webhook 服务。

        Args:
            config: 应用配置实例
        """
        self.config = config
        self.formatter = MessageFormatter()

    async def process_push_event(
        self,
        payload: Dict[str, Any],
        webhook_config: WebhookConfig
    ) -> bool:
        """
        处理 Push 事件。

        Args:
            payload: GitHub Webhook payload
            webhook_config: 匹配的 Webhook 配置

        Returns:
            bool: 处理成功返回 True
        """
        try:
            # 解析事件数据
            event = PushEventData.from_payload(payload)

            logger.log_event_processing(
                "push",
                event.repo_name,
                True,
                {
                    "branch": event.branch,
                    "commit_count": event.commit_count,
                    "pusher": event.pusher
                }
            )

            # 格式化消息
            message = self.formatter.format_push_event(event)

            # 发送到所有配置的目标
            return await self._send_to_targets(message, webhook_config)

        except Exception as e:
            logger.log_event_processing(
                "push",
                payload.get("repository", {}).get("full_name", "未知"),
                False,
                error=str(e)
            )
            return False

    async def process_pull_request_event(
        self,
        payload: Dict[str, Any],
        webhook_config: WebhookConfig
    ) -> bool:
        """
        处理 Pull Request 事件。

        Args:
            payload: GitHub Webhook payload
            webhook_config: 匹配的 Webhook 配置

        Returns:
            bool: 处理成功返回 True
        """
        try:
            # 解析事件数据
            event = PullRequestEventData.from_payload(payload)

            logger.log_event_processing(
                "pull_request",
                event.repo_name,
                True,
                {
                    "action": event.action,
                    "pr_number": event.pull_request.number,
                    "user": event.user
                }
            )

            # 格式化消息
            message = self.formatter.format_pull_request_event(event)

            # 发送到所有配置的目标
            return await self._send_to_targets(message, webhook_config)

        except Exception as e:
            logger.log_event_processing(
                "pull_request",
                payload.get("repository", {}).get("full_name", "未知"),
                False,
                error=str(e)
            )
            return False

    async def process_issue_event(
        self,
        payload: Dict[str, Any],
        webhook_config: WebhookConfig
    ) -> bool:
        """
        处理 Issue 事件。

        Args:
            payload: GitHub Webhook payload
            webhook_config: 匹配的 Webhook 配置

        Returns:
            bool: 处理成功返回 True
        """
        try:
            # 解析事件数据
            event = IssueEventData.from_payload(payload)

            logger.log_event_processing(
                "issues",
                event.repo_name,
                True,
                {
                    "action": event.action,
                    "issue_number": event.issue.number,
                    "user": event.user
                }
            )

            # 格式化消息
            message = self.formatter.format_issue_event(event)

            # 发送到所有配置的目标
            return await self._send_to_targets(message, webhook_config)

        except Exception as e:
            logger.log_event_processing(
                "issues",
                payload.get("repository", {}).get("full_name", "未知"),
                False,
                error=str(e)
            )
            return False

    async def process_release_event(
        self,
        payload: Dict[str, Any],
        webhook_config: WebhookConfig
    ) -> bool:
        """
        处理 Release 事件。

        Args:
            payload: GitHub Webhook payload
            webhook_config: 匹配的 Webhook 配置

        Returns:
            bool: 处理成功返回 True
        """
        try:
            # 解析事件数据
            event = ReleaseEventData.from_payload(payload)

            logger.log_event_processing(
                "release",
                event.repo_name,
                True,
                {
                    "action": event.action,
                    "tag": event.release.tag_name,
                    "user": event.user
                }
            )

            # 格式化消息
            message = self.formatter.format_release_event(event)

            # 发送到所有配置的目标
            return await self._send_to_targets(message, webhook_config)

        except Exception as e:
            logger.log_event_processing(
                "release",
                payload.get("repository", {}).get("full_name", "未知"),
                False,
                error=str(e)
            )
            return False

    async def process_issue_comment_event(
        self,
        payload: Dict[str, Any],
        webhook_config: WebhookConfig
    ) -> bool:
        """
        处理 Issue/PR 评论事件。

        Args:
            payload: GitHub Webhook payload
            webhook_config: 匹配的 Webhook 配置

        Returns:
            bool: 处理成功返回 True
        """
        try:
            # 解析事件数据
            event = IssueCommentEventData.from_payload(payload)

            logger.log_event_processing(
                "issue_comment",
                event.repo_name,
                True,
                {
                    "action": event.action,
                    "issue_number": event.issue_number,
                    "user": event.user,
                    "is_pr": event.is_pull_request
                }
            )

            # 格式化消息
            message = self.formatter.format_issue_comment_event(event)

            # 发送到所有配置的目标
            return await self._send_to_targets(message, webhook_config)

        except Exception as e:
            logger.log_event_processing(
                "issue_comment",
                payload.get("repository", {}).get("full_name", "未知"),
                False,
                error=str(e)
            )
            return False

    async def _send_to_targets(
        self,
        message: Any,
        webhook_config: WebhookConfig
    ) -> bool:
        """
        发送消息到所有配置的目标。

        Args:
            message: 要发送的消息
            webhook_config: Webhook 配置

        Returns:
            bool: 所有目标都发送成功返回 True
        """
        all_success = True

        # 兼容旧格式：从 webhook_config.ONEBOT 获取目标
        for target in webhook_config.ONEBOT:
            try:
                # 旧格式总是使用 "onebot" 客户端
                client = BotClientManager.get_client("onebot")
                if client is None:
                    logger.error("OneBot 客户端未初始化")
                    all_success = False
                    continue

                success = await client.send_message(
                    target.type,
                    target.id,
                    message
                )
                if not success:
                    all_success = False

            except BotClientError as e:
                logger.error(
                    "发送消息到 %s %d 失败: %s",
                    target.type,
                    target.id,
                    e
                )
                all_success = False

        return all_success
