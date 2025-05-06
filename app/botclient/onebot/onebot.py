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
OneBot V11 客户端
本模块提供了一个 OneBot V11 客户端的实现，支持通过 WebSocket 和 HTTP 发送消息。
作者：AptS:1547
版本：0.1.0-alpha
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

import json
import uuid
import asyncio
import logging
from typing import Union, List, Dict, Any
import aiohttp

logger = logging.getLogger(__name__)

class OneBotException(Exception):
    """OneBot 基础异常类"""

class WSConnectionException(OneBotException):
    """WebSocket 连接异常"""

class OneBotWebSocketManager:                # pylint: disable=too-many-instance-attributes
    """管理 OneBot WebSocket 连接的单例类"""
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, onebot_url: str, access_token: str = ""):
        if self._initialized:
            return

        self.onebot_url = onebot_url
        self.access_token = access_token
        self.ws = None
        self.session = None
        self.response_futures = {}
        self.running = False
        self._initialized = True
        self._lock = asyncio.Lock()
        self._receiver_task = None

    async def start(self, max_retries: int = 5, retry_delay: float = 2.0):
        """
        启动 WebSocket 连接，支持重试机制
        
        参数:
            max_retries: 最大重试次数
            retry_delay: 重试间隔（秒）
        """
        async with self._lock:
            if self.running:
                return

            retries = 0
            current_delay = retry_delay

            while retries <= max_retries:
                try:
                    if retries > 0:
                        logger.info("尝试重新连接 WebSocket (第 %d 次)...", retries)

                    self.session = aiohttp.ClientSession()

                    headers = {}
                    if self.access_token:
                        headers["Authorization"] = f"Bearer {self.access_token}"

                    self.ws = await self.session.ws_connect(self.onebot_url, headers=headers)
                    self.running = True

                    # 启动消息接收器
                    self._receiver_task = asyncio.create_task(self._message_receiver())
                    logger.info("WebSocket 连接已建立")
                    return  # 成功连接，退出循环

                except Exception as e:          # pylint: disable=broad-except
                    if self.session:
                        await self.session.close()
                        self.session = None

                    retries += 1

                    if retries > max_retries:
                        logger.error("WebSocket 连接失败，已达到最大重试次数: %d", max_retries)
                        raise WSConnectionException(f"无法建立 WebSocket 连接: {e}") from e

                    logger.warning("WebSocket 连接失败，将在 %.1f 秒后重试: %s", current_delay, e)
                    await asyncio.sleep(current_delay)
                    current_delay = min(current_delay * 1.5, 30)  # 指数退避，但最多等待30秒

    async def stop(self):
        """关闭 WebSocket 连接"""
        async with self._lock:
            if not self.running:
                return

            self.running = False

            # 取消接收器任务
            if self._receiver_task and not self._receiver_task.done():
                self._receiver_task.cancel()
                try:
                    await self._receiver_task
                except asyncio.CancelledError:
                    pass
                self._receiver_task = None

            # 关闭所有等待中的 Future
            for _, future in self.response_futures.items():
                if not future.done():
                    future.set_exception(WSConnectionException("WebSocket 连接已关闭"))
            self.response_futures.clear()

            # 关闭WebSocket连接
            if self.ws:
                await self.ws.close()
                self.ws = None

            # 关闭HTTP会话
            if self.session:
                await self.session.close()
                self.session = None

            logger.info("WebSocket 连接已关闭")

    async def _message_receiver(self):           # pylint: disable=too-many-branches, too-many-statements
        """接收并处理 WebSocket 消息的异步任务"""
        try:                                     # pylint: disable=too-many-nested-blocks
            while self.running and self.ws:
                try:
                    response = await self.ws.receive()

                    if response.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(response.data)
                        echo = data.get("echo")

                        if echo and echo in self.response_futures:
                            future = self.response_futures.pop(echo)
                            if not future.done():
                                future.set_result(data)
                        else:
                            logger.debug("收到无匹配 echo 的响应或不含 echo: %s", data)

                    elif response.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING):
                        logger.warning("WebSocket 连接已关闭: %s", response.data)
                        break

                    elif response.type == aiohttp.WSMsgType.ERROR:
                        logger.error("WebSocket 连接错误: %s", response.data)
                        break

                    else:
                        logger.warning("收到未知类型的消息: %s", response.type)

                except asyncio.CancelledError:
                    logger.info("WebSocket 接收任务被取消")
                except aiohttp.ClientError as e:
                    logger.error("处理 WebSocket 消息时出错: %s", str(e))
                    if self.ws:
                        await self.ws.close()
                    break
                except Exception as e:      # pylint: disable=broad-except
                    logger.error("处理 WebSocket 消息时出错: %s", str(e))
                    break

        except asyncio.CancelledError:
            logger.info("WebSocket 接收任务被取消")

        finally:
            if self.running:
                logger.info("WebSocket 连接中断，正在重新连接...")
                asyncio.create_task(self._attempt_reconnect())

    async def _attempt_reconnect(self, retry_delay: float = 5.0, max_delay: float = 60.0):
        """尝试重新连接WebSocket"""
        # 确保先停止现有连接
        await self.stop()

        delay = retry_delay
        while self.running:
            try:
                logger.info("尝试重新连接 WebSocket (延迟 %.1f 秒)...", delay)
                await asyncio.sleep(delay)
                await self.start(max_retries=0)
                return  # 如果成功连接则退出
            except Exception as e:      # pylint: disable=broad-except
                logger.error("重新连接失败: %s", e)
                delay = min(delay * 1.5, max_delay)

    async def send_request(self, request: dict, timeout: float = 30.0) -> Dict[str, Any]:
        """
        发送请求并等待响应
        
        参数:
            request: 请求数据
            timeout: 超时时间（秒）
            
        返回:
            API 响应
        """
        if not self.running:
            # 如果尚未运行，则启动连接
            await self.start()

        if not self.ws:
            raise WSConnectionException("WebSocket 连接不可用")

        echo_id = str(uuid.uuid4())
        request["echo"] = echo_id

        future = asyncio.Future()
        self.response_futures[echo_id] = future

        try:
            await self.ws.send_str(json.dumps(request))

            try:
                response = await asyncio.wait_for(future, timeout)
                return response
            except asyncio.TimeoutError:
                self.response_futures.pop(echo_id, None)
                logger.error("请求超时：%s", echo_id)
                return {
                    "status": "error",
                    "retcode": -1,
                    "message": "请求超时",
                    "echo": echo_id
                }

        except asyncio.TimeoutError:
            self.response_futures.pop(echo_id, None)
            logger.error("请求超时：%s", echo_id)
            return {
                "status": "error",
                "retcode": -1,
                "message": "请求超时",
                "echo": echo_id
            }
        except aiohttp.ClientError as e:
            self.response_futures.pop(echo_id, None)
            logger.error("发送请求失败: %s", str(e))
            raise
        except Exception as e:
            self.response_futures.pop(echo_id, None)
            logger.error("发送请求失败: %s", str(e))
            raise

class OnebotClient:      # pylint: disable=too-few-public-methods
    """OneBot 客户端基类"""
    def __init__(self, onebot_url: str, access_token: str = ""):
        """
        初始化 OneBot 客户端

        参数:
            onebot_url: OneBot 实现的 URL 地址
            access_token: 鉴权 token，如果有的话
        """
        self.onebot_url = onebot_url
        self.access_token = access_token

    async def send_message(
        self,
        onebot_type: str,
        onebot_id: int,
        message: Union[str, List[Dict[str, Any]]],
        auto_escape: bool = False
    ) -> Dict[str, Any]:
        """
        发送消息的抽象方法，子类需要实现

        参数:
            onebot_type: 消息类型，例如 "group" 或 "private"
            onebot_id: 消息接收者的 ID
            message: 要发送的消息，可以是字符串或消息段列表
            auto_escape: 是否转义 CQ 码，默认为 False
        
        返回:
            API 响应
        """
        raise NotImplementedError("send_message 方法需要在子类中实现")

class OneBotWebSocketClient(OnebotClient):
    """基于 WebSocket 的 OneBot V11 客户端"""

    def __init__(self, onebot_url: str, access_token: str = ""):
        super().__init__(onebot_url, access_token)
        self.manager = OneBotWebSocketManager(onebot_url, access_token)

    async def start(self, max_retries: int = 5, retry_delay: float = 2.0):
        """启动 WebSocket 连接"""
        await self.manager.start(max_retries=max_retries, retry_delay=retry_delay)

    async def stop(self):
        """停止 WebSocket 连接"""
        await self.manager.stop()

    async def send_message(
        self,
        onebot_type: str,
        onebot_id: int,
        message: Union[str, List[Dict[str, Any]]],
        auto_escape: bool = False
    ) -> Dict[str, Any]:
        """发送消息"""
        if not self._validate_message_type(onebot_type):
            raise ValueError(f"不支持的消息类型: {onebot_type}")

        request = {
            "action": "send_msg",
            "params": {
                "message_type": onebot_type,
                "message": message,
                "auto_escape": auto_escape
            }
        }

        if onebot_type == "group":
            request["params"]["group_id"] = onebot_id
        else:  # private
            request["params"]["user_id"] = onebot_id

        try:
            return await self.manager.send_request(request)
        except Exception as e:
            logger.error("发送消息时出错: %s", e)
            raise

    def _validate_message_type(self, onebot_type: str) -> bool:
        """验证消息类型是否有效"""
        if onebot_type not in ["group", "private"]:
            logger.error("不支持的消息类型: {onebot_type}")
            return False
        return True

class OneBotHTTPClient(OnebotClient):      # pylint: disable=too-few-public-methods
    """基于 HTTP 的 OneBot V11 客户端"""

    async def send_message(
        self,
        onebot_type: str,
        onebot_id: int,
        message: Union[str, List[Dict[str, Any]]],
        auto_escape: bool = False
    ) -> Dict[str, Any]:
        """发送消息"""
        if onebot_type not in ["group", "private"]:
            logger.error("不支持的消息类型: {onebot_type}")
            return {
                "status": "error",
                "retcode": -1,
                "message": f"不支持的消息类型: {onebot_type}"
            }

        request = {
            "message_type": onebot_type,
            "message": message,
            "auto_escape": auto_escape
        }

        if onebot_type == "group":
            request["group_id"] = onebot_id
        else:  # private
            request["user_id"] = onebot_id

        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.onebot_url}/send_msg",
                    json=request,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        logger.error("HTTP 请求失败，状态码: %d", response.status)
                        return {
                            "status": "error",
                            "retcode": -1,
                            "message": f"HTTP 错误: {response.status}"
                        }

                    data = await response.json()
                    return data
        except aiohttp.ClientError as e:
            logger.error("aiohttp 客户端错误: %s", e)
            raise
        except Exception as e:
            logger.error("发送消息时出错: %s", e)
            raise

# 全局客户端实例
_ONEBOT_CLIENT = None

async def init_onebot_client(
        protocol_type: str,
        url: str,
        access_token: str = "",
        max_retries: int = 5,
        retry_delay: float = 2.0
    ) -> OnebotClient:
    """
    初始化全局 OneBot 客户端
    
    参数:
        protocol_type: 客户端类型，"ws" 或 "http"
        url: OneBot 实现的 URL 地址
        access_token: 鉴权 token，如果有的话
        max_retries: 最大重试次数 (仅用于 WebSocket)
        retry_delay: 重试间隔（秒）(仅用于 WebSocket)
    
    返回:
        已初始化的客户端实例
    """
    global _ONEBOT_CLIENT  # pylint: disable=global-statement

    if _ONEBOT_CLIENT is not None:
        logger.warning("OneBot 客户端已经初始化，将返回现有实例")
        return _ONEBOT_CLIENT

    if protocol_type == "ws":
        _ONEBOT_CLIENT = OneBotWebSocketClient(url, access_token)
        # 启动 WebSocket 连接
        logger.info("正在初始化 WebSocket 连接...")
        try:
            await _ONEBOT_CLIENT.manager.start(max_retries=max_retries, retry_delay=retry_delay)
            logger.info("WebSocket 连接已成功建立")
        except Exception as e:  # pylint: disable=broad-except
            logger.error("建立 WebSocket 连接失败: %s", e)
            raise
    elif protocol_type == "http":
        _ONEBOT_CLIENT = OneBotHTTPClient(url, access_token)
    else:
        raise ValueError(f"不支持的协议类型: {protocol_type}")

    return _ONEBOT_CLIENT

def get_onebot_client():
    """
    获取全局 OneBot 客户端实例
    如果客户端尚未初始化，会抛出异常
    
    返回:
        OneBot 客户端实例
    """
    if _ONEBOT_CLIENT is None:
        raise RuntimeError("OneBot 客户端尚未初始化，请先调用 init_onebot_client")

    return _ONEBOT_CLIENT

async def shutdown_onebot_client():
    """关闭 OneBot 客户端连接"""
    global _ONEBOT_CLIENT  # pylint: disable=global-statement

    if _ONEBOT_CLIENT is None:
        return

    if isinstance(_ONEBOT_CLIENT, OneBotWebSocketClient):
        logger.info("正在关闭 WebSocket 连接...")
        try:
            await _ONEBOT_CLIENT.manager.stop()
            logger.info("WebSocket 连接已成功关闭")
        except Exception as e:  # pylint: disable=broad-except
            logger.error("关闭 WebSocket 连接时出错: %s", e)

    _ONEBOT_CLIENT = None
