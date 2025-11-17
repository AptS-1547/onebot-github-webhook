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
数据模型模块

本模块定义应用使用的各类数据模型。

作者：AptS:1547
版本：0.2.0
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

from app.models.config import (
    Config,
    WebhookConfig,
    OnebotTarget,
    NamedTargetConfig,
    WebhookTargetConfig,
    get_settings
)
from app.models.message import MessageSegment, MessageBuilder
from app.models.webhook_event import (
    PushEventData,
    PullRequestEventData,
    IssueEventData,
    ReleaseEventData,
    IssueCommentEventData
)
from app.models.universal_message import (
    UniversalMessage,
    UniversalMessageSegment,
    MessageSegmentType,
    MessageBuilder as UniversalMessageBuilder
)

__all__ = [
    "Config",
    "WebhookConfig",
    "OnebotTarget",
    "NamedTargetConfig",
    "WebhookTargetConfig",
    "get_settings",
    "MessageSegment",
    "MessageBuilder",
    "PushEventData",
    "PullRequestEventData",
    "IssueEventData",
    "ReleaseEventData",
    "IssueCommentEventData",
    "UniversalMessage",
    "UniversalMessageSegment",
    "MessageSegmentType",
    "UniversalMessageBuilder"
]
