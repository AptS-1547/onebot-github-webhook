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
OneBot GitHub Webhook Matching 模块
本模块用于处理 GitHub Webhook 事件的匹配逻辑，包括验证签名、查找匹配的 webhook 配置和提取 push 事件数据。
作者：AptS:1547
版本：0.1.0-alpha
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

import logging
import fnmatch

logger = logging.getLogger(__name__)

def match_pattern(value: str, pattern: str) -> bool:
    """
    检查字符串是否匹配配置中的模式
    支持大小写不敏感匹配和通配符模式

    Args:
        value: 要匹配的字符串 (例如 'user/repo' 或 'main')
        pattern: 配置中的模式 (例如 'user/*', 'feature/*')
        treat_star_as_all: 是否将单独的 "*" 视为匹配所有内容（用于分支匹配）

    Returns:
        bool: 是否匹配
    """
    if not value or not pattern:
        return False

    value = value.lower()
    pattern = pattern.lower()

    # 分支匹配特殊情况：单独的 "*" 匹配所有内容
    if pattern == "*":
        return True

    if '*' in pattern or '?' in pattern or '[' in pattern:
        return fnmatch.fnmatch(value, pattern)

    return value == pattern
