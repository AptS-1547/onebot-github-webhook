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
import pathlib
import shutil
import importlib
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import api_router
from app.models.config import get_settings, Config
from app.botclient.manager import BotClientManager
from app.botclient.factory import BotClientFactory
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


def load_platform_module(platform: str, custom_module: Optional[str] = None) -> bool:
    """
    动态加载平台客户端模块。

    Args:
        platform: 平台类型（如 onebot, telegram 等）
        custom_module: 自定义模块路径（可选，默认为 app.botclient.{platform}）

    Returns:
        bool: 是否成功加载模块

    Raises:
        ImportError: 模块加载失败
    """
    # 确定模块路径
    if custom_module:
        module_path = custom_module
    else:
        # 按约定自动推断：platform "onebot" -> "app.botclient.onebot"
        module_path = f"app.botclient.{platform}"

    try:
        importlib.import_module(module_path)
        logger.info("已加载平台模块: 平台=%s, 模块=%s", platform, module_path)
        return True
    except ImportError as e:
        logger.error("无法加载模块: 模块=%s, 错误=%s", module_path, e)
        raise ImportError(f"无法加载平台 '{platform}' 的模块 '{module_path}': {e}") from e


def auto_migrate_yaml_to_toml() -> bool:
    """
    自动迁移 YAML 配置到 TOML（如果需要）。

    Returns:
        bool: 是否执行了迁移
    """
    yaml_path = pathlib.Path.cwd() / "config.yaml"
    toml_path = pathlib.Path.cwd() / "config.toml"

    # 如果 TOML 已存在，无需迁移
    if toml_path.exists():
        return False

    # 如果 YAML 不存在，无需迁移
    if not yaml_path.exists():
        return False

    try:
        logger.info("=" * 60)
        logger.info("检测到 YAML 配置文件，开始自动迁移到 TOML...")
        logger.info("=" * 60)

        # 加载 YAML 配置
        config = Config.from_yaml_legacy()

        # 保存为 TOML
        config.to_toml_file()

        # 创建 YAML 备份
        backup_path = yaml_path.with_suffix('.yaml.bak')
        shutil.copy2(yaml_path, backup_path)

        logger.info("✓ 配置迁移成功！")
        logger.info("  原文件: %s", yaml_path)
        logger.info("  新文件: %s", toml_path)
        logger.info("  备份: %s", backup_path)
        logger.info("=" * 60)

        return True

    except Exception as e:  # pylint: disable=broad-except
        logger.error("自动迁移失败: %s", e)
        logger.warning("将使用 YAML 配置继续运行")
        return False


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    管理应用程序生命周期的上下文管理器。

    在应用启动时初始化资源，在应用关闭时释放资源。
    """
    # 尝试自动迁移配置
    auto_migrate_yaml_to_toml()

    # 加载配置
    config = get_settings()

    # 确定配置文件类型
    config_file = "config.toml" if pathlib.Path("config.toml").exists() else "config.yaml"
    logger.log_config_loaded(config_file, len(config.webhook_sources))

    # 初始化 Bot 客户端（支持多平台）
    if not config.bot_backends:
        logger.warning("未配置任何 Bot 后端")
    else:
        # 初始化所有启用的 Bot 后端
        for backend_config in config.bot_backends:
            if not backend_config.enabled:
                logger.info("跳过已禁用的 Bot 后端: %s", backend_config.name)
                continue

            try:
                # 动态加载平台模块（触发工厂注册）
                load_platform_module(
                    backend_config.platform,
                    backend_config.module
                )

                # 使用工厂模式创建客户端
                client = BotClientFactory.create(backend_config)

                # 如果是 WebSocket 客户端，启动连接
                if hasattr(client, 'start'):
                    await client.start(max_retries=5, retry_delay=2.0)

                # 注册客户端到管理器
                await BotClientManager.register_client(backend_config.name, client)

                logger.info("客户端已注册: 名称=%s, 类型=%s",
                           backend_config.name, backend_config.platform)

            except ImportError as e:
                logger.error("无法加载平台模块: 名称=%s, 平台=%s, 错误=%s",
                           backend_config.name, backend_config.platform, e)
                raise BotClientInitializationError(
                    f"无法加载平台 '{backend_config.platform}' 的客户端模块: {e}",
                    details={"name": backend_config.name, "platform": backend_config.platform}
                ) from e

            except KeyError as e:
                logger.error("不支持的平台类型: 名称=%s, 平台=%s",
                           backend_config.name, backend_config.platform)
                raise BotClientInitializationError(
                    f"不支持的平台类型 '{backend_config.platform}'。"
                    f"可能原因：模块加载成功但未注册到工厂，或平台名称拼写错误。",
                    details={"name": backend_config.name, "platform": backend_config.platform}
                ) from e

            except BotClientConnectionError as e:
                logger.error("Bot 客户端连接失败: 名称=%s, 错误=%s",
                           backend_config.name, e)
                raise BotClientInitializationError(
                    f"Bot 客户端 '{backend_config.name}' 连接失败: {e}",
                    details={"name": backend_config.name, "platform": backend_config.platform}
                ) from e

            except BotClientTimeoutError as e:
                logger.error("Bot 客户端初始化超时: 名称=%s, 错误=%s",
                           backend_config.name, e)
                raise BotClientInitializationError(
                    f"Bot 客户端 '{backend_config.name}' 初始化超时: {e}",
                    details={"name": backend_config.name, "platform": backend_config.platform}
                ) from e

            except Exception as e:
                logger.error("初始化 Bot 客户端时发生未知错误: 名称=%s, 错误=%s",
                           backend_config.name, e)
                raise BotClientInitializationError(
                    f"Bot 客户端 '{backend_config.name}' 初始化失败: {e}",
                    details={"name": backend_config.name, "platform": backend_config.platform}
                ) from e

    # 统计已注册的客户端
    registered_clients = BotClientManager.list_clients()
    if registered_clients:
        logger.info("Bot 客户端初始化完成，共 %d 个客户端", len(registered_clients))
    else:
        logger.warning("没有成功注册任何 Bot 客户端")

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
    clients = BotClientManager.list_clients()
    bot_clients_status = {}

    for name, client in clients.items():
        bot_clients_status[name] = {
            "connected": client.is_connected,
            "type": client.client_type
        }

    return {
        "status": "healthy",
        "bot_clients": bot_clients_status
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
