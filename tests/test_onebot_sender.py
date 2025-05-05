import sys
import os
import json
import uuid
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch, call

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入测试对象
from app.onebot.onebot import (
    OneBotWebSocketManager, OneBotWebSocketClient, 
    OneBotHTTPClient, text
)
from app.onebot.onebot import WSConnectionException

# 全局测试变量
WS_URL = "wss://api.esaps.net/api/napcat/ws"
HTTP_URL = "http://localhost:5700"
ACCESS_TOKEN = "pJ*Z{{uzwbvi}rZrRN9CKaIvKJyjx*"
GROUP_ID = 982915192
USER_ID = 1464170336
TEST_UUID = "test-uuid-123456"
TEST_ECHO = "id1"

# 为了便于使用 aiohttp.WSMsgType 常量，我们创建一个模拟类
class WSMsgType:
    TEXT = 1
    CLOSED = 8
    ERROR = 4


@pytest.fixture
def onebot_config():
    """准备 OneBot 配置数据"""
    return {
        "url": WS_URL,
        "token": ACCESS_TOKEN,
        "type": "ws"
    }


@pytest.fixture
def message_data():
    """准备消息数据"""
    return {
        "type": "group",
        "id": GROUP_ID,
        "message": "Test message"
    }


@pytest.fixture
def github_data():
    """准备 GitHub 数据"""
    return {
        "repo_name": "user/repo",
        "branch": "main",
        "pusher": "tester",
        "commit_count": 2,
        "commits": [
            {
                "id": "1234567890abcdef",
                "message": "First commit message",
                "author": {"name": "Author1"}
            },
            {
                "id": "abcdef1234567890",
                "message": "Second commit message",
                "author": {"name": "Author2"}
            }
        ]
    }


class TestOneBotWebSocketManager:
    """测试 WebSocket 连接管理器"""

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_singleton_pattern(self, mock_session):
        """测试单例模式"""
        # 创建两个实例
        manager1 = OneBotWebSocketManager(WS_URL, ACCESS_TOKEN)
        manager2 = OneBotWebSocketManager(WS_URL, "another_token")
        
        # 验证是同一个实例
        assert manager1 is manager2
        
        # 验证第一次创建的参数
        assert manager1.onebot_url == WS_URL
        assert manager1.access_token == ACCESS_TOKEN

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_start_connection(self, mock_session):
        """测试启动 WebSocket 连接"""
        # 设置模拟对象
        mock_ws = AsyncMock()
        mock_session_instance = AsyncMock()
        mock_session_instance.ws_connect = AsyncMock(return_value=mock_ws)
        mock_session.return_value = mock_session_instance
        
        # 创建并启动管理器
        manager = OneBotWebSocketManager(WS_URL, ACCESS_TOKEN)
        await manager.start()
        
        # 验证连接被正确建立
        mock_session_instance.ws_connect.assert_called_once_with(
            WS_URL,
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
        )
        assert manager.running is True
        assert manager.ws is mock_ws
        
        # 清理
        await manager.stop()

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_start_connection_failure(self, mock_session):
        """测试连接失败的情况"""
        # 模拟连接失败
        mock_session_instance = AsyncMock()
        mock_session_instance.ws_connect = AsyncMock(side_effect=Exception("Connection failed"))
        mock_session.return_value = mock_session_instance
        
        # 创建管理器
        manager = OneBotWebSocketManager(WS_URL, ACCESS_TOKEN)
        
        # 验证连接失败抛出正确的异常
        with pytest.raises(WSConnectionException) as excinfo:
            await manager.start()
            
        assert "Connection failed" in str(excinfo.value)


class TestOneBotClients:
    """测试消息发送客户端"""
    
    @pytest.mark.asyncio
    @patch('app.onebot.onebot.OneBotWebSocketManager.send_request')
    async def test_websocket_client_send_message(self, mock_send_request):
        """测试 WebSocket 客户端发送消息"""
        # 设置mock返回值
        mock_send_request.return_value = {"status": "ok", "data": {"message_id": 123}}
        
        # 创建客户端
        client = OneBotWebSocketClient(WS_URL, ACCESS_TOKEN)
        
        # 发送消息
        result = await client.send_message("group", GROUP_ID, "Hello world")
        
        # 验证请求格式
        expected_request = {
            "action": "send_msg",
            "params": {
                "message_type": "group",
                "group_id": GROUP_ID,
                "message": "Hello world",
                "auto_escape": False
            }
        }
        mock_send_request.assert_called_once()
        actual_request = mock_send_request.call_args[0][0]
        assert actual_request["action"] == expected_request["action"]
        assert actual_request["params"] == expected_request["params"]
        
        # 验证结果
        assert result["status"] == "ok"
        assert result["data"]["message_id"] == 123

    @pytest.mark.asyncio
    @patch('app.onebot.onebot.OneBotWebSocketManager.send_request')
    async def test_websocket_client_send_rich_message(self, mock_send_request):
        """测试 WebSocket 客户端发送富文本消息"""
        # 设置mock返回值
        mock_send_request.return_value = {"status": "ok", "data": {"message_id": 456}}
        
        # 创建客户端
        client = OneBotWebSocketClient(WS_URL, ACCESS_TOKEN)
        
        # 构建消息段
        message = [
            text("Hello "),
            text("World!")
        ]
        
        # 发送消息
        result = await client.send_message("private", USER_ID, message)
        
        # 验证请求格式
        expected_params = {
            "message_type": "private",
            "user_id": USER_ID,
            "message": message,
            "auto_escape": False
        }
        mock_send_request.assert_called_once()
        actual_request = mock_send_request.call_args[0][0]
        assert actual_request["params"] == expected_params
        
        # 验证结果
        assert result["status"] == "ok"
        assert result["data"]["message_id"] == 456

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_http_client_send_group_message(self, mock_post):
        """测试 HTTP 客户端发送群消息"""
        # 设置模拟响应
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"status": "ok", "data": {"message_id": 789}})
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # 创建客户端
        client = OneBotHTTPClient(HTTP_URL, ACCESS_TOKEN)
        
        # 发送消息
        result = await client.send_message("group", GROUP_ID, "Hello via HTTP")
        
        # 验证请求格式
        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        headers = mock_post.call_args[1]["headers"]
        json_data = mock_post.call_args[1]["json"]
        
        assert url == f"{HTTP_URL}/send_msg"
        assert headers["Authorization"] == f"Bearer {ACCESS_TOKEN}"
        assert headers["Content-Type"] == "application/json"
        assert json_data["message_type"] == "group"
        assert json_data["group_id"] == GROUP_ID
        assert json_data["message"] == "Hello via HTTP"
        
        # 验证结果
        assert result["status"] == "success"

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_http_client_send_private_message(self, mock_post):
        """测试 HTTP 客户端发送私聊消息"""
        # 设置模拟响应
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"status": "ok", "data": {"message_id": 456}})
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # 创建客户端
        client = OneBotHTTPClient(HTTP_URL, ACCESS_TOKEN)
        
        # 发送消息
        result = await client.send_message("private", USER_ID, "Hello via HTTP")
        
        # 验证请求格式
        mock_post.assert_called_once()
        json_data = mock_post.call_args[1]["json"]
        
        assert json_data["message_type"] == "private"
        assert json_data["user_id"] == USER_ID
        assert json_data["message"] == "Hello via HTTP"
        
        # 验证结果
        assert result["status"] == "success"


class TestMessageFormatting:
    """测试消息格式化"""
    
    def test_text_message(self):
        """测试文本消息格式化"""
        # 简单文本
        msg = text("Hello World")
        assert msg == {"type": "text", "data": {"text": "Hello World"}}
        
        # 空文本
        empty = text("")
        assert empty == {"type": "text", "data": {"text": ""}}


if __name__ == "__main__":
    pytest.main(["-xvs"])