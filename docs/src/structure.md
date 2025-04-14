# 项目结构

- [app.py](https://github.com/AptS-1547/onebot-github-webhook/blob/master/app.py): 主应用入口和 Web 服务器
- [send_message.py](https://github.com/AptS-1547/onebot-github-webhook/blob/master/send_message.py): OneBot 消息发送客户端
- [settings.py](https://github.com/AptS-1547/onebot-github-webhook/blob/master/settings.py): 配置加载和验证
- [requirements.txt](https://github.com/AptS-1547/onebot-github-webhook/blob/master/requirements.txt): 项目依赖

## 依赖

- FastAPI: Web 框架
- Uvicorn: ASGI 服务器
- aiohttp: 异步 HTTP 客户端
- pydantic: 数据验证
