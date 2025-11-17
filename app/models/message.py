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
OneBot 消息模型

本模块定义了 OneBot 消息段的数据结构。

作者：AptS:1547
版本：0.2.0
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

from typing import Dict, Any, List


class MessageSegment:
    """
    OneBot 消息段类。

    提供静态方法用于构建各类消息段。
    """

    @staticmethod
    def text(content: str) -> Dict[str, Any]:
        """
        创建纯文本消息段。

        Args:
            content: 文本内容

        Returns:
            Dict[str, Any]: 消息段字典
        """
        return {"type": "text", "data": {"text": content}}

    @staticmethod
    def image(file: str, url: str = "") -> Dict[str, Any]:
        """
        创建图片消息段。

        Args:
            file: 图片文件路径或 URL
            url: 图片 URL（可选）

        Returns:
            Dict[str, Any]: 消息段字典
        """
        data = {"file": file}
        if url:
            data["url"] = url
        return {"type": "image", "data": data}

    @staticmethod
    def at(user_id: int) -> Dict[str, Any]:
        """
        创建 @ 消息段。

        Args:
            user_id: 用户 QQ 号

        Returns:
            Dict[str, Any]: 消息段字典
        """
        return {"type": "at", "data": {"qq": str(user_id)}}

    @staticmethod
    def at_all() -> Dict[str, Any]:
        """
        创建 @全体成员 消息段。

        Returns:
            Dict[str, Any]: 消息段字典
        """
        return {"type": "at", "data": {"qq": "all"}}


class MessageBuilder:
    """
    消息构建器。

    用于方便地构建由多个消息段组成的消息。

    Attributes:
        segments: 消息段列表
    """

    def __init__(self) -> None:
        """初始化消息构建器。"""
        self.segments: List[Dict[str, Any]] = []

    def text(self, content: str) -> "MessageBuilder":
        """
        添加文本消息段。

        Args:
            content: 文本内容

        Returns:
            MessageBuilder: 返回自身以支持链式调用
        """
        self.segments.append(MessageSegment.text(content))
        return self

    def image(self, file: str, url: str = "") -> "MessageBuilder":
        """
        添加图片消息段。

        Args:
            file: 图片文件路径或 URL
            url: 图片 URL（可选）

        Returns:
            MessageBuilder: 返回自身以支持链式调用
        """
        self.segments.append(MessageSegment.image(file, url))
        return self

    def at(self, user_id: int) -> "MessageBuilder":
        """
        添加 @ 消息段。

        Args:
            user_id: 用户 QQ 号

        Returns:
            MessageBuilder: 返回自身以支持链式调用
        """
        self.segments.append(MessageSegment.at(user_id))
        return self

    def at_all(self) -> "MessageBuilder":
        """
        添加 @全体成员 消息段。

        Returns:
            MessageBuilder: 返回自身以支持链式调用
        """
        self.segments.append(MessageSegment.at_all())
        return self

    def build(self) -> List[Dict[str, Any]]:
        """
        构建消息。

        Returns:
            List[Dict[str, Any]]: 消息段列表
        """
        return self.segments

    def clear(self) -> "MessageBuilder":
        """
        清空消息段。

        Returns:
            MessageBuilder: 返回自身以支持链式调用
        """
        self.segments.clear()
        return self
