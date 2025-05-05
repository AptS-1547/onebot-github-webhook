import json
import hmac
import hashlib
import sys
import os
import pytest

from unittest.mock import MagicMock, patch
from fastapi import HTTPException

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.github import verify_signature

class MockRequest:
    """模拟 FastAPI 请求对象"""

    def __init__(self, body_data):
        self.body_data = body_data

    async def body(self):
        return self.body_data

    async def json(self):
        return json.loads(self.body_data.decode('utf-8'))

@pytest.fixture
def webhook_test_data():
    """准备测试数据"""
    # 测试有效载荷
    payload = {
        "repository": {
            "full_name": "user/repo"
        },
        "ref": "refs/heads/main",
        "commits": []
    }
    payload_bytes = json.dumps(payload).encode('utf-8')

    # 测试 webhook 配置
    webhook_config = MagicMock()
    webhook_config.REPO = ["user/repo"]
    webhook_config.SECRET = "test_secret"

    # 计算有效签名
    valid_signature = "sha256=" + hmac.new(
        key=b"test_secret",
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()

    return {
        'payload': payload,
        'payload_bytes': payload_bytes,
        'webhook_config': webhook_config,
        'valid_signature': valid_signature
    }

@pytest.mark.asyncio
@patch('app.core.github.logger')  # 修正导入路径
async def test_valid_signature(mock_logger, webhook_test_data):
    """测试有效签名验证"""
    request = MockRequest(webhook_test_data['payload_bytes'])
    result = await verify_signature(
        request=request,
        webhooks=[webhook_test_data['webhook_config']],
        x_hub_signature_256=webhook_test_data['valid_signature']
    )
    assert result is True

@pytest.mark.asyncio
@patch('app.core.github.logger')  # 修正导入路径
async def test_invalid_signature(mock_logger, webhook_test_data):
    """测试无效签名验证"""
    request = MockRequest(webhook_test_data['payload_bytes'])
    invalid_signature = "sha256=invalid_hash_value"

    with pytest.raises(HTTPException) as excinfo:
        await verify_signature(
            request=request,
            webhooks=[webhook_test_data['webhook_config']],
            x_hub_signature_256=invalid_signature
        )

    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Invalid signature"

@pytest.mark.asyncio
@patch('app.core.github.logger')  # 修正导入路径
async def test_missing_signature(mock_logger, webhook_test_data):
    """测试缺失签名验证"""
    request = MockRequest(webhook_test_data['payload_bytes'])

    with pytest.raises(HTTPException) as excinfo:
        await verify_signature(
            request=request,
            webhooks=[webhook_test_data['webhook_config']],
            x_hub_signature_256=None
        )

    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Missing X-Hub-Signature-256 header"

@pytest.mark.asyncio
@patch('app.core.github.logger')  # 修正导入路径
async def test_no_matching_webhook(mock_logger, webhook_test_data):
    """测试找不到匹配的 webhook 配置"""
    # 使用不匹配的仓库名
    payload = {
        "repository": {
            "full_name": "another/repo"
        }
    }
    payload_bytes = json.dumps(payload).encode('utf-8')
    request = MockRequest(payload_bytes)

    # 应该返回 True 因为没有找到匹配的 webhook，所以跳过签名验证
    result = await verify_signature(
        request=request,
        webhooks=[webhook_test_data['webhook_config']],
        x_hub_signature_256=webhook_test_data['valid_signature']
    )

    assert result is True
    mock_logger.warning.assert_called_once()
