## API 参考

### Webhook 接口

- **路径**: `/github-webhook`
- **方法**: POST
- **请求头**:
  - `Content-Type`: application/json
  - `X-GitHub-Event`: 事件类型
  - `X-Hub-Signature-256`: SHA-256 HMAC 签名

- **响应**:

  ```json
  {
    "status": "success|ignored",
    "message": "处理信息"
  }
  ```
