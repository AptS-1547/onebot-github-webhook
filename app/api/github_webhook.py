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
GitHub Webhook 路由模块

本模块处理 GitHub Webhook HTTP 请求。

作者：AptS:1547
版本：0.2.0
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

from typing import Dict, Any, Optional

from fastapi import APIRouter, Request, HTTPException, Header

from app.dependencies import ConfigDep, WebhookServiceDep
from app.core.github.webhook import GitHubWebhookHandler
from app.exceptions import (
    SignatureVerificationError,
    InvalidPayloadError,
    WebhookMatchError
)
from app.utils.logger import StructuredLogger

router = APIRouter()
logger = StructuredLogger(__name__)


@router.post("")
async def github_webhook(
    request: Request,
    config: ConfigDep,
    webhook_service: WebhookServiceDep,
    x_github_event: Optional[str] = Header(None, alias="X-GitHub-Event"),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    content_type: Optional[str] = Header(None, alias="Content-Type")
) -> Dict[str, Any]:
    """
    处理 GitHub Webhook 请求。

    Args:
        request: FastAPI Request 对象
        config: 应用配置（通过依赖注入）
        webhook_service: Webhook 服务（通过依赖注入）
        x_github_event: GitHub 事件类型头部
        x_hub_signature_256: GitHub 签名头部
        content_type: 内容类型头部

    Returns:
        Dict[str, Any]: 响应数据

    Raises:
        HTTPException: 处理失败时
    """
    # 记录请求来源
    client_ip = request.client.host if request.client else "未知"

    # 检查 Content-Type
    if content_type != "application/json":
        logger.info("收到非 JSON 格式的请求: %s, 来源: %s", content_type, client_ip)
        return {
            "status": "ignored",
            "message": "只处理 application/json 格式的请求"
        }

    # 检查事件类型头部
    if not x_github_event:
        logger.info("缺少 X-GitHub-Event 头，来源: %s", client_ip)
        return {"status": "ignored", "message": "缺少 X-GitHub-Event 头"}

    event_type = x_github_event

    # 解析 JSON payload
    try:
        payload = await request.json()
        if not payload:
            logger.info("请求体为空，来源: %s", client_ip)
            return {"status": "ignored", "message": "请求体为空"}

        # 验证 payload 格式
        payload = GitHubWebhookHandler.validate_payload(payload)

    except Exception as e:
        logger.error("解析请求体失败: %s, 来源: %s", e, client_ip)
        raise HTTPException(
            status_code=400,
            detail=f"无效的 JSON payload: {e}"
        ) from e

    repo_name = payload.get("repository", {}).get("full_name", "")

    # 记录收到的 webhook
    logger.log_webhook_received(event_type, repo_name, client_ip)

    # 查找对应的密钥并验证签名
    secret = GitHubWebhookHandler.find_secret_for_repo(
        repo_name,
        config.GITHUB_WEBHOOK
    )

    if secret:
        try:
            GitHubWebhookHandler.verify_signature(
                payload,
                x_hub_signature_256 or "",
                secret
            )
        except SignatureVerificationError as e:
            logger.log_signature_verification(False, repo_name, str(e))
            # 签名验证失败必须返回 401
            raise HTTPException(
                status_code=401,
                detail=e.message
            ) from e
    else:
        logger.warning("仓库 %s 未配置密钥，跳过签名验证", repo_name)

    # 提取分支信息
    branch = GitHubWebhookHandler.extract_branch_from_payload(
        payload,
        event_type
    )

    # 查找匹配的 webhook 配置
    matched_webhook = GitHubWebhookHandler.find_matching_webhook(
        repo_name,
        branch,
        event_type,
        config.GITHUB_WEBHOOK
    )

    if not matched_webhook:
        logger.log_webhook_not_matched(repo_name, branch, event_type)
        return {
            "status": "ignored",
            "message": "找不到匹配的 webhook 配置"
        }

    logger.log_webhook_matched(
        matched_webhook.NAME,
        repo_name,
        branch,
        event_type
    )

    # 根据事件类型处理
    success = False

    try:
        if event_type == "push":
            success = await webhook_service.process_push_event(
                payload,
                matched_webhook
            )

        elif event_type == "pull_request":
            success = await webhook_service.process_pull_request_event(
                payload,
                matched_webhook
            )

        elif event_type == "issues":
            success = await webhook_service.process_issue_event(
                payload,
                matched_webhook
            )

        elif event_type == "release":
            success = await webhook_service.process_release_event(
                payload,
                matched_webhook
            )

        elif event_type == "issue_comment":
            success = await webhook_service.process_issue_comment_event(
                payload,
                matched_webhook
            )

        else:
            logger.info("收到 %s 事件，但尚未实现处理逻辑", event_type)
            return {
                "status": "ignored",
                "message": f"暂不处理 {event_type} 类型的事件"
            }

    except Exception as e:
        logger.error("处理事件时发生错误: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"处理事件失败: {e}"
        ) from e

    if success:
        return {"status": "success", "message": f"处理 {event_type} 事件成功"}

    return {"status": "failed", "message": "处理事件时发生错误"}
