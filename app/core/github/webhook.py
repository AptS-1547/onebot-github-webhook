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
GitHub Webhook 处理模块

本模块用于处理 GitHub Webhook 事件，包括验证签名和查找匹配的配置。

作者：AptS:1547
版本：0.2.0
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

import hmac
import hashlib
import json
from typing import Optional, List, Dict, Any

from app.utils.matching import match_pattern
from app.models.config import WebhookConfig
from app.exceptions import SignatureVerificationError, InvalidPayloadError
from app.utils.logger import StructuredLogger

logger = StructuredLogger(__name__)


class GitHubWebhookHandler:
    """
    GitHub Webhook 处理类。

    提供签名验证和配置匹配功能。
    """

    @staticmethod
    def verify_signature(
        payload: Dict[str, Any],
        signature: str,
        secret: str
    ) -> None:
        """
        验证 GitHub Webhook 签名。

        Args:
            payload: 已解析的 JSON payload
            signature: X-Hub-Signature-256 头部值
            secret: Webhook 密钥

        Raises:
            SignatureVerificationError: 签名验证失败
        """
        if not signature:
            raise SignatureVerificationError(
                "缺少 X-Hub-Signature-256 头部",
                details={"reason": "missing_header"}
            )

        # 将 payload 重新序列化为 JSON 字符串（用于签名验证）
        # GitHub 使用紧凑的 JSON 格式（无空格）
        body = json.dumps(payload, separators=(',', ':')).encode('utf-8')

        # 计算 HMAC-SHA256 签名
        expected_signature = hmac.new(
            key=secret.encode('utf-8'),
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()

        expected_signature_header = f"sha256={expected_signature}"

        # 使用恒定时间比较避免时序攻击
        if not hmac.compare_digest(expected_signature_header, signature):
            raise SignatureVerificationError(
                "签名验证失败",
                details={"reason": "signature_mismatch"}
            )

        logger.log_signature_verification(True)

    @staticmethod
    def find_matching_webhook(
        repo_name: str,
        branch: str,
        event_type: str,
        webhooks: List[WebhookConfig]
    ) -> Optional[WebhookConfig]:
        """
        查找匹配的 webhook 配置。

        Args:
            repo_name: 仓库全名（如 "user/repo"）
            branch: 分支名（可能为空，对于非 push 事件）
            event_type: 事件类型（如 "push", "pull_request"）
            webhooks: webhook 配置列表

        Returns:
            Optional[WebhookConfig]: 匹配的配置，如果没有匹配则返回 None
        """
        logger.debug(
            "尝试匹配 webhook: 仓库=%s, 分支=%s, 事件类型=%s",
            repo_name,
            branch,
            event_type
        )

        for webhook in webhooks:
            # 检查仓库是否匹配
            repo_matches = any(
                match_pattern(repo_name, repo_pattern)
                for repo_pattern in webhook.REPO
            )
            if not repo_matches:
                continue

            # 检查事件类型是否匹配
            if event_type not in webhook.EVENTS:
                continue

            # 对于 push 和 pull_request 事件，需要检查分支
            if event_type in ["push", "pull_request"]:
                if not branch:
                    # 如果没有分支信息，跳过分支检查
                    logger.debug("找到匹配的 webhook 配置: %s", webhook.NAME)
                    return webhook

                branch_matches = any(
                    match_pattern(branch, branch_pattern)
                    for branch_pattern in webhook.BRANCH
                )
                if not branch_matches:
                    continue

            # 对于其他事件，可选地检查分支（如果配置了 BRANCH_CHECK_ALL）
            else:
                if hasattr(webhook, "BRANCH_CHECK_ALL") and webhook.BRANCH_CHECK_ALL:
                    if branch:
                        branch_matches = any(
                            match_pattern(branch, branch_pattern)
                            for branch_pattern in webhook.BRANCH
                        )
                        if not branch_matches:
                            continue

            logger.debug("找到匹配的 webhook 配置: %s", webhook.NAME)
            return webhook

        logger.debug("未找到匹配的 webhook 配置")
        return None

    @staticmethod
    def find_secret_for_repo(
        repo_name: str,
        webhooks: List[WebhookConfig]
    ) -> Optional[str]:
        """
        查找仓库对应的 Webhook 密钥。

        Args:
            repo_name: 仓库全名
            webhooks: webhook 配置列表

        Returns:
            Optional[str]: 密钥，如果没有找到则返回 None
        """
        for webhook in webhooks:
            if any(match_pattern(repo_name, repo_pattern) for repo_pattern in webhook.REPO):
                return webhook.SECRET

        return None

    @staticmethod
    def extract_branch_from_payload(
        payload: Dict[str, Any],
        event_type: str
    ) -> str:
        """
        从 payload 中提取分支名。

        Args:
            payload: GitHub Webhook payload
            event_type: 事件类型

        Returns:
            str: 分支名，如果无法提取则返回空字符串
        """
        if event_type == "push":
            ref = payload.get("ref", "")
            return ref.replace("refs/heads/", "") if ref else ""

        if event_type == "pull_request":
            pr = payload.get("pull_request", {})
            base = pr.get("base", {})
            return base.get("ref", "")

        return ""

    @staticmethod
    def validate_payload(payload: Any) -> Dict[str, Any]:
        """
        验证 payload 格式是否正确。

        Args:
            payload: 待验证的 payload

        Returns:
            Dict[str, Any]: 验证通过的 payload

        Raises:
            InvalidPayloadError: payload 格式不正确
        """
        if not isinstance(payload, dict):
            raise InvalidPayloadError(
                "Payload 必须是 JSON 对象",
                details={"type": type(payload).__name__}
            )

        # 检查必要字段
        if "repository" not in payload:
            raise InvalidPayloadError(
                "Payload 缺少 repository 字段",
                details={"payload_keys": list(payload.keys())}
            )

        repo = payload.get("repository", {})
        if not isinstance(repo, dict) or "full_name" not in repo:
            raise InvalidPayloadError(
                "repository 字段格式不正确",
                details={"repository": repo}
            )

        return payload
