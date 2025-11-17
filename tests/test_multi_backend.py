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
多 Backend 支持测试

测试 WebhookService 是否正确使用 BotClientManager 获取客户端

作者：AptS:1547
版本：0.2.0
日期：2025-11-18
本程序遵循 Apache License 2.0 许可证
"""

import asyncio
from typing import Union

import pytest

from app.models.config import Config, OnebotTarget, WebhookConfig
from app.services.webhook_service import WebhookService
from app.botclient.manager import BotClientManager
from app.botclient.base import BotClientInterface
from app.models.universal_message import UniversalMessage


class MockBotClient(BotClientInterface):
    """模拟 Bot 客户端，用于测试"""

    def __init__(self, name: str, client_type: str):
        """
        初始化模拟客户端。

        Args:
            name: 客户端名称
            client_type: 客户端类型
        """
        self._name = name
        self._client_type = client_type
        self.sent_messages = []

    @property
    def client_type(self) -> str:
        """客户端类型"""
        return self._client_type

    async def send_message(
        self,
        target_type: str,
        target_id: Union[int, str],
        message: Union[UniversalMessage, str]
    ) -> bool:
        """
        记录发送的消息（不真实发送）。

        Args:
            target_type: 目标类型
            target_id: 目标 ID
            message: 消息内容

        Returns:
            bool: 总是返回 True
        """
        self.sent_messages.append({
            "target_type": target_type,
            "target_id": target_id,
            "message": str(message)
        })
        print(f"[{self._name}] 发送消息到 {target_type} {target_id}")
        return True

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return True

    async def close(self) -> None:
        """关闭客户端"""
        print(f"[{self._name}] 客户端已关闭")


@pytest.mark.asyncio
async def test_webhook_service_with_manager():
    """测试 WebhookService 使用 BotClientManager 获取客户端"""

    print("=" * 60)
    print("测试 1: WebhookService 使用 BotClientManager")
    print("=" * 60)

    # 创建配置
    config = Config(
        bot_backends=[],
        targets=[],
        webhook_sources=[]
    )

    # 注册模拟客户端
    mock_client = MockBotClient("test-onebot", "onebot")
    await BotClientManager.register_client("onebot", mock_client)

    # 创建 WebhookService（使用新接口：接收 Config）
    service = WebhookService(config)

    # 创建模拟的 WebhookConfig（旧格式）
    webhook_config = WebhookConfig(
        NAME="test-webhook",
        REPO=["test/repo"],
        BRANCH=["main"],
        SECRET="",
        EVENTS=["push"],
        ONEBOT=[
            OnebotTarget(type="group", id=123456789)
        ]
    )

    # 模拟消息
    message = "测试消息"

    # 发送消息
    success = await service._send_to_targets(message, webhook_config)

    # 验证
    assert success, "消息发送应该成功"
    assert len(mock_client.sent_messages) == 1, "应该发送了 1 条消息"
    assert mock_client.sent_messages[0]["target_type"] == "group"
    assert mock_client.sent_messages[0]["target_id"] == 123456789

    print("✓ WebhookService 正确使用 BotClientManager 获取客户端")
    print("✓ 消息成功发送")

    # 清理
    await BotClientManager.close_all()


@pytest.mark.asyncio
async def test_multiple_targets():
    """测试发送到多个目标"""

    print("\n" + "=" * 60)
    print("测试 2: 发送到多个目标")
    print("=" * 60)

    # 创建配置
    config = Config(
        bot_backends=[],
        targets=[],
        webhook_sources=[]
    )

    # 注册模拟客户端
    mock_client = MockBotClient("multi-onebot", "onebot")
    await BotClientManager.register_client("onebot", mock_client)

    # 创建 WebhookService
    service = WebhookService(config)

    # 创建包含多个目标的 WebhookConfig
    webhook_config = WebhookConfig(
        NAME="multi-target",
        REPO=["test/repo"],
        BRANCH=["main"],
        SECRET="",
        EVENTS=["push"],
        ONEBOT=[
            OnebotTarget(type="group", id=111),
            OnebotTarget(type="group", id=222),
            OnebotTarget(type="private", id=333)
        ]
    )

    # 发送消息
    message = "多目标测试消息"
    success = await service._send_to_targets(message, webhook_config)

    # 验证
    assert success, "消息发送应该成功"
    assert len(mock_client.sent_messages) == 3, "应该发送了 3 条消息"

    # 验证每个目标
    assert mock_client.sent_messages[0]["target_id"] == 111
    assert mock_client.sent_messages[1]["target_id"] == 222
    assert mock_client.sent_messages[2]["target_id"] == 333
    assert mock_client.sent_messages[2]["target_type"] == "private"

    print("✓ 成功发送到 3 个目标")
    print("✓ 目标类型正确处理")

    # 清理
    await BotClientManager.close_all()


@pytest.mark.asyncio
async def test_client_not_found():
    """测试客户端不存在的情况"""

    print("\n" + "=" * 60)
    print("测试 3: 客户端不存在")
    print("=" * 60)

    # 确保 BotClientManager 为空
    BotClientManager.clear_registry()

    # 创建配置
    config = Config(
        bot_backends=[],
        targets=[],
        webhook_sources=[]
    )

    # 创建 WebhookService（客户端未注册）
    service = WebhookService(config)

    # 创建 WebhookConfig
    webhook_config = WebhookConfig(
        NAME="test",
        REPO=["test/repo"],
        BRANCH=["main"],
        SECRET="",
        EVENTS=["push"],
        ONEBOT=[OnebotTarget(type="group", id=123)]
    )

    # 尝试发送消息
    message = "测试消息"
    success = await service._send_to_targets(message, webhook_config)

    # 验证
    assert not success, "客户端不存在时应该返回 False"

    print("✓ 正确处理客户端不存在的情况")


async def main():
    """运行所有测试"""
    try:
        await test_webhook_service_with_manager()
        await test_multiple_targets()
        await test_client_not_found()

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
