import sys
import os
import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入 OneBotSender 类
from send_message import OneBotSender

@pytest.fixture
def onebot_config():
    """准备 OneBot 配置数据"""
    return {
        "url": "ws://localhost:8080/ws",
        "token": "test_token",
        "type": "ws"
    }

@pytest.fixture
def message_data():
    """准备消息数据"""
    return {
        "type": "group",
        "id": 123456789,
        "message": "Test message"
    }

@pytest.mark.asyncio
@patch('send_message.aiohttp.ClientSession')
@patch('send_message.logger')
async def test_websocket_send(mock_logger, mock_session, onebot_config, message_data):
    """测试通过 WebSocket 发送消息"""
    # 设置模拟对象
    mock_ws = AsyncMock()
    mock_session_instance = MagicMock()
    mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
    mock_session_instance.__aexit__ = AsyncMock(return_value=None)
    mock_session_instance.ws_connect = AsyncMock(return_value=mock_ws)
    mock_session.return_value = mock_session_instance
    
    # 创建 OneBotSender 实例
    sender = OneBotSender(onebot_config)
    
    # 调用发送方法
    await sender.send_to_onebot(message_data)
    
    # 验证调用
    mock_session_instance.ws_connect.assert_called_once_with(
        "ws://localhost:8080/ws",
        headers={"Authorization": "Bearer test_token"}
    )
    
    # 验证发送的消息格式
    sent_message = json.loads(mock_ws.send_str.call_args[0][0])
    assert sent_message["action"] == "send_group_msg"
    assert sent_message["params"]["group_id"] == 123456789
    assert sent_message["params"]["message"] == "Test message"

@pytest.mark.asyncio
@patch('send_message.aiohttp.ClientSession')
@patch('send_message.logger')
async def test_http_send(mock_logger, mock_session, onebot_config, message_data):
    """测试通过 HTTP 发送消息"""
    # 修改配置为 HTTP
    config = onebot_config.copy()
    config["type"] = "http"
    config["url"] = "http://localhost:8080/api"
    
    # 设置模拟对象
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"status": "ok"})
    
    mock_session_instance = MagicMock()
    mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
    mock_session_instance.__aexit__ = AsyncMock(return_value=None)
    mock_session_instance.post = AsyncMock(return_value=mock_response)
    mock_session.return_value = mock_session_instance
    
    # 创建 OneBotSender 实例
    sender = OneBotSender(config)
    
    # 调用发送方法
    await sender.send_to_onebot(message_data)
    
    # 验证调用
    mock_session_instance.post.assert_called_once()
    call_args = mock_session_instance.post.call_args
    assert call_args[0][0] == "http://localhost:8080/api/send_group_msg"
    
    # 验证请求头和数据
    headers = call_args[1]["headers"]
    assert headers["Authorization"] == "Bearer test_token"
    
    json_data = call_args[1]["json"]
    assert json_data["group_id"] == 123456789
    assert json_data["message"] == "Test message"

@pytest.mark.asyncio
@patch('send_message.aiohttp.ClientSession')
@patch('send_message.logger')
async def test_private_message_send(mock_logger, mock_session, onebot_config, message_data):
    """测试发送私聊消息"""
    # 修改消息类型为私聊
    private_message = message_data.copy()
    private_message["type"] = "private"
    
    # 设置模拟对象
    mock_ws = AsyncMock()
    mock_session_instance = MagicMock()
    mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
    mock_session_instance.__aexit__ = AsyncMock(return_value=None)
    mock_session_instance.ws_connect = AsyncMock(return_value=mock_ws)
    mock_session.return_value = mock_session_instance
    
    # 创建 OneBotSender 实例
    sender = OneBotSender(onebot_config)
    
    # 调用发送方法
    await sender.send_to_onebot(private_message)
    
    # 验证发送的消息格式
    sent_message = json.loads(mock_ws.send_str.call_args[0][0])
    assert sent_message["action"] == "send_private_msg"
    assert sent_message["params"]["user_id"] == 123456789
    assert sent_message["params"]["message"] == "Test message"

@pytest.mark.asyncio
@patch('send_message.aiohttp.ClientSession')
@patch('send_message.logger')
async def test_error_handling(mock_logger, mock_session, onebot_config, message_data):
    """测试错误处理"""
    # 模拟连接错误
    mock_session_instance = MagicMock()
    mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
    mock_session_instance.__aexit__ = AsyncMock(return_value=None)
    mock_session_instance.ws_connect = AsyncMock(side_effect=Exception("Connection error"))
    mock_session.return_value = mock_session_instance
    
    # 创建 OneBotSender 实例
    sender = OneBotSender(onebot_config)
    
    # 调用发送方法，应该捕获异常并记录
    await sender.send_to_onebot(message_data)
    
    # 验证错误被记录
    mock_logger.error.assert_called_once()