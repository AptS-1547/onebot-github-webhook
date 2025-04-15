import json
import logging
from typing import Union, List, Dict, Any
import aiohttp

logger = logging.getLogger(__name__)

class WSConnectionException(Exception):
    """WebSocket 连接异常"""

class OnebotClient:
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
    """基于 aiohttp 的 OneBot V11 WebSocket 客户端，仅用于发送消息"""

    async def send_message(
        self,
        onebot_type: str,
        onebot_id: int,
        message: Union[str, List[Dict[str, Any]]],
        auto_escape: bool = False
    ) -> Dict[str, Any]:
        """
        发送群消息
        
        参数:
            user_id: 发送消息的用户 ID
            onebot_id: 发送消息的群 ID
            message: 要发送的消息，可以是字符串或消息段列表
            auto_escape: 是否转义 CQ 码，默认为 False
        
        返回:
            API 响应
        """
        request = {
            "action": "send_msg",
            "params": {
                "message_type": onebot_type,
                "message": message,
                "auto_escape": auto_escape
            },
            "echo": "The_ESAP_Project_Github_Notification"
        }

        if onebot_type == "group":
            request["params"]["group_id"] = onebot_id
        elif onebot_type == "private":
            request["params"]["user_id"] = onebot_id

        # 准备 headers
        headers = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        try:
            # 使用 aiohttp 的 ClientSession
            async with aiohttp.ClientSession() as session:
                # 创建 WebSocket 连接
                async with session.ws_connect(
                    self.onebot_url,
                    headers=headers
                ) as ws:
                    # 发送请求
                    await ws.send_str(json.dumps(request))

                    # 接收响应
                    response = await ws.receive()

                    # 处理消息类型
                    if response.type == aiohttp.WSMsgType.TEXT:
                        return json.loads(response.data)
                    elif response.type == aiohttp.WSMsgType.CLOSED:
                        logger.debug("WebSocket 连接已关闭")
                        return {"status": "ok", "retcode": 0, "data": {"message_id": -1}}
                    elif response.type == aiohttp.WSMsgType.ERROR:
                        logger.error("WebSocket 连接错误: %s", ws.exception())
                        raise WSConnectionException("WebSocket 连接错误")
                    else:
                        logger.warning("收到未知类型的消息: %s", response.type)
                        return {"status": "error", "retcode": -1, "message": f"未知响应类型: {response.type}"}

        except aiohttp.ClientError as e:
            logger.error("aiohttp 客户端错误: %s", e)
            raise
        except Exception as e:
            logger.error("发送群消息时出错: %s", e)
            raise

class OneBotHTTPClient(OnebotClient):
    """基于 aiohttp 的 OneBot V11 HTTP 客户端，仅用于发送消息"""

    async def send_message(
        self,
        onebot_type: str,
        onebot_id: int,
        message: Union[str, List[Dict[str, Any]]],
        auto_escape: bool = False
    ) -> Dict[str, Any]:
        """
        发送群消息
        
        参数:
            user_id: 发送消息的用户 ID
            onebot_id: 发送消息的群 ID
            message: 要发送的消息，可以是字符串或消息段列表
            auto_escape: 是否转义 CQ 码，默认为 False
        
        返回:
            API 响应
        """
        request = {
            "message_type": onebot_type,
            "message": message,
            "auto_escape": auto_escape
        }

        if onebot_type == "group":
            request["group_id"] = onebot_id
        elif onebot_type == "private":
            request["user_id"] = onebot_id

        # 准备 headers
        headers = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        headers["Content-Type"] = "application/json"

        try:
            # 使用 aiohttp 的 ClientSession
            async with aiohttp.ClientSession() as session:
                # 发送请求
                async with session.post(
                    self.onebot_url + "/send_msg",
                    json=request,
                    headers=headers
                ) as response:
                    # 检查响应状态码
                    if response.status != 200:
                        logger.error("HTTP 请求失败，状态码: %s", response.status)
                        return {"status": "error", "retcode": -1, "message": f"HTTP 错误: {response.status}"}

                    # 解析 JSON 响应
                    data = await response.json()
                    return data

        except aiohttp.ClientError as e:
            logger.error("aiohttp 客户端错误: %s", e)
            raise
        except Exception as e:
            logger.error("发送群消息时出错: %s", e)
            raise

# 消息段工具函数
def text(content: str) -> Dict[str, Any]:
    """纯文本消息"""
    return {"type": "text", "data": {"text": content}}

def at(qq: int) -> Dict[str, Any]:
    """@某人"""
    return {"type": "at", "data": {"qq": str(qq)}}

def image(file: str) -> Dict[str, Any]:
    """图片消息"""
    return {"type": "image", "data": {"file": file}}

async def send_github_notification(
    onebot_type: str,
    onebot_url: str,
    access_token: str,
    repo_name: str,
    branch: str,
    pusher: str,
    commit_count: int,
    commits: List[Dict],
    onebot_send_type: str = "group",
    onebot_id: int = 0
):
    """发送 GitHub 推送通知"""

    if onebot_type == "ws":
        client = OneBotWebSocketClient(onebot_url, access_token)
    elif onebot_type == "http":
        client = OneBotHTTPClient(onebot_url, access_token)
    else:
        logger.error("不支持的 OneBot 连接类型: %s", onebot_type)
        return None

    # 构建消息
    message = [
        text("📢 GitHub 推送通知\n"),
        text(f"仓库：{repo_name}\n"),
        text(f"分支：{branch}\n"),
        text(f"推送者：{pusher}\n"),
        text(f"提交数量：{commit_count}\n\n")
    ]

    # 添加最近的提交信息（最多3条）
    for i, commit in enumerate(commits[:3]):
        commit_id = commit.get("id", "")[:7]
        commit_msg = commit.get("message", "").split("\n")[0]  # 只取第一行
        author = commit.get("author", {}).get("name", "")

        message.append(text(f"[{i+1}] {commit_id} by {author}\n"))
        message.append(text(f"    {commit_msg}\n"))

    # 发送消息
    try:
        if onebot_send_type in ["group", "private"]:
            result = await client.send_message(onebot_send_type, onebot_id, message)
        else:
            logger.error("不支持的 OneBot 类型: %s", onebot_send_type)
            return None
        return result
    except Exception as e:                                 # pylint: disable=broad-except
        logger.error("发送 GitHub 通知失败: %s", e)
        return None
