import hmac
import hashlib
import logging
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Header

from settings import Settings
from send_message import send_github_notification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

settings = Settings().from_yaml()

# 全局变量
WS_URL = settings.WS_URL
WS_ACCESS_TOKEN = settings.WS_ACCESS_TOKEN
GITHUB_WEBHOOK = settings.GITHUB_WEBHOOK

async def verify_signature(request: Request, x_hub_signature_256: Optional[str] = Header(None)):
    """验证 GitHub webhook 签名"""

    try:
        body = await request.body()
        payload = await request.json()
        repo_name = payload.get("repository", {}).get("full_name")
    except Exception as e:
        logger.error("解析请求体失败: %s", str(e))
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from e

    webhook_secret = None
    for webhook in settings.GITHUB_WEBHOOK:
        if repo_name in webhook.REPO:
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

@app.post("/github-webhook")
async def github_webhook(request: Request):
    """处理 GitHub webhook 请求"""

    content_type = request.headers.get("Content-Type")
    if content_type != "application/json":
        logger.info("收到非 JSON 格式的请求，忽略")
        return {"status": "ignored", "message": "只处理 application/json 格式的请求"}

    event_type = request.headers.get("X-GitHub-Event")

    try:
        await verify_signature(request, request.headers.get("X-Hub-Signature-256"))
    except HTTPException:
        logger.info("签名验证失败")
        return {"status": "ignored", "message": "签名验证失败"}

    payload = await request.json()
    if not payload:
        logger.info("请求体为空，忽略")
        return {"status": "ignored", "message": "请求体为空"}

    repo_name = payload.get("repository", {}).get("full_name")
    branch = payload.get("ref", "").replace("refs/heads/", "")

    matched_webhook = None
    for webhook in settings.GITHUB_WEBHOOK:
        if (repo_name in webhook.REPO and 
            branch in webhook.BRANCH and 
            event_type in webhook.EVENTS):
            matched_webhook = webhook
            break

    if not matched_webhook:
        logger.info("找不到匹配的 webhook 配置: 仓库=%s, 分支=%s, 事件类型=%s", repo_name, branch, event_type)
        return {"status": "ignored", "message": "找不到匹配的 webhook 配置"}

    # 处理不同类型的事件，暂时只支持 push 事件
    if event_type == "push":
        pusher = payload.get("pusher", {}).get("name")
        commits = payload.get("commits", [])
        commit_count = len(commits)

        logger.info("发现新的 push 事件，来自 %s 仓库", repo_name)
        logger.info("分支: %s，推送者: %s，提交数量: %s", branch, pusher, commit_count)

        # 向配置的所有 OneBot 目标发送通知
        for target in matched_webhook.ONEBOT:
            if target.type == "group":
                logger.info("正在发送消息到 QQ 群 %s", target.id)
                await send_github_notification(
                    ws_url=settings.WS_URL,
                    access_token=settings.WS_ACCESS_TOKEN,
                    group_id=target.id,
                    repo_name=repo_name,
                    branch=branch,
                    pusher=pusher,
                    commit_count=commit_count,
                    commits=commits
                )
            elif target.type == "private":
                logger.info("正在发送消息到 QQ 用户 %s", target.id)
                # TODO: 处理私聊消息

        return {"status": "success", "message": "处理 push 事件成功"}
    else:
        logger.info("收到 %s 事件，但尚未实现处理逻辑", event_type)
        return {"status": "ignored", "message": f"暂不处理 {event_type} 类型的事件"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
