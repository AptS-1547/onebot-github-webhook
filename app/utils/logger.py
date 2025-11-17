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
结构化日志系统

本模块提供结构化日志记录工具，统一日志格式和级别使用规范。

作者：AptS:1547
版本：0.2.0
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

import logging
from typing import Any, Dict, Optional


class StructuredLogger:
    """
    结构化日志记录器。

    提供结构化的日志记录方法，包含完整的上下文信息。

    Attributes:
        logger: Python 标准库 logging.Logger 实例
    """

    def __init__(self, name: str) -> None:
        """
        初始化结构化日志记录器。

        Args:
            name: 日志记录器名称，通常使用模块的 __name__
        """
        self.logger = logging.getLogger(name)

    def log_webhook_received(
        self,
        event_type: str,
        repo_name: str,
        client_ip: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        记录收到 webhook 事件。

        Args:
            event_type: GitHub 事件类型（如 "push", "pull_request"）
            repo_name: 仓库全名（如 "user/repo"）
            client_ip: 客户端 IP 地址
            extra: 额外的上下文信息
        """
        self.logger.info(
            "收到 GitHub Webhook 事件: 类型=%s, 仓库=%s, 来源IP=%s",
            event_type,
            repo_name,
            client_ip or "未知"
        )
        if extra:
            self.logger.debug("额外信息: %s", extra)

    def log_webhook_matched(
        self,
        webhook_name: str,
        repo_name: str,
        branch: Optional[str] = None,
        event_type: Optional[str] = None
    ) -> None:
        """
        记录 webhook 配置匹配成功。

        Args:
            webhook_name: 匹配的 webhook 配置名称
            repo_name: 仓库全名
            branch: 分支名（可选）
            event_type: 事件类型（可选）
        """
        self.logger.info(
            "匹配到 Webhook 配置: 名称=%s, 仓库=%s, 分支=%s, 事件=%s",
            webhook_name,
            repo_name,
            branch or "N/A",
            event_type or "N/A"
        )

    def log_webhook_not_matched(
        self,
        repo_name: str,
        branch: Optional[str] = None,
        event_type: Optional[str] = None
    ) -> None:
        """
        记录 webhook 配置匹配失败。

        Args:
            repo_name: 仓库全名
            branch: 分支名（可选）
            event_type: 事件类型（可选）
        """
        self.logger.warning(
            "未找到匹配的 Webhook 配置: 仓库=%s, 分支=%s, 事件=%s",
            repo_name,
            branch or "N/A",
            event_type or "N/A"
        )

    def log_signature_verification(
        self,
        success: bool,
        repo_name: Optional[str] = None,
        error: Optional[str] = None
    ) -> None:
        """
        记录签名验证结果。

        Args:
            success: 验证是否成功
            repo_name: 仓库全名
            error: 错误信息（验证失败时）
        """
        if success:
            self.logger.info("Webhook 签名验证成功: 仓库=%s", repo_name or "未知")
        else:
            self.logger.error(
                "Webhook 签名验证失败: 仓库=%s, 错误=%s",
                repo_name or "未知",
                error or "未知错误"
            )

    def log_bot_message_sent(  # pylint: disable=too-many-arguments
        self,
        bot_type: str,
        target_type: str,
        target_id: int,
        success: bool,
        message_preview: Optional[str] = None,
        error: Optional[str] = None
    ) -> None:
        """
        记录发送 Bot 消息结果。

        Args:
            bot_type: Bot 类型（如 "onebot"）
            target_type: 目标类型（如 "group", "private"）
            target_id: 目标 ID（群号或用户 ID）
            success: 是否发送成功
            message_preview: 消息内容预览（前50字符）
            error: 错误信息（发送失败时）
        """
        level = logging.INFO if success else logging.ERROR
        status = "成功" if success else "失败"

        if success:
            self.logger.log(
                level,
                "Bot 消息发送%s: 类型=%s, 目标=%s:%d, 预览=%s",
                status,
                bot_type,
                target_type,
                target_id,
                message_preview[:50] if message_preview else "N/A"
            )
        else:
            self.logger.log(
                level,
                "Bot 消息发送%s: 类型=%s, 目标=%s:%d, 错误=%s",
                status,
                bot_type,
                target_type,
                target_id,
                error or "未知错误"
            )

    def log_bot_client_connection(
        self,
        bot_type: str,
        url: str,
        success: bool,
        error: Optional[str] = None
    ) -> None:
        """
        记录 Bot 客户端连接状态。

        Args:
            bot_type: Bot 类型
            url: 连接 URL
            success: 是否连接成功
            error: 错误信息（连接失败时）
        """
        level = logging.INFO if success else logging.ERROR
        status = "成功" if success else "失败"

        if success:
            self.logger.log(
                level,
                "Bot 客户端连接%s: 类型=%s, URL=%s",
                status,
                bot_type,
                url
            )
        else:
            self.logger.log(
                level,
                "Bot 客户端连接%s: 类型=%s, URL=%s, 错误=%s",
                status,
                bot_type,
                url,
                error or "未知错误"
            )

    def log_bot_client_reconnect(
        self,
        bot_type: str,
        attempt: int,
        delay: float,
        url: Optional[str] = None
    ) -> None:
        """
        记录 Bot 客户端重连尝试。

        Args:
            bot_type: Bot 类型
            attempt: 重连尝试次数
            delay: 重连延迟（秒）
            url: 连接 URL
        """
        self.logger.warning(
            "Bot 客户端准备重连: 类型=%s, 尝试次数=%d, 延迟=%.1f秒, URL=%s",
            bot_type,
            attempt,
            delay,
            url or "N/A"
        )

    def log_event_processing(  # pylint: disable=too-many-arguments
        self,
        event_type: str,
        repo_name: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """
        记录事件处理结果。

        Args:
            event_type: 事件类型
            repo_name: 仓库全名
            success: 是否处理成功
            details: 事件详情（如分支名、PR号等）
            error: 错误信息（处理失败时）
        """
        level = logging.INFO if success else logging.ERROR
        status = "成功" if success else "失败"

        detail_str = ", ".join(f"{k}={v}" for k, v in (details or {}).items())

        if success:
            self.logger.log(
                level,
                "事件处理%s: 类型=%s, 仓库=%s, 详情={%s}",
                status,
                event_type,
                repo_name,
                detail_str
            )
        else:
            self.logger.log(
                level,
                "事件处理%s: 类型=%s, 仓库=%s, 错误=%s",
                status,
                event_type,
                repo_name,
                error or "未知错误"
            )

    def log_config_loaded(
        self,
        config_file: str,
        webhooks_count: int
    ) -> None:
        """
        记录配置文件加载结果。

        Args:
            config_file: 配置文件路径
            webhooks_count: 加载的 webhook 配置数量
        """
        self.logger.info(
            "配置文件加载成功: 文件=%s, Webhook配置数=%d",
            config_file,
            webhooks_count
        )

    def log_config_error(
        self,
        config_file: str,
        error: str
    ) -> None:
        """
        记录配置文件加载错误。

        Args:
            config_file: 配置文件路径
            error: 错误信息
        """
        self.logger.error(
            "配置文件加载失败: 文件=%s, 错误=%s",
            config_file,
            error
        )

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        记录调试级别日志。

        Args:
            message: 日志消息
            *args: 格式化参数
            **kwargs: 额外参数
        """
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        记录信息级别日志。

        Args:
            message: 日志消息
            *args: 格式化参数
            **kwargs: 额外参数
        """
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        记录警告级别日志。

        Args:
            message: 日志消息
            *args: 格式化参数
            **kwargs: 额外参数
        """
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        记录错误级别日志。

        Args:
            message: 日志消息
            *args: 格式化参数
            **kwargs: 额外参数
        """
        self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        记录严重错误级别日志。

        Args:
            message: 日志消息
            *args: 格式化参数
            **kwargs: 额外参数
        """
        self.logger.critical(message, *args, **kwargs)
