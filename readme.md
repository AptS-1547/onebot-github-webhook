<h1 align="center">
  OneBot GitHub Webhook
</h1>

<p align="center">
  一个用于接收 GitHub Webhook 并通过 OneBot 协议将推送通知转发到 QQ 群的服务。
</p>

<p align="center">
  <a href="https://www.codefactor.io/repository/github/AptS-1547/onebot-github-webhook/">
    <img src="https://www.codefactor.io/repository/github/AptS-1547/onebot-github-webhook/badge" alt="CodeFactor" />
  </a>

  <a href="https://github.com/AptS-1547/onebot-github-webhook/activity">
    <img src="https://img.shields.io/github/last-commit/AptS-1547/onebot-github-webhook/master" alt="Last Commit"/>
  </a>

  <a href="./LICENSE">
    <img src="https://img.shields.io/github/license/AptS-1547/onebot-github-webhook" alt="GPL-3.0\"/>
  </a>
</p>

## 功能特点

- 接收 GitHub 的 Webhook 推送事件
- 支持 Webhook 签名验证，确保请求安全
- 通过 OneBot 协议将推送信息转发到指定的 QQ 群
- 可配置监听的仓库和分支
- 格式化的推送通知消息，包含仓库、分支、推送者和最新提交信息

## 安装

1. 克隆本仓库：

```bash
git clone https://github.com/AptS-1547/onebot-github-webhook
cd onebot-github-webhook
```

2. 创建并激活虚拟环境：

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或者 .venv\Scripts\activate  # Windows
```

3. 安装依赖：

```bash
pip install -r requirements.txt
```

4. 修改配置文件

在程序第一次运行时会自动生成 `config.yaml` 文件，您可以根据需要修改其中的配置项。
或者复制 `config.yaml.example` 文件并重命名为 `config.yaml`，然后根据需要修改配置项。

```bash
cp config.yaml.example config.yaml
```

## 配置

在 `.env` 文件中设置以下环境变量：

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `WS_URL` | OneBot WebSocket 连接地址 | `ws://localhost:8080/ws` |
| `WS_ACCESS_TOKEN` | OneBot 访问令牌 | `your_token` |
| `GITHUB_WEBHOOK_SECRET` | GitHub Webhook 密钥 | `your_secret` |
| `GITHUB_REPO` | 监听的仓库列表 | `["username/repo"]` |
| `GITHUB_BRANCH` | 监听的分支列表 | `["main", "develop"]` |
| `QQ_GROUP` | 通知的 QQ 群号列表 | `[123456789]` |

## 运行

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

## 项目结构

- [app.py](app.py): 主应用入口和 Web 服务器
- [send_message.py](send_message.py): OneBot 消息发送客户端
- [settings.py](settings.py): 配置加载和验证
- [requirements.txt](requirements.txt): 项目依赖

## 依赖

- FastAPI: Web 框架
- Uvicorn: ASGI 服务器
- aiohttp: 异步 HTTP 客户端
- pydantic: 数据验证
