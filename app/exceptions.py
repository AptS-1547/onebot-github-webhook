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
统一异常体系

本模块定义了项目中使用的所有自定义异常类，提供清晰的异常层次结构。

作者：AptS:1547
版本：0.2.0
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

from typing import Optional


class WebhookError(Exception):
    """
    Webhook 基础异常类。

    所有 Webhook 相关的异常都应继承此类。

    Attributes:
        message: 错误描述信息
        status_code: HTTP 状态码（用于 API 响应）
        details: 额外的错误详情
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[dict] = None
    ) -> None:
        """
        初始化 WebhookError。

        Args:
            message: 错误描述信息
            status_code: HTTP 状态码，默认为 500
            details: 额外的错误详情字典
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class SignatureVerificationError(WebhookError):
    """
    签名验证失败异常。

    当 GitHub Webhook 签名验证失败时抛出。
    """

    def __init__(
        self,
        message: str = "Webhook signature verification failed",
        details: Optional[dict] = None
    ) -> None:
        """
        初始化 SignatureVerificationError。

        Args:
            message: 错误描述，默认为 "Webhook signature verification failed"
            details: 额外的错误详情
        """
        super().__init__(message, status_code=401, details=details)


class ConfigurationError(WebhookError):
    """
    配置错误异常。

    当配置文件加载失败或配置项不合法时抛出。
    """

    def __init__(
        self,
        message: str,
        details: Optional[dict] = None
    ) -> None:
        """
        初始化 ConfigurationError。

        Args:
            message: 错误描述
            details: 额外的错误详情
        """
        super().__init__(message, status_code=500, details=details)


class BotClientError(WebhookError):
    """
    Bot 客户端错误异常。

    当与 Bot 客户端通信失败时抛出。
    """

    def __init__(
        self,
        message: str,
        details: Optional[dict] = None
    ) -> None:
        """
        初始化 BotClientError。

        Args:
            message: 错误描述
            details: 额外的错误详情
        """
        super().__init__(message, status_code=503, details=details)


class BotClientInitializationError(BotClientError):
    """
    Bot 客户端初始化失败异常。

    当 Bot 客户端初始化失败时抛出。
    """

    def __init__(
        self,
        message: str = "Bot client initialization failed",
        details: Optional[dict] = None
    ) -> None:
        """
        初始化 BotClientInitializationError。

        Args:
            message: 错误描述，默认为 "Bot client initialization failed"
            details: 额外的错误详情
        """
        super().__init__(message, details=details)


class BotClientConnectionError(BotClientError):
    """
    Bot 客户端连接错误异常。

    当 Bot 客户端连接失败或断开时抛出。
    """

    def __init__(
        self,
        message: str = "Bot client connection error",
        details: Optional[dict] = None
    ) -> None:
        """
        初始化 BotClientConnectionError。

        Args:
            message: 错误描述，默认为 "Bot client connection error"
            details: 额外的错误详情
        """
        super().__init__(message, details=details)


class BotClientTimeoutError(BotClientError):
    """
    Bot 客户端超时异常。

    当 Bot 客户端操作超时时抛出。
    """

    def __init__(
        self,
        message: str = "Bot client operation timeout",
        details: Optional[dict] = None
    ) -> None:
        """
        初始化 BotClientTimeoutError。

        Args:
            message: 错误描述，默认为 "Bot client operation timeout"
            details: 额外的错误详情
        """
        super().__init__(message, details=details)


class WebhookMatchError(WebhookError):
    """
    Webhook 匹配失败异常。

    当找不到匹配的 Webhook 配置时抛出。
    """

    def __init__(
        self,
        message: str = "No matching webhook configuration found",
        details: Optional[dict] = None
    ) -> None:
        """
        初始化 WebhookMatchError。

        Args:
            message: 错误描述，默认为 "No matching webhook configuration found"
            details: 额外的错误详情
        """
        super().__init__(message, status_code=404, details=details)


class InvalidPayloadError(WebhookError):
    """
    无效的 Payload 异常。

    当 GitHub Webhook payload 格式不正确或缺少必要字段时抛出。
    """

    def __init__(
        self,
        message: str = "Invalid webhook payload",
        details: Optional[dict] = None
    ) -> None:
        """
        初始化 InvalidPayloadError。

        Args:
            message: 错误描述，默认为 "Invalid webhook payload"
            details: 额外的错误详情
        """
        super().__init__(message, status_code=400, details=details)
