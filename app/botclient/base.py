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
日期：2025-04-18
本程序遵循 Apache License 2.0 许可证
"""

from abc import ABC, abstractmethod
from typing import Union, List, Dict, Any, Set
from pydantic import BaseModel

from app.models.universal_message import UniversalMessage


class BotTarget(BaseModel):
    """
    通用的消息目标抽象。

    Attributes:
        platform: 平台类型（如 "onebot", "telegram", "wecom"）
        target_type: 目标类型（平台特定，如 "group", "private", "channel"）
        target_id: 目标 ID（字符串格式，兼容所有平台）
    """
    platform: str
    target_type: str
    target_id: str

    @classmethod
    def from_config(
        cls,
        bot_name: str,
        target_type: str,
        target_id: str,
        platform: str = "onebot"
    ) -> 'BotTarget':
        """
        从配置创建 BotTarget。

        Args:
            bot_name: Bot 实例名称
            target_type: 目标类型
            target_id: 目标 ID
            platform: 平台类型

        Returns:
            BotTarget: 目标实例
        """
        return cls(
            platform=platform,
            target_type=target_type,
            target_id=target_id
        )


class BotClientInterface(ABC):
    """
    Bot 客户端抽象接口。

    所有 Bot 客户端实现必须继承此类并实现其抽象方法。

    支持的消息类型：
        - UniversalMessage: 通用消息格式（推荐）
        - 纯文本字符串（向后兼容）
        - 平台特定格式（向后兼容）
    """

    @abstractmethod
    async def send_message(
        self,
        target_type: str,
        target_id: Union[int, str],
        message: Union[str, List[Dict[str, Any]], UniversalMessage],
        **kwargs: Any
    ) -> bool:
        """
        发送消息到指定目标。

        Args:
            target_type: 目标类型（如 "group", "private", "channel"）
            target_id: 目标 ID（可以是整数或字符串）
            message: 消息内容
                - UniversalMessage: 通用消息（会自动转换为平台格式）
                - str: 纯文本字符串
                - List[Dict]: 平台特定格式（OneBot 消息段列表）
            **kwargs: 额外的参数（如 auto_escape 等）

        Returns:
            bool: 发送成功返回 True，失败返回 False

        Raises:
            BotClientError: 发送消息时发生错误
            BotClientTimeoutError: 发送消息超时
            BotClientConnectionError: 客户端未连接或连接断开
        """

    async def send_universal_message(
        self,
        target: BotTarget,
        message: UniversalMessage,
        **kwargs: Any
    ) -> bool:
        """
        发送通用消息（推荐接口）。

        Args:
            target: 消息目标
            message: 通用消息
            **kwargs: 额外参数

        Returns:
            bool: 发送成功返回 True，失败返回 False
        """
        # 将 target_id 转换为合适的类型
        target_id: Union[int, str]
        try:
            target_id = int(target.target_id)
        except ValueError:
            target_id = target.target_id

        return await self.send_message(
            target_type=target.target_type,
            target_id=target_id,
            message=message,
            **kwargs
        )

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

    @property
    def supported_features(self) -> Set[str]:
        """
        获取客户端支持的特性集合。

        Returns:
            Set[str]: 支持的特性集合
                - "text": 纯文本
                - "markdown": Markdown 格式
                - "html": HTML 格式
                - "image": 图片
                - "file": 文件
                - "link": 链接
                - "code": 代码块
                - "bold": 粗体
                - "italic": 斜体
        """
        # 默认只支持纯文本
        return {"text"}
