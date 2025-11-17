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
通用消息模型

提供平台无关的消息抽象，支持多种 Bot 平台。

作者：AptS:1547
版本：0.2.0-alpha
日期：2025-04-18
本程序遵循 Apache License 2.0 许可证
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class MessageSegmentType(str, Enum):
    """消息段类型枚举"""
    TEXT = "text"           # 纯文本
    LINK = "link"           # 链接
    CODE = "code"           # 代码块
    BOLD = "bold"           # 粗体文本
    ITALIC = "italic"       # 斜体文本
    NEWLINE = "newline"     # 换行


class UniversalMessageSegment(BaseModel):
    """
    通用消息段。

    平台无关的消息片段表示。

    Attributes:
        type: 消息段类型
        content: 消息内容
        metadata: 额外的元数据（平台特定属性）
    """
    type: MessageSegmentType
    content: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def text(cls, content: str) -> 'UniversalMessageSegment':
        """创建文本消息段"""
        return cls(type=MessageSegmentType.TEXT, content=content)

    @classmethod
    def link(cls, text: str, url: str) -> 'UniversalMessageSegment':
        """创建链接消息段"""
        return cls(
            type=MessageSegmentType.LINK,
            content=text,
            metadata={"url": url}
        )

    @classmethod
    def code(cls, code: str, language: str = "") -> 'UniversalMessageSegment':
        """创建代码块消息段"""
        return cls(
            type=MessageSegmentType.CODE,
            content=code,
            metadata={"language": language}
        )

    @classmethod
    def bold(cls, text: str) -> 'UniversalMessageSegment':
        """创建粗体文本消息段"""
        return cls(type=MessageSegmentType.BOLD, content=text)

    @classmethod
    def italic(cls, text: str) -> 'UniversalMessageSegment':
        """创建斜体文本消息段"""
        return cls(type=MessageSegmentType.ITALIC, content=text)

    @classmethod
    def newline(cls) -> 'UniversalMessageSegment':
        """创建换行消息段"""
        return cls(type=MessageSegmentType.NEWLINE, content="\n")


class UniversalMessage(BaseModel):
    """
    通用消息。

    平台无关的消息表示，包含多个消息段。

    Attributes:
        segments: 消息段列表
    """
    segments: List[UniversalMessageSegment] = Field(default_factory=list)

    def add_segment(self, segment: UniversalMessageSegment) -> 'UniversalMessage':
        """
        添加消息段。

        Args:
            segment: 消息段

        Returns:
            UniversalMessage: 当前消息对象（支持链式调用）
        """
        self.segments.append(segment)
        return self

    def add_text(self, text: str) -> 'UniversalMessage':
        """添加文本消息段（便捷方法）"""
        return self.add_segment(UniversalMessageSegment.text(text))

    def add_link(self, text: str, url: str) -> 'UniversalMessage':
        """添加链接消息段（便捷方法）"""
        return self.add_segment(UniversalMessageSegment.link(text, url))

    def add_code(self, code: str, language: str = "") -> 'UniversalMessage':
        """添加代码块消息段（便捷方法）"""
        return self.add_segment(UniversalMessageSegment.code(code, language))

    def add_bold(self, text: str) -> 'UniversalMessage':
        """添加粗体文本消息段（便捷方法）"""
        return self.add_segment(UniversalMessageSegment.bold(text))

    def add_newline(self) -> 'UniversalMessage':
        """添加换行（便捷方法）"""
        return self.add_segment(UniversalMessageSegment.newline())

    def to_onebot(self) -> List[Dict[str, Any]]:
        """
        转换为 OneBot 消息格式。

        Returns:
            List[Dict[str, Any]]: OneBot 消息段列表
        """
        onebot_segments = []

        for segment in self.segments:
            if segment.type == MessageSegmentType.TEXT:
                onebot_segments.append({
                    "type": "text",
                    "data": {"text": segment.content}
                })
            elif segment.type == MessageSegmentType.LINK:
                # OneBot 不直接支持链接，转为文本
                url = segment.metadata.get("url", "")
                onebot_segments.append({
                    "type": "text",
                    "data": {"text": f"{segment.content} ({url})"}
                })
            elif segment.type == MessageSegmentType.CODE:
                # OneBot 不直接支持代码块，转为文本
                onebot_segments.append({
                    "type": "text",
                    "data": {"text": f"```\n{segment.content}\n```"}
                })
            elif segment.type == MessageSegmentType.BOLD:
                # OneBot 不支持粗体，直接使用文本
                onebot_segments.append({
                    "type": "text",
                    "data": {"text": segment.content}
                })
            elif segment.type == MessageSegmentType.ITALIC:
                # OneBot 不支持斜体，直接使用文本
                onebot_segments.append({
                    "type": "text",
                    "data": {"text": segment.content}
                })
            elif segment.type == MessageSegmentType.NEWLINE:
                onebot_segments.append({
                    "type": "text",
                    "data": {"text": "\n"}
                })

        return onebot_segments

    def to_telegram_markdown(self) -> str:
        """
        转换为 Telegram Markdown 格式。

        Returns:
            str: Telegram Markdown 文本
        """
        parts = []

        for segment in self.segments:
            if segment.type == MessageSegmentType.TEXT:
                # 转义 Telegram Markdown 特殊字符
                text = segment.content.replace("_", "\\_").replace("*", "\\*")
                parts.append(text)
            elif segment.type == MessageSegmentType.LINK:
                url = segment.metadata.get("url", "")
                parts.append(f"[{segment.content}]({url})")
            elif segment.type == MessageSegmentType.CODE:
                language = segment.metadata.get("language", "")
                if language:
                    parts.append(f"```{language}\n{segment.content}\n```")
                else:
                    parts.append(f"`{segment.content}`")
            elif segment.type == MessageSegmentType.BOLD:
                parts.append(f"*{segment.content}*")
            elif segment.type == MessageSegmentType.ITALIC:
                parts.append(f"_{segment.content}_")
            elif segment.type == MessageSegmentType.NEWLINE:
                parts.append("\n")

        return "".join(parts)

    def to_wecom_markdown(self) -> str:
        """
        转换为企业微信 Markdown 格式。

        Returns:
            str: 企业微信 Markdown 文本
        """
        parts = []

        for segment in self.segments:
            if segment.type == MessageSegmentType.TEXT:
                parts.append(segment.content)
            elif segment.type == MessageSegmentType.LINK:
                url = segment.metadata.get("url", "")
                parts.append(f"[{segment.content}]({url})")
            elif segment.type == MessageSegmentType.CODE:
                # 企业微信支持代码块
                parts.append(f"`{segment.content}`")
            elif segment.type == MessageSegmentType.BOLD:
                parts.append(f"**{segment.content}**")
            elif segment.type == MessageSegmentType.ITALIC:
                # 企业微信不支持斜体，直接使用文本
                parts.append(segment.content)
            elif segment.type == MessageSegmentType.NEWLINE:
                parts.append("\n")

        return "".join(parts)

    def to_plain_text(self) -> str:
        """
        转换为纯文本格式（降级方案）。

        Returns:
            str: 纯文本
        """
        parts = []

        for segment in self.segments:
            if segment.type == MessageSegmentType.TEXT:
                parts.append(segment.content)
            elif segment.type == MessageSegmentType.LINK:
                url = segment.metadata.get("url", "")
                parts.append(f"{segment.content} ({url})")
            elif segment.type == MessageSegmentType.CODE:
                parts.append(segment.content)
            elif segment.type in (MessageSegmentType.BOLD, MessageSegmentType.ITALIC):
                parts.append(segment.content)
            elif segment.type == MessageSegmentType.NEWLINE:
                parts.append("\n")

        return "".join(parts)


class MessageBuilder:
    """
    消息构建器。

    提供流式 API 构建消息。

    Example:
        >>> msg = MessageBuilder() \\
        ...     .text("Hello ") \\
        ...     .bold("World") \\
        ...     .newline() \\
        ...     .link("GitHub", "https://github.com") \\
        ...     .build()
    """

    def __init__(self):
        """初始化消息构建器"""
        self._message = UniversalMessage()

    def text(self, content: str) -> 'MessageBuilder':
        """添加文本"""
        self._message.add_text(content)
        return self

    def link(self, text: str, url: str) -> 'MessageBuilder':
        """添加链接"""
        self._message.add_link(text, url)
        return self

    def code(self, code: str, language: str = "") -> 'MessageBuilder':
        """添加代码块"""
        self._message.add_code(code, language)
        return self

    def bold(self, text: str) -> 'MessageBuilder':
        """添加粗体文本"""
        self._message.add_bold(text)
        return self

    def italic(self, text: str) -> 'MessageBuilder':
        """添加斜体文本"""
        self._message.add_segment(UniversalMessageSegment.italic(text))
        return self

    def newline(self) -> 'MessageBuilder':
        """添加换行"""
        self._message.add_newline()
        return self

    def build(self) -> UniversalMessage:
        """构建消息"""
        return self._message
