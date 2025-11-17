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
OneBot GitHub Webhook 入口文件

本文件用于启动应用并配置全局资源。

作者：AptS:1547
版本：0.2.0
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import api_router
from app.models.config import get_settings
from app.botclient.onebot.onebot import OneBotWebSocketClient, OneBotHTTPClient
from app.botclient.manager import BotClientManager
from app.exceptions import (
    WebhookError,
    BotClientInitializationError,
    BotClientConnectionError,
    BotClientTimeoutError
)
from app.utils.logger import StructuredLogger

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = StructuredLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    管理应用程序生命周期的上下文管理器。

    在应用启动时初始化资源，在应用关闭时释放资源。
    """
    config = get_settings()

    logger.log_config_loaded("config.yaml", len(config.GITHUB_WEBHOOK))

    # 初始化 Bot 客户端
    try:
        if config.ONEBOT_PROTOCOL_TYPE == "ws":
            client = OneBotWebSocketClient(
                config.ONEBOT_URL,
                config.ONEBOT_ACCESS_TOKEN
            )
            await client.start(max_retries=5, retry_delay=2.0)
        else:
            client = OneBotHTTPClient(
                config.ONEBOT_URL,
                config.ONEBOT_ACCESS_TOKEN
            )

        # 注册客户端到管理器
        await BotClientManager.register_client("onebot", client)

        logger.info("OneBot 客户端初始化成功")

    except BotClientConnectionError as e:
        logger.error("OneBot 客户端连接失败: %s", e)
        raise BotClientInitializationError(
            f"OneBot 客户端连接失败: {e}",
            details={"url": config.ONEBOT_URL}
        ) from e

    except BotClientTimeoutError as e:
        logger.error("OneBot 客户端初始化超时: %s", e)
        raise BotClientInitializationError(
            f"OneBot 客户端初始化超时: {e}",
            details={"url": config.ONEBOT_URL}
        ) from e

    except Exception as e:
        logger.error("初始化 OneBot 客户端时发生未知错误: %s", e)
        raise BotClientInitializationError(
            f"初始化失败: {e}",
            details={"url": config.ONEBOT_URL}
        ) from e

    yield

    # 关闭所有客户端
    logger.info("正在关闭应用...")
    await BotClientManager.close_all()
    logger.info("应用已关闭")


app = FastAPI(
    title="OneBot GitHub Webhook",
    description="GitHub Webhook 推送消息到 QQ 群",
    version="0.2.0",
    lifespan=lifespan
)


# 全局异常处理器
@app.exception_handler(WebhookError)
async def webhook_error_handler(request: Request, exc: WebhookError):
    """
    处理 WebhookError 异常。

    Args:
        request: FastAPI Request 对象
        exc: WebhookError 异常实例

    Returns:
        JSONResponse: 错误响应
    """
    logger.error(
        "Webhook 错误: %s | 路径: %s | 客户端: %s | 详情: %s",
        exc.message,
        request.url.path,
        request.client.host if request.client else "未知",
        exc.details
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details
        }
    )


# 包含 API 路由
app.include_router(api_router)


# 健康检查端点
@app.get("/health")
async def health_check():
    """
    健康检查端点。

    Returns:
        dict: 健康状态
    """
    onebot_client = BotClientManager.get_client("onebot")
    return {
        "status": "healthy",
        "bot_client": {
            "connected": onebot_client.is_connected if onebot_client else False,
            "type": onebot_client.client_type if onebot_client else None
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
