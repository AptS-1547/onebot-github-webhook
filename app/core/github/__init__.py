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
GitHub 处理模块
本模块用于处理 GitHub Webhook 事件以及轮训 GitHub 仓库的相关操作。
作者：AptS:1547
版本：0.1.0-alpha
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

from .webhook import GitHubWebhookHandler
from .polling import GitHubPollingHandler

__all__ = [
    "GitHubWebhookHandler",
    "GitHubPollingHandler",
]
