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
Bot 客户端模块

本模块提供各类 Bot 客户端的实现和管理。

作者：AptS:1547
版本：0.2.0
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

from app.botclient.base import BotClientInterface, BotTarget
from app.botclient.manager import BotClientManager
from app.botclient.factory import BotClientFactory

__all__ = ["BotClientInterface", "BotTarget", "BotClientManager", "BotClientFactory"]
