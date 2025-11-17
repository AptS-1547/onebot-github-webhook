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
Bot 客户端抽象接口

本模块定义了 Bot 客户端的抽象基类和通用接口。

作者：AptS:1547
版本：0.2.0
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

from abc import ABC, abstractmethod
from typing import Union, List, Dict, Any


class BotClientInterface(ABC):
    """
    Bot 客户端抽象接口。

    所有 Bot 客户端实现必须继承此类并实现其抽象方法。

    支持的消息类型：
        - 纯文本字符串
        - OneBot 消息段列表（List[Dict[str, Any]]）
    """

    @abstractmethod
    async def send_message(
        self,
        target_type: str,
        target_id: int,
        message: Union[str, List[Dict[str, Any]]],
        **kwargs: Any
    ) -> bool:
        """
        发送消息到指定目标。

        Args:
            target_type: 目标类型（如 "group" 表示群组，"private" 表示私聊）
            target_id: 目标 ID（群号或用户 QQ 号）
            message: 消息内容，可以是纯文本字符串或消息段列表
            **kwargs: 额外的参数（如 auto_escape 等）

        Returns:
            bool: 发送成功返回 True，失败返回 False

        Raises:
            BotClientError: 发送消息时发生错误
            BotClientTimeoutError: 发送消息超时
            BotClientConnectionError: 客户端未连接或连接断开
        """

    @abstractmethod
    async def close(self) -> None:
        """
        关闭客户端连接并释放资源。

        此方法应该确保优雅地关闭所有连接和清理资源。
        """

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """
        检查客户端是否已连接。

        Returns:
            bool: 已连接返回 True，未连接返回 False
        """

    @property
    @abstractmethod
    def client_type(self) -> str:
        """
        获取客户端类型。

        Returns:
            str: 客户端类型标识（如 "onebot", "telegram" 等）
        """
