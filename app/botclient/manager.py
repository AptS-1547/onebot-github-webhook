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
Bot 客户端管理器

本模块提供 Bot 客户端的注册、获取和生命周期管理功能。

作者：AptS:1547
版本：0.2.0
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

import logging
from typing import Dict, Optional

from app.botclient.base import BotClientInterface
from app.exceptions import BotClientInitializationError

logger = logging.getLogger(__name__)


class BotClientManager:
    """
    Bot 客户端管理器。

    负责管理所有 Bot 客户端实例的生命周期，包括注册、获取和关闭。

    Attributes:
        _clients: 客户端注册表，键为客户端名称，值为客户端实例
    """

    _clients: Dict[str, BotClientInterface] = {}

    @classmethod
    async def register_client(
        cls,
        name: str,
        client: BotClientInterface,
        replace: bool = False
    ) -> None:
        """
        注册 Bot 客户端。

        Args:
            name: 客户端名称（如 "onebot"）
            client: 客户端实例，必须实现 BotClientInterface
            replace: 是否替换已存在的同名客户端，默认为 False

        Raises:
            BotClientInitializationError: 客户端已存在且 replace=False 时
            TypeError: client 不是 BotClientInterface 的实例时
        """
        if not isinstance(client, BotClientInterface):
            raise TypeError(
                f"客户端必须实现 BotClientInterface 接口，"
                f"但得到了 {type(client).__name__}"
            )

        if name in cls._clients and not replace:
            raise BotClientInitializationError(
                f"客户端 '{name}' 已存在，请使用 replace=True 替换",
                details={"client_name": name}
            )

        if name in cls._clients:
            logger.warning("替换已存在的客户端: %s", name)
            # 关闭旧客户端
            await cls._clients[name].close()

        cls._clients[name] = client
        logger.info(
            "客户端已注册: 名称=%s, 类型=%s",
            name,
            client.client_type
        )

    @classmethod
    def get_client(cls, name: str) -> Optional[BotClientInterface]:
        """
        获取指定名称的 Bot 客户端。

        Args:
            name: 客户端名称

        Returns:
            BotClientInterface: 客户端实例，如果不存在则返回 None
        """
        client = cls._clients.get(name)
        if client is None:
            logger.warning("客户端 '%s' 不存在", name)
        return client

    @classmethod
    def has_client(cls, name: str) -> bool:
        """
        检查指定名称的客户端是否已注册。

        Args:
            name: 客户端名称

        Returns:
            bool: 存在返回 True，否则返回 False
        """
        return name in cls._clients

    @classmethod
    def list_clients(cls) -> Dict[str, BotClientInterface]:
        """
        列出所有已注册的客户端。

        Returns:
            Dict[str, BotClientInterface]: 客户端名称到客户端实例的映射
        """
        return cls._clients.copy()

    @classmethod
    async def close_client(cls, name: str) -> bool:
        """
        关闭指定名称的客户端。

        Args:
            name: 客户端名称

        Returns:
            bool: 成功关闭返回 True，客户端不存在返回 False
        """
        client = cls._clients.pop(name, None)
        if client is None:
            logger.warning("无法关闭客户端 '%s'：客户端不存在", name)
            return False

        try:
            await client.close()
            logger.info("客户端已关闭: %s", name)
            return True
        except Exception as e:  # pylint: disable=broad-except
            logger.error("关闭客户端 '%s' 时发生错误: %s", name, e)
            return False

    @classmethod
    async def close_all(cls) -> None:
        """
        关闭所有已注册的客户端。

        此方法会逐个关闭所有客户端，即使某些客户端关闭失败也会继续。
        """
        logger.info("正在关闭所有客户端...")
        client_names = list(cls._clients.keys())

        for name in client_names:
            await cls.close_client(name)

        cls._clients.clear()
        logger.info("所有客户端已关闭")

    @classmethod
    def clear_registry(cls) -> None:
        """
        清空客户端注册表（不关闭客户端）。

        警告：此方法仅用于测试，会导致客户端泄漏。
        正常情况下应使用 close_all()。
        """
        logger.warning("清空客户端注册表（未关闭客户端，可能导致资源泄漏）")
        cls._clients.clear()
