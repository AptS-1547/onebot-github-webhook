## GitHub Webhook 设置

1. 在 GitHub 仓库中前往 Settings -> Webhooks -> Add webhook
2. Payload URL 设置为 `http://你的服务器地址:8000/github-webhook`
3. Content type 选择 `application/json`
4. Secret 填写与配置文件中 `SECRET` 相同的值
5. 选择需要监听的事件（或选择 "Send me everything" 接收所有事件）
6. 启用 webhook（勾选 "Active"）
