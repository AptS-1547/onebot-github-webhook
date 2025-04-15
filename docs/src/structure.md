## 项目结构

- [app.py](app.py): 主应用入口和 Web 服务器
- [hooks/github_webhook.py](hooks/github_webhook.py): GitHub Webhook 处理逻辑
- [send_message.py](send_message.py): OneBot 消息发送客户端
- [settings.py](settings.py): 配置加载和验证
- [requirements.txt](requirements.txt): 项目依赖

## 依赖

- FastAPI: Web 框架
- Uvicorn: ASGI 服务器
- aiohttp: 异步 HTTP 客户端
- pydantic: 数据验证
- PyYAML: YAML 配置文件解析
