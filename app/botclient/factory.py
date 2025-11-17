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
Bot 客户端工厂

提供客户端创建和注册机制。

作者：AptS:1547
版本：0.2.0-alpha
日期：2025-04-18
本程序遵循 Apache License 2.0 许可证
"""

import logging
from typing import Dict, Type, Callable, Any

from app.botclient.base import BotClientInterface
from app.models.config import BotBackendConfig

logger = logging.getLogger(__name__)


class BotClientFactory:
    """
    Bot 客户端工厂类。

    提供插件化的客户端注册和创建机制。
    """

    _registry: Dict[str, Callable[[BotBackendConfig], BotClientInterface]] = {}

    @classmethod
    def register(
        cls,
        platform: str,
        creator: Callable[[BotBackendConfig], BotClientInterface]
    ) -> None:
        """
        注册客户端创建函数。

        Args:
            platform: 平台类型（如 "onebot", "telegram"）
            creator: 客户端创建函数，接受 BotBackendConfig 返回客户端实例
        """
        if platform in cls._registry:
            logger.warning("平台 '%s' 已注册，将被覆盖", platform)

        cls._registry[platform] = creator
        logger.info("客户端创建器已注册: 平台=%s", platform)

    @classmethod
    def create(cls, config: BotBackendConfig) -> BotClientInterface:
        """
        根据配置创建客户端实例。

        Args:
            config: Bot 后端配置

        Returns:
            BotClientInterface: 客户端实例

        Raises:
            ValueError: 不支持的平台类型
        """
        platform = config.platform

        if platform not in cls._registry:
            raise ValueError(
                f"不支持的平台类型: {platform}。"
                f"已注册平台: {list(cls._registry.keys())}"
            )

        creator = cls._registry[platform]
        logger.debug("正在创建客户端: 平台=%s, 名称=%s", platform, config.name)

        try:
            client = creator(config)
            logger.info("客户端创建成功: 平台=%s, 名称=%s", platform, config.name)
            return client
        except Exception as e:
            logger.error("客户端创建失败: 平台=%s, 错误=%s", platform, e)
            raise

    @classmethod
    def list_supported_platforms(cls) -> list[str]:
        """
        列出所有已注册的平台。

        Returns:
            list[str]: 平台类型列表
        """
        return list(cls._registry.keys())

    @classmethod
    def is_platform_supported(cls, platform: str) -> bool:
        """
        检查平台是否已注册。

        Args:
            platform: 平台类型

        Returns:
            bool: 已注册返回 True，否则返回 False
        """
        return platform in cls._registry
