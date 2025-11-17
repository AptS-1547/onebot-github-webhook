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
OneBot 客户端模块

本模块提供 OneBot V11 协议的客户端实现。

作者：AptS:1547
版本：0.2.0
日期：2025-04-18
本程序遵循 Apache License 2.0 许可证
"""

from typing import Union

from .onebot import OneBotWebSocketClient, OneBotHTTPClient
from app.botclient.factory import BotClientFactory
from app.models.config import BotBackendConfig


def create_onebot_client(config: BotBackendConfig) -> Union[OneBotWebSocketClient, OneBotHTTPClient]:
    """
    根据配置创建 OneBot 客户端。

    Args:
        config: Bot 后端配置

    Returns:
        OneBot 客户端实例（WebSocket 或 HTTP）
    """
    conn = config.connection
    protocol = conn.__dict__.get('protocol', 'http')
    url = conn.__dict__.get('url', '')
    access_token = conn.__dict__.get('access_token', '')

    if protocol == 'ws':
        return OneBotWebSocketClient(url, access_token)
    return OneBotHTTPClient(url, access_token)


# 注册到工厂
BotClientFactory.register('onebot', create_onebot_client)

__all__ = ["OneBotWebSocketClient", "OneBotHTTPClient", "create_onebot_client"]
