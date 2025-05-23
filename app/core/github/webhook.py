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
本模块用于处理 GitHub Webhook 事件，包括验证签名、查找匹配的 webhook 配置和提取 push 事件数据。
作者：AptS:1547
版本：0.1.0-alpha
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

import hmac
import hashlib
import logging
from typing import Optional, Dict, Any, List

from fastapi import Request, HTTPException, Header

from app.utils.matching import match_pattern

logger = logging.getLogger(__name__)

class GitHubWebhookHandler:
    """
    GitHub Webhook 处理类
    用于处理 GitHub Webhook 事件，包括验证签名、查找匹配的 webhook 配置和提取 push 事件数据。
    """

    @staticmethod
    async def verify_signature(
            request: Request,
            webhooks: List,
            x_hub_signature_256: Optional[str] = Header(None)
            ) -> bool:
        """验证 GitHub webhook 签名"""

        try:
            body = await request.body()
            payload = await request.json()
            repo_name = payload.get("repository", {}).get("full_name")
        except Exception as e:
            logger.error("解析请求体失败: %s", str(e))
            raise HTTPException(
                status_code=400, detail="Invalid JSON payload") from e

        webhook_secret = None
        for webhook in webhooks:
            if any(match_pattern(repo_name, repo_pattern) for repo_pattern in webhook.REPO):
                webhook_secret = webhook.SECRET
                break

        if not webhook_secret:
            logger.warning("仓库 %s 未配置 webhook 密钥，跳过签名验证", repo_name)
            return True

        if not x_hub_signature_256:
            raise HTTPException(
                status_code=401, detail="Missing X-Hub-Signature-256 header")

        signature = hmac.new(
            key=webhook_secret.encode(),
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()

        expected_signature = f"sha256={signature}"
        if not hmac.compare_digest(expected_signature, x_hub_signature_256):
            raise HTTPException(status_code=401, detail="Invalid signature")

        return True

    @staticmethod
    def find_matching_webhook(
            repo_name: str,
            branch: str,
            event_type: str,
            webhooks: List
            ) -> Optional[Any]:
        """
        查找匹配的 webhook 配置

        Args:
            repo_name: 仓库名
            branch: 分支名 (可能为空，对于非push事件)
            event_type: 事件类型
            webhooks: webhook 配置列表

        Returns:
            匹配的 webhook 配置或 None
        """
        logger.debug("尝试匹配 webhook: 仓库=%s, 分支=%s, 事件类型=%s", repo_name, branch, event_type)

        for webhook in webhooks:
            repo_matches = any(match_pattern(repo_name, repo_pattern)
                            for repo_pattern in webhook.REPO)
            if not repo_matches:
                continue

            if event_type not in webhook.EVENTS:
                continue

            if event_type in ["push", "pull_request"]:
                branch_matches = any(match_pattern(branch, branch_pattern)
                                    for branch_pattern in webhook.BRANCH)
                if not branch_matches:
                    continue
            else:
                if getattr(webhook, "BRANCH_CHECK_ALL", False) and branch:
                    branch_matches = any(match_pattern(branch, branch_pattern)
                                        for branch_pattern in webhook.BRANCH)
                    if not branch_matches:
                        continue

            logger.debug("找到匹配的webhook配置: %s", webhook)
            return webhook

        logger.debug("未找到匹配的webhook配置")
        return None

    @staticmethod
    def extract_push_data(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        从 push 事件中提取相关数据

        Args:
            payload: GitHub webhook 负载

        Returns:
            包含提取数据的字典
        """
        return {
            "repo_name": payload.get("repository", {}).get("full_name"),
            "branch": payload.get("ref", "").replace("refs/heads/", ""),
            "pusher": payload.get("pusher", {}).get("name"),
            "commits": payload.get("commits", []),
            "commit_count": len(payload.get("commits", []))
        }

    @staticmethod
    def extract_pull_request_data(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        从 pull request 事件中提取相关数据

        Args:
            payload: GitHub webhook 负载

        Returns:
            包含提取数据的字典
        """
        return {
            "repo_name": payload.get("repository", {}).get("full_name"),
            "pull_request_number": payload.get("number"),
            "action": payload.get("action"),
            "pull_request": payload.get("pull_request", {}),
            "user": payload.get("sender", {}).get("login")
        }

    @staticmethod
    def extract_issue_data(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        从 issue 事件中提取相关数据

        Args:
            payload: GitHub webhook 负载

        Returns:
            包含提取数据的字典
        """
        return {
            "repo_name": payload.get("repository", {}).get("full_name"),
            "issue_number": payload.get("issue", {}).get("number"),
            "action": payload.get("action"),
            "issue": payload.get("issue", {}),
            "user": payload.get("sender", {}).get("login")
        }

    @staticmethod
    def extract_release_data(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        从 release 事件中提取相关数据

        Args:
            payload: GitHub webhook 负载

        Returns:
            包含提取数据的字典
        """
        return {
            "repo_name": payload.get("repository", {}).get("full_name"),
            "release_tag": payload.get("release", {}).get("tag_name"),
            "action": payload.get("action"),
            "release": payload.get("release", {}),
            "user": payload.get("sender", {}).get("login")
        }

    @staticmethod
    def extract_issue_comment_data(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        从 issue comment 事件中提取相关数据

        Args:
            payload: GitHub webhook 负载

        Returns:
            包含提取数据的字典
        """
        return {
            "repo_name": payload.get("repository", {}).get("full_name"),
            "issue_number": payload.get("issue", {}).get("number"),
            "action": payload.get("action"),
            "comment": payload.get("comment", {}),
            "user": payload.get("sender", {}).get("login")
        }
