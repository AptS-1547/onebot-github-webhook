import hmac
import hashlib
import logging

from fastapi import FastAPI, Request, HTTPException, Header, Depends

from settings import Settings
from send_message import send_github_notification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

settings = Settings().from_yaml()

# 全局变量
WS_URL = settings.WS_URL
WS_ACCESS_TOKEN = settings.WS_ACCESS_TOKEN
GITHUB_WEBHOOK_SECRET = settings.GITHUB_WEBHOOK_SECRET
GITHUB_REPO = settings.GITHUB_REPO
GITHUB_BRANCH = settings.GITHUB_BRANCH
QQ_GROUP = settings.QQ_GROUP

async def verify_signature(request: Request, x_hub_signature_256: str = Header(None)):
    """验证 GitHub webhook 签名"""
    if not GITHUB_WEBHOOK_SECRET:
        return True

    if not x_hub_signature_256:
        raise HTTPException(status_code=401, detail="Missing X-Hub-Signature-256 header")

    body = await request.body()

    signature = hmac.new(
        key = str(GITHUB_WEBHOOK_SECRET).encode(),
        msg = body,
        digestmod = hashlib.sha256
    ).hexdigest()

    expected_signature = f"sha256={signature}"
    if not hmac.compare_digest(expected_signature, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

    return True

@app.post("/github-webhook")
async def github_webhook(request: Request, _: bool = Depends(verify_signature)):
    """
    处理 GitHub webhook 请求
    """

    content_type = request.headers.get("Content-Type")

    if content_type != "application/json":
        logger.info("收到非 JSON 格式的请求，忽略")
        return {"status": "ignored", "message": "只处理 application/json 格式的请求"}

    event_type = request.headers.get("X-GitHub-Event")

    payload = await request.json()

    if event_type == "push":
        # 提取有用的信息
        repo_name = payload.get("repository", {}).get("full_name")
        branch = payload.get("ref", "").replace("refs/heads/", "")
        pusher = payload.get("pusher", {}).get("name")
        commits = payload.get("commits", [])
        commit_count = len(commits)

        if repo_name not in GITHUB_REPO:
            logger.info("仓库 %s 不在允许的列表中，忽略", repo_name)
            return {"status": "ignored", "message": f"仓库 {repo_name} 不在允许的列表中"}

        if branch not in GITHUB_BRANCH:
            logger.info("分支 %s 不在允许的列表中，忽略", branch)
            return {"status": "ignored", "message": f"分支 {branch} 不在允许的列表中"}

        logger.info("发现新的 push 事件，来自 %s 仓库", repo_name)
        logger.info("分支: %s， 推送者: %s， 提交数量: %d", branch, pusher, commit_count)

        for QQ_GROUP_ID in QQ_GROUP:
            logger.info("正在发送消息到 QQ 群 %s", QQ_GROUP_ID)

            await send_github_notification(
                ws_url=WS_URL,
                access_token=WS_ACCESS_TOKEN,
                group_id=QQ_GROUP_ID,
                repo_name=repo_name,
                branch=branch,
                pusher=pusher,
                commit_count=commit_count,
                commits=commits
            )

        # 这里可以添加你的业务逻辑，比如触发部署、发送通知等

        return {"status": "success", "message": "处理 push 事件成功"}
    else:
        logger.info("收到 %s 事件，忽略", event_type)
        return {"status": "ignored", "message": f"不处理 {event_type} 类型的事件"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
