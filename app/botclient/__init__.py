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
OneBot GitHub Webhook botclient 模块
本模块用于各类 Bot 客户端的实现，包括 Onebot、Rocket.Chat、Telegram 等。
本模块的设计目标是提供一个统一的接口，以便于在不同的 Bot 客户端之间进行切换和扩展。
作者：AptS:1547
版本：0.1.0-alpha
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

import logging
from typing import Dict, Optional, Any

from .onebot import (
    init_onebot_client,
    shutdown_onebot_client
)

_logger = logging.getLogger(__name__)

class BotClient:
    """统一的 Bot 客户端接口"""

    _clients_registry: Dict[str, Any] = {}

    @classmethod
    async def init_client(cls, client_type: str, *args, **kwargs):
        """
        初始化 Bot 客户端
        根据 client_type 的不同，初始化不同的 Bot 客户端
        """

        _logger.info("Initializing client of type: %s", client_type)

        if client_type == "onebot":
            client = await init_onebot_client(*args, **kwargs)
        elif client_type == "rocketchat":
            raise NotImplementedError("Rocket.Chat client is not implemented yet.")
        elif client_type == "telegram":
            raise NotImplementedError("Telegram client is not implemented yet.")
        else:
            raise ValueError(f"Unsupported client type: {client_type}")

        cls._clients_registry[client_type] = client
        return client

    @classmethod
    def get_client(cls, client_type: str) -> Optional[Any]:
        """
        获取指定类型的客户端实例
        
        Args:
            client_type: 客户端类型
            
        Returns:
            客户端实例，如果不存在则返回None
        """
        return cls._clients_registry.get(client_type)

    @classmethod
    def shutdown_client(cls, *args, **kwargs):
        """
        关闭 Bot 客户端
        关闭全部的 Bot 客户端
        """
        return shutdown_onebot_client(*args, **kwargs)

__all__ = [
    "BotClient",
]
