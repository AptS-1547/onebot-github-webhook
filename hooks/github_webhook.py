import hmac
import hashlib
import logging
from typing import Optional, Dict, Any, List

from fastapi import Request, HTTPException, Header

logger = logging.getLogger(__name__)

def match_repository(repo_name: str, pattern: str) -> bool:
    """
    检查仓库名是否匹配配置中的模式
    支持大小写不敏感匹配和通配符（用户名/*）形式
    
    Args:
        repo_name: 实际的仓库全名 (例如 'user/repo')
        pattern: 配置中的仓库模式 (例如 'user/repo' 或 'user/*')
    
    Returns:
        bool: 是否匹配
    """
    if not repo_name or not pattern:
        return False

    repo_name = repo_name.lower()
    pattern = pattern.lower()

    if pattern.endswith('/*'):
        user = pattern[:-2]
        return repo_name.startswith(f"{user}/")

    return repo_name == pattern

async def verify_signature(request: Request, webhooks: List, x_hub_signature_256: Optional[str] = Header(None)):
    """验证 GitHub webhook 签名"""

    try:
        body = await request.body()
        payload = await request.json()
        repo_name = payload.get("repository", {}).get("full_name")
    except Exception as e:
        logger.error("解析请求体失败: %s", str(e))
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from e

    webhook_secret = None
    for webhook in webhooks:
        if any(match_repository(repo_name, repo_pattern) for repo_pattern in webhook.REPO):
            webhook_secret = webhook.SECRET
            break

    if not webhook_secret:
        logger.warning("仓库 %s 未配置 webhook 密钥，跳过签名验证", repo_name)
        return True

    if not x_hub_signature_256:
        raise HTTPException(status_code=401, detail="Missing X-Hub-Signature-256 header")

    signature = hmac.new(
        key=webhook_secret.encode(),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()

    expected_signature = f"sha256={signature}"
    if not hmac.compare_digest(expected_signature, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

    return True

def find_matching_webhook(repo_name: str, branch: str, event_type: str, webhooks: List) -> Optional[Any]:
    """
    查找匹配的 webhook 配置
    
    Args:
        repo_name: 仓库名
        branch: 分支名
        event_type: 事件类型
        webhooks: webhook 配置列表
        
    Returns:
        匹配的 webhook 配置或 None
    """
    for webhook in webhooks:
        repo_matches = any(match_repository(repo_name, repo_pattern) for repo_pattern in webhook.REPO)

        if (repo_matches and
            branch in webhook.BRANCH and
            event_type in webhook.EVENTS):
            return webhook

    return None

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
