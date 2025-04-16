import logging
from fastapi import FastAPI, Request, HTTPException

from settings import Settings
from send_message import send_github_notification
from hooks.github_webhook import verify_signature, find_matching_webhook, extract_push_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

settings = Settings().from_yaml()

@app.post("/github-webhook")
async def github_webhook(request: Request):
    """处理 GitHub webhook 请求"""

    content_type = request.headers.get("Content-Type")
    if content_type != "application/json":
        logger.info("收到非 JSON 格式的请求，忽略")
        return {"status": "ignored", "message": "只处理 application/json 格式的请求"}

    event_type = request.headers.get("X-GitHub-Event", "")
    if not event_type:
        logger.info("缺少 X-GitHub-Event 头，忽略")
        return {"status": "ignored", "message": "缺少 X-GitHub-Event 头"}

    try:
        await verify_signature(
            request, 
            settings.GITHUB_WEBHOOK, 
            request.headers.get("X-Hub-Signature-256")
        )
    except HTTPException as e:
        logger.info(f"签名验证失败: {e.detail}")
        return {"status": "ignored", "message": f"签名验证失败: {e.detail}"}

    payload = await request.json()
    if not payload:
        logger.info("请求体为空，忽略")
        return {"status": "ignored", "message": "请求体为空"}

    repo_name = payload.get("repository", {}).get("full_name")
    branch = payload.get("ref", "").replace("refs/heads/", "")

    matched_webhook = find_matching_webhook(
        repo_name,
        branch,
        event_type,
        settings.GITHUB_WEBHOOK
    )

    if not matched_webhook:
        logger.info("找不到匹配的 webhook 配置: 仓库 %s, 分支 %s, 事件类型 %s", repo_name, branch, event_type)
        return {"status": "ignored", "message": "找不到匹配的 webhook 配置"}

    # 处理不同类型的事件，暂时只支持 push 事件
    if event_type == "push":
        push_data = extract_push_data(payload)

        logger.info("发现新的 push 事件，来自 %s 仓库", push_data["repo_name"])
        logger.info("分支: %s，推送者: %s，提交数量: %s",
                   push_data["branch"],
                   push_data["pusher"],
                   push_data["commit_count"])

        # 向配置的所有 OneBot 目标发送通知
        for target in matched_webhook.ONEBOT:
            logger.info("正在发送消息到 QQ %s %s", target.type, target.id)
            await send_github_notification(
                onebot_type=settings.ONEBOT_TYPE,
                onebot_url=settings.ONEBOT_URL,
                access_token=settings.ONEBOT_ACCESS_TOKEN,
                repo_name=push_data["repo_name"],
                branch=push_data["branch"],
                pusher=push_data["pusher"],
                commit_count=push_data["commit_count"],
                commits=push_data["commits"],
                onebot_send_type=target.type,
                onebot_id=target.id
            )

        return {"status": "success", "message": "处理 push 事件成功"}
    else:
        logger.info("收到 %s 事件，但尚未实现处理逻辑", event_type)
        return {"status": "ignored", "message": f"暂不处理 {event_type} 类型的事件"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
