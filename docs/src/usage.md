# 使用指南

## 运行服务

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

或者直接执行：

```bash
python app.py
```

## GitHub Webhook 设置

1. 在 GitHub 仓库中前往 Settings -> Webhooks -> Add webhook
2. Payload URL 设置为 `http://你的服务器地址:8000/github-webhook`
3. Content type 选择 `application/json`
4. Secret 填写与 `.env` 中 `GITHUB_WEBHOOK_SECRET` 相同的值
5. 选择 "Just the push event" 或根据需要选择事件
6. 启用 webhook（勾选 "Active"）
