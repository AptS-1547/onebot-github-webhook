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

### 现有功能

- **Webhook 事件接收**：接收并处理 GitHub 的 Webhook 推送事件
- **安全验证**：支持 Webhook 签名验证，确保请求安全性
- **OneBot 协议支持**：通过 OneBot 协议将推送信息转发到指定的 QQ 群或私聊
- **灵活配置**：可配置监听的仓库、分支和事件类型
- **高级仓库匹配**：
  - 支持大小写不敏感的仓库名匹配
  - 支持 `用户名/*` 通配符匹配用户的所有仓库
- **格式化消息**：结构化的推送通知，包含仓库、分支、推送者和最新提交信息

### 计划实现功能

- **GitHub API 轮询**：
  - 为无法设置 Webhook 的场景提供定时轮询机制
  - 支持自定义轮询间隔
  - 检测提交、PR、Issue 等变化
  
- **自定义模板系统**：
  - 支持用户自定义消息格式
  - Jinja2 模板语法
  - 支持不同事件类型的独立模板
  - 多种消息格式（纯文本、Markdown、JSON 等）

- **更多事件支持**：
  - Issues 事件（创建、关闭、重新打开）
  - Pull Request 事件（创建、合并、评论）
  - Release 事件（发布、预发布）
  - Discussion 事件

- **统计与监控**：
  - 处理事件统计
  - 服务健康检查
  - Prometheus 指标导出

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

4. 配置文件设置：

在程序第一次运行时会自动生成 config.yaml 文件，您可以根据需要修改其中的配置项。  
或者复制示例配置文件：

```bash
cp config.yaml.example config.yaml
```

## 配置说明

配置文件 config.yaml 的结构如下：

```yaml
ENV: "production"  # 环境变量，可选值为 "production" 或 "development"
ONEBOT_URL: "ws://localhost:8080/ws"  # OneBot 连接地址
ONEBOT_TYPE: "ws"  # OneBot 连接类型，可选值为 "ws" 或 "http"
ONEBOT_ACCESS_TOKEN: "your_token"  # OneBot 访问令牌

GITHUB_WEBHOOK:
  - NAME: "github"  # webhook 名称
    REPO:  # 监听的仓库列表，支持用户名/* 匹配用户所有仓库
      - "username/repo"
      - "username/*"
    BRANCH:  # 监听的分支列表
      - "main"
      - "develop"
    SECRET: "your_secret"  # GitHub Webhook 密钥
    EVENTS:  # 监听的事件类型
      - "push"
      - "pull_request"
      - "issues"
      - "issue_comment"
      - "release"
    ONEBOT:  # 通知的 OneBot 目标列表
      - type: "group"  # 目标类型，可选值为 "group" 或 "private"
        id: 123456789  # 目标 ID，群号或用户 ID
```

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
4. Secret 填写与配置文件中 `SECRET` 相同的值
5. 选择需要监听的事件（或选择 "Send me everything" 接收所有事件）
6. 启用 webhook（勾选 "Active"）

## 开发路线图

### 1. GitHub API 轮询（计划中）

对于无法使用 webhook 的场景（如私有仓库或受限环境），我们计划实现基于 GitHub API 的轮询机制。

#### 设计概要

- **配置方式**：

```yaml
GITHUB_API_POLLING:
  - NAME: "polling-example"
    REPO:
      - "username/repo"
    BRANCH:
      - "main"
    INTERVAL: 300  # 轮询间隔（秒）
    EVENTS:
      - "push"
      - "pull_request"
    TOKEN: "github_personal_access_token"  # GitHub 个人访问令牌
    ONEBOT:
      - type: "group"
        id: 123456789
```

- **功能**：
  - 定时检查仓库变更
  - 对比上次轮询结果，只通知新变更
  - 支持提交、PR、Issue 等多种数据类型轮询
  - 优化请求频率，避免触发 GitHub API 限流

- **实现计划**：
  - 使用 `APScheduler` 实现定时任务
  - 使用 `aiohttp` 实现异步 HTTP 请求
  - 使用本地文件存储上次轮询状态 ~~（轻量化的玩意不可能给你上数据库 or Redis）~~
  - 封装 GitHub API 客户端，处理认证和错误

### 2. 自定义模板系统（计划中）

允许用户自定义各类事件的通知消息格式，提供更灵活的展示方式。

#### 设计概要

- **模板存储**：
  - 模板文件存储在 `templates/` 目录下
  - 按照事件类型命名，如 `templates/push.txt`、`templates/issues.txt` 等
  - 也可以创建自定义命名的模板文件用于不同场景

- **配置方式**：

  ```yaml
  GITHUB_WEBHOOK:
    - NAME: "github"
      REPO:
        - "username/repo"
      BRANCH:
        - "main"
      SECRET: "your_secret"
      EVENTS:
        - "push"
        - "issues"
      TEMPLATES:  # 为不同事件类型指定自定义模板
        push: "custom_push.txt"  # 使用自定义推送模板
        issues: "default"  # 使用默认 issues 模板
      ONEBOT:
        - type: "group"
          id: 123456789
  ```

- **模板示例** (`templates/push.txt`):

  ```
  📢 GitHub 推送通知
  仓库：{{ repo_name }}
  分支：{{ branch }}
  推送者：{{ pusher }}
  提交数量：{{ commit_count }}
  {% for commit in commits %}
  [{{ loop.index }}] {{ commit.id[:7] }} by {{ commit.author.name }}
      {{ commit.message.split('\n')[0] }}
  {% endfor %}
  ```

- **模板示例** (`templates/issues.txt`):

  ```
  📋 Issue {{ action }}
  仓库：{{ repo_name }}
  标题：{{ issue.title }}
  作者：{{ issue.user.login }}
  链接：{{ issue.html_url }}
  ```

- **功能**：
  - 基于 Jinja2 模板引擎
  - 支持条件语句和循环
  - 每个 Webhook 可以指定不同的模板集合
  - 提供默认模板，无需配置即可使用
  - 模板变量自动文档化（将提供变量参考）

- **实现计划**：
  - 引入 Jinja2 依赖
  - 实现模板目录扫描和加载机制
  - 开发模板缓存以提高性能
  - 提供模板变量参考文档
  - 添加模板验证功能，避免语法错误

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

## 项目结构

- app.py: 主应用入口和 Web 服务器
- github_webhook.py: GitHub Webhook 处理逻辑
- send_message.py: OneBot 消息发送客户端
- settings.py: 配置加载和验证
- requirements.txt: 项目依赖

## 部署建议

### Docker 部署（计划支持）

```bash
docker run -d \
  --name onebot-github-webhook \
  -p 8000:8000 \
  -v $(pwd)/config.yaml:/app/config.yaml \
  e1saps/onebot-github-webhook:latest
```

### Systemd 服务

创建 `/etc/systemd/system/onebot-github-webhook.service`:

```ini
[Unit]
Description=OneBot GitHub Webhook Service
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/onebot-github-webhook
ExecStart=/opt/onebot-github-webhook/.venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

启用服务:

```bash
sudo systemctl enable onebot-github-webhook
sudo systemctl start onebot-github-webhook
```

## 常见问题

**Q: Webhook 触发但 QQ 未收到消息怎么办？**

A: 请检查以下几点：

1. OneBot 地址和 token 是否正确
2. OneBot 实现是否支持 WebSocket/HTTP 连接
3. QQ 机器人是否在目标群/好友中
4. 查看日志获取详细错误信息

**Q: 如何支持多个 QQ 机器人？**

A: 本程序暂时不支持推送到多个 QQ 机器人

## 贡献指南

欢迎提交 Pull Request 或 Issue 来帮助改进本项目！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 GPL-3.0 许可证。
