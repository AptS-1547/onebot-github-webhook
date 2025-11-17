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
依赖注入系统

本模块提供 FastAPI 依赖注入的依赖项。

作者：AptS:1547
版本：0.2.0
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

from typing import Annotated

from fastapi import Depends, HTTPException

from app.models.config import Config, get_settings
from app.botclient.base import BotClientInterface
from app.botclient.manager import BotClientManager
from app.services.webhook_service import WebhookService


def get_config() -> Config:
    """
    获取应用配置。

    Returns:
        Config: 应用配置实例
    """
    return get_settings()


def get_bot_client() -> BotClientInterface:
    """
    获取 Bot 客户端实例。

    Returns:
        BotClientInterface: Bot 客户端实例

    Raises:
        HTTPException: Bot 客户端未初始化
    """
    client = BotClientManager.get_client("onebot")
    if client is None:
        raise HTTPException(
            status_code=503,
            detail="Bot 客户端未初始化"
        )
    return client


def get_webhook_service(
    config: Annotated[Config, Depends(get_config)]
) -> WebhookService:
    """
    获取 Webhook 服务实例。

    Args:
        config: 应用配置实例（通过依赖注入）

    Returns:
        WebhookService: Webhook 服务实例
    """
    return WebhookService(config)


# 类型别名，方便在其他模块中使用
ConfigDep = Annotated[Config, Depends(get_config)]
BotClientDep = Annotated[BotClientInterface, Depends(get_bot_client)]
WebhookServiceDep = Annotated[WebhookService, Depends(get_webhook_service)]
