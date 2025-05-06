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
Onebot Github Webhook 消息模型
本文件用于定义 Onebot Github Webhook 的消息模型。
作者：AptS:1547
版本：0.1.0-alpha
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

from typing import Dict, Any

class MessageSegment:
    """
    消息段类
    用于定义消息段的类型和数据
    """

    # 消息段工具函数
    @staticmethod
    def text(content: str) -> Dict[str, Any]:
        """纯文本消息"""
        return {"type": "text", "data": {"text": content}}
