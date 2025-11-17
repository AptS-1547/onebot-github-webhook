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

本模块提供了 OneBot V11 协议的客户端实现，支持 WebSocket 和 HTTP 两种协议。

作者：AptS:1547
版本：0.2.0
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

import json
import uuid
import asyncio
from typing import Union, List, Dict, Any, Optional

import aiohttp

from app.botclient.base import BotClientInterface
from app.models.universal_message import UniversalMessage
from app.exceptions import (
    BotClientError,
    BotClientConnectionError,
    BotClientTimeoutError
)
from app.utils.logger import StructuredLogger

logger = StructuredLogger(__name__)


class OneBotWebSocketManager:
    """
    管理 OneBot WebSocket 连接。

    负责 WebSocket 连接的建立、消息收发和重连逻辑。

    Attributes:
        onebot_url: OneBot WebSocket 服务器 URL
        access_token: 访问令牌
        ws: WebSocket 连接对象
        session: aiohttp ClientSession
        response_futures: 等待响应的 Future 字典
        running: 连接是否运行中
        _lock: 异步锁
        _receiver_task: 消息接收任务
        _reconnect_attempts: 重连尝试次数
    """

    def __init__(self, onebot_url: str, access_token: str = "") -> None:
        """
        初始化 WebSocket 管理器。

        Args:
            onebot_url: OneBot WebSocket 服务器 URL
            access_token: 访问令牌（可选）
        """
        self.onebot_url = onebot_url
        self.access_token = access_token
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.response_futures: Dict[str, asyncio.Future] = {}
        self.running = False
        self._lock = asyncio.Lock()
        self._receiver_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        self._reconnect_attempts = 0

    async def start(
        self,
        max_retries: int = 5,
        retry_delay: float = 2.0
    ) -> None:
        """
        启动 WebSocket 连接，支持重试机制。

        Args:
            max_retries: 最大重试次数
            retry_delay: 初始重试间隔（秒）

        Raises:
            BotClientConnectionError: 连接失败且达到最大重试次数
        """
        async with self._lock:
            if self.running:
                logger.debug("WebSocket 已在运行中，跳过启动")
                return

            retries = 0
            current_delay = retry_delay

            while retries <= max_retries:
                try:
                    if retries > 0:
                        logger.log_bot_client_reconnect(
                            "onebot",
                            retries,
                            current_delay,
                            self.onebot_url
                        )

                    self.session = aiohttp.ClientSession()

                    headers = {}
                    if self.access_token:
                        headers["Authorization"] = f"Bearer {self.access_token}"

                    self.ws = await self.session.ws_connect(
                        self.onebot_url,
                        headers=headers
                    )
                    self.running = True
                    self._reconnect_attempts = 0

                    # 启动消息接收器
                    self._receiver_task = asyncio.create_task(
                        self._message_receiver()
                    )

                    logger.log_bot_client_connection(
                        "onebot",
                        self.onebot_url,
                        True
                    )
                    return  # 成功连接，退出循环

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if self.session:
                        await self.session.close()
                        self.session = None

                    retries += 1

                    if retries > max_retries:
                        error_msg = f"无法建立 WebSocket 连接: {e}"
                        logger.log_bot_client_connection(
                            "onebot",
                            self.onebot_url,
                            False,
                            error_msg
                        )
                        raise BotClientConnectionError(
                            error_msg,
                            details={"url": self.onebot_url, "retries": retries}
                        ) from e

                    logger.warning(
                        "WebSocket 连接失败，将在 %.1f 秒后重试: %s",
                        current_delay,
                        e
                    )
                    await asyncio.sleep(current_delay)
                    current_delay = min(current_delay * 1.5, 30)

    async def stop(self) -> None:
        """
        关闭 WebSocket 连接并清理资源。
        """
        async with self._lock:
            if not self.running:
                return

            self.running = False

            # 取消重连任务
            if self._reconnect_task and not self._reconnect_task.done():
                self._reconnect_task.cancel()
                try:
                    await self._reconnect_task
                except asyncio.CancelledError:
                    pass
                self._reconnect_task = None

            # 取消接收器任务
            if self._receiver_task and not self._receiver_task.done():
                self._receiver_task.cancel()
                try:
                    await self._receiver_task
                except asyncio.CancelledError:
                    pass
                self._receiver_task = None

            # 关闭所有等待中的 Future
            for echo_id, future in self.response_futures.items():
                if not future.done():
                    future.set_exception(
                        BotClientConnectionError("WebSocket 连接已关闭")
                    )
            self.response_futures.clear()

            # 关闭 WebSocket 连接
            if self.ws:
                await self.ws.close()
                self.ws = None

            # 关闭 HTTP 会话
            if self.session:
                await self.session.close()
                self.session = None

            logger.info("WebSocket 连接已关闭")

    async def _message_receiver(self) -> None:
        """
        接收并处理 WebSocket 消息的异步任务。
        """
        try:
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
                            logger.debug(
                                "收到无匹配 echo 的响应或不含 echo: %s",
                                data
                            )

                    elif response.type in (
                        aiohttp.WSMsgType.CLOSED,
                        aiohttp.WSMsgType.CLOSING
                    ):
                        logger.warning(
                            "WebSocket 连接已关闭: %s",
                            response.data
                        )
                        break

                    elif response.type == aiohttp.WSMsgType.ERROR:
                        logger.error(
                            "WebSocket 连接错误: %s",
                            response.data
                        )
                        break

                    else:
                        logger.warning(
                            "收到未知类型的消息: %s",
                            response.type
                        )

                except asyncio.CancelledError:
                    logger.debug("WebSocket 接收任务被取消")
                    raise
                except (aiohttp.ClientError, json.JSONDecodeError) as e:
                    logger.error("处理 WebSocket 消息时出错: %s", e)
                    break

        except asyncio.CancelledError:
            logger.debug("WebSocket 接收任务被取消")

        finally:
            # 只有在仍然运行时才触发重连
            if self.running:
                logger.info("WebSocket 连接中断，准备重新连接...")
                # 使用受控的方式创建重连任务
                self._reconnect_task = asyncio.create_task(
                    self._attempt_reconnect()
                )

    async def _attempt_reconnect(
        self,
        retry_delay: float = 5.0,
        max_delay: float = 60.0,
        max_attempts: int = 10
    ) -> None:
        """
        尝试重新连接 WebSocket。

        Args:
            retry_delay: 初始重试延迟（秒）
            max_delay: 最大重试延迟（秒）
            max_attempts: 最大重连尝试次数
        """
        delay = retry_delay
        self._reconnect_attempts = 0

        while self.running and self._reconnect_attempts < max_attempts:
            try:
                self._reconnect_attempts += 1
                logger.log_bot_client_reconnect(
                    "onebot",
                    self._reconnect_attempts,
                    delay,
                    self.onebot_url
                )

                await asyncio.sleep(delay)
                await self.start(max_retries=0)
                return  # 成功重连

            except BotClientConnectionError as e:
                logger.error("重新连接失败: %s", e)
                delay = min(delay * 1.5, max_delay)

            except asyncio.CancelledError:
                logger.debug("重连任务被取消")
                return

        if self._reconnect_attempts >= max_attempts:
            logger.error(
                "已达到最大重连尝试次数 (%d)，放弃重连",
                max_attempts
            )
            self.running = False

    async def send_request(
        self,
        request: Dict[str, Any],
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        发送请求并等待响应。

        Args:
            request: 请求数据
            timeout: 超时时间（秒）

        Returns:
            Dict[str, Any]: API 响应

        Raises:
            BotClientConnectionError: WebSocket 未连接
            BotClientTimeoutError: 请求超时
            BotClientError: 其他错误
        """
        if not self.running:
            # 如果尚未运行，则启动连接
            await self.start()

        if not self.ws:
            raise BotClientConnectionError("WebSocket 连接不可用")

        echo_id = str(uuid.uuid4())
        request["echo"] = echo_id

        future: asyncio.Future = asyncio.Future()
        self.response_futures[echo_id] = future

        try:
            await self.ws.send_str(json.dumps(request))

            response = await asyncio.wait_for(future, timeout)
            return response

        except asyncio.TimeoutError as e:
            self.response_futures.pop(echo_id, None)
            logger.error("请求超时: %s", echo_id)
            raise BotClientTimeoutError(
                f"请求超时: {echo_id}",
                details={"echo_id": echo_id, "timeout": timeout}
            ) from e

        except aiohttp.ClientError as e:
            self.response_futures.pop(echo_id, None)
            logger.error("发送请求失败: %s", e)
            raise BotClientError(
                f"发送请求失败: {e}",
                details={"echo_id": echo_id}
            ) from e

        except Exception as e:
            self.response_futures.pop(echo_id, None)
            logger.error("发送请求失败: %s", e)
            raise BotClientError(
                f"发送请求失败: {e}",
                details={"echo_id": echo_id}
            ) from e


class OneBotWebSocketClient(BotClientInterface):
    """
    基于 WebSocket 的 OneBot V11 客户端。

    实现了 BotClientInterface 接口，提供 WebSocket 连接的消息发送功能。

    Attributes:
        onebot_url: OneBot WebSocket 服务器 URL
        access_token: 访问令牌
        manager: WebSocket 连接管理器
    """

    def __init__(self, onebot_url: str, access_token: str = "") -> None:
        """
        初始化 WebSocket 客户端。

        Args:
            onebot_url: OneBot WebSocket 服务器 URL
            access_token: 访问令牌（可选）
        """
        self.onebot_url = onebot_url
        self.access_token = access_token
        self.manager = OneBotWebSocketManager(onebot_url, access_token)

    async def start(
        self,
        max_retries: int = 5,
        retry_delay: float = 2.0
    ) -> None:
        """
        启动 WebSocket 连接。

        Args:
            max_retries: 最大重试次数
            retry_delay: 重试间隔（秒）
        """
        await self.manager.start(max_retries=max_retries, retry_delay=retry_delay)

    async def send_message(
        self,
        target_type: str,
        target_id: Union[int, str],
        message: Union[str, List[Dict[str, Any]], UniversalMessage],
        **kwargs: Any
    ) -> bool:
        """
        发送消息到指定目标。

        Args:
            target_type: 目标类型（"group" 或 "private"）
            target_id: 目标 ID（群号或用户 QQ 号）
            message: 消息内容
                - UniversalMessage: 通用消息（自动转换）
                - str: 纯文本
                - List[Dict]: OneBot 消息段列表
            **kwargs: 额外参数，如 auto_escape

        Returns:
            bool: 发送成功返回 True

        Raises:
            ValueError: 目标类型不支持
            BotClientError: 发送失败
        """
        # 转换 UniversalMessage 为 OneBot 格式
        if isinstance(message, UniversalMessage):
            message = message.to_onebot()

        # 确保 target_id 是整数
        if isinstance(target_id, str):
            target_id = int(target_id)

        if target_type not in ["group", "private"]:
            raise ValueError(f"不支持的目标类型: {target_type}")

        auto_escape = kwargs.get("auto_escape", False)

        request = {
            "action": "send_msg",
            "params": {
                "message_type": target_type,
                "message": message,
                "auto_escape": auto_escape
            }
        }

        if target_type == "group":
            request["params"]["group_id"] = target_id
        else:  # private
            request["params"]["user_id"] = target_id

        try:
            response = await self.manager.send_request(request)

            # 检查响应状态
            if response.get("status") == "ok" or response.get("retcode") == 0:
                logger.log_bot_message_sent(
                    "onebot",
                    target_type,
                    target_id,
                    True,
                    str(message)[:50] if isinstance(message, str) else "消息段"
                )
                return True

            error_msg = response.get("message", "未知错误")
            logger.log_bot_message_sent(
                "onebot",
                target_type,
                target_id,
                False,
                None,
                error_msg
            )
            return False

        except (BotClientTimeoutError, BotClientError) as e:
            logger.log_bot_message_sent(
                "onebot",
                target_type,
                target_id,
                False,
                None,
                str(e)
            )
            raise

    async def close(self) -> None:
        """
        关闭客户端连接。
        """
        await self.manager.stop()

    @property
    def is_connected(self) -> bool:
        """
        检查是否已连接。

        Returns:
            bool: 已连接返回 True
        """
        return self.manager.running and self.manager.ws is not None

    @property
    def client_type(self) -> str:
        """
        获取客户端类型。

        Returns:
            str: "onebot"
        """
        return "onebot"


class OneBotHTTPClient(BotClientInterface):
    """
    基于 HTTP 的 OneBot V11 客户端。

    实现了 BotClientInterface 接口，提供 HTTP 请求的消息发送功能。

    Attributes:
        onebot_url: OneBot HTTP API 服务器 URL
        access_token: 访问令牌
    """

    def __init__(self, onebot_url: str, access_token: str = "") -> None:
        """
        初始化 HTTP 客户端。

        Args:
            onebot_url: OneBot HTTP API 服务器 URL
            access_token: 访问令牌（可选）
        """
        self.onebot_url = onebot_url
        self.access_token = access_token
        self._session: Optional[aiohttp.ClientSession] = None

    async def send_message(
        self,
        target_type: str,
        target_id: Union[int, str],
        message: Union[str, List[Dict[str, Any]], UniversalMessage],
        **kwargs: Any
    ) -> bool:
        """
        发送消息到指定目标。

        Args:
            target_type: 目标类型（"group" 或 "private"）
            target_id: 目标 ID（群号或用户 QQ 号）
            message: 消息内容
                - UniversalMessage: 通用消息（自动转换）
                - str: 纯文本
                - List[Dict]: OneBot 消息段列表
            **kwargs: 额外参数，如 auto_escape

        Returns:
            bool: 发送成功返回 True

        Raises:
            ValueError: 目标类型不支持
            BotClientError: 发送失败
        """
        # 转换 UniversalMessage 为 OneBot 格式
        if isinstance(message, UniversalMessage):
            message = message.to_onebot()

        # 确保 target_id 是整数
        if isinstance(target_id, str):
            target_id = int(target_id)

        if target_type not in ["group", "private"]:
            raise ValueError(f"不支持的目标类型: {target_type}")

        auto_escape = kwargs.get("auto_escape", False)

        request = {
            "message_type": target_type,
            "message": message,
            "auto_escape": auto_escape
        }

        if target_type == "group":
            request["group_id"] = target_id
        else:  # private
            request["user_id"] = target_id

        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        try:
            # 添加超时控制
            timeout = aiohttp.ClientTimeout(total=30)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.onebot_url}/send_msg",
                    json=request,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        error_msg = f"HTTP 错误: {response.status}"
                        logger.log_bot_message_sent(
                            "onebot",
                            target_type,
                            target_id,
                            False,
                            None,
                            error_msg
                        )
                        raise BotClientError(
                            error_msg,
                            details={
                                "status_code": response.status,
                                "url": f"{self.onebot_url}/send_msg"
                            }
                        )

                    data = await response.json()

                    # 检查响应状态
                    if data.get("status") == "ok" or data.get("retcode") == 0:
                        logger.log_bot_message_sent(
                            "onebot",
                            target_type,
                            target_id,
                            True,
                            str(message)[:50] if isinstance(message, str) else "消息段"
                        )
                        return True

                    error_msg = data.get("message", "未知错误")
                    logger.log_bot_message_sent(
                        "onebot",
                        target_type,
                        target_id,
                        False,
                        None,
                        error_msg
                    )
                    return False

        except asyncio.TimeoutError as e:
            error_msg = "HTTP 请求超时"
            logger.log_bot_message_sent(
                "onebot",
                target_type,
                target_id,
                False,
                None,
                error_msg
            )
            raise BotClientTimeoutError(error_msg) from e

        except aiohttp.ClientError as e:
            error_msg = f"HTTP 客户端错误: {e}"
            logger.log_bot_message_sent(
                "onebot",
                target_type,
                target_id,
                False,
                None,
                error_msg
            )
            raise BotClientError(error_msg) from e

    async def close(self) -> None:
        """
        关闭客户端连接。

        HTTP 客户端使用临时会话，无需显式关闭。
        """
        # HTTP 客户端使用临时 session，无需关闭

    @property
    def is_connected(self) -> bool:
        """
        检查是否已连接。

        Returns:
            bool: HTTP 客户端始终返回 True
        """
        return True

    @property
    def client_type(self) -> str:
        """
        获取客户端类型。

        Returns:
            str: "onebot"
        """
        return "onebot"
