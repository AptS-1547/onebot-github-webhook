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
版本：0.1.0-alpha
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import api_router
from app.models import config
from app.onebot import init_onebot_client, shutdown_onebot_client


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    管理应用程序生命周期的上下文管理器
    在应用启动时初始化资源，在应用关闭时释放资源
    """

    try:
        await init_onebot_client(
            client_type=config.ONEBOT_TYPE,
            url=config.ONEBOT_URL,
            access_token=config.ONEBOT_ACCESS_TOKEN
        )
    except Exception as e:  # pylint: disable=broad-except
        logger.error("初始化 OneBot 客户端失败: %s", e)
        sys.exit(1)

    yield

    await shutdown_onebot_client()

app = FastAPI(lifespan=lifespan)

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
