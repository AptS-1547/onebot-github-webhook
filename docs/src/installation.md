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
# 或者使用 Poetry
# poetry install
```

4. 配置文件设置：

在程序第一次运行时会自动生成 config.yaml 文件，您可以根据需要修改其中的配置项。  
或者复制示例配置文件：

```bash
cp config/config.example.yaml config.yaml
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
    REPO:  # 监听的仓库列表，支持通配符匹配
      - "username/repo"
      - "username/*"
      - "*/*-api"
    BRANCH:  # 监听的分支列表，支持通配符匹配
      - "main"
      - "develop"
      - "feature/*"
      - "release-*"
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
uvicorn main:app --host 0.0.0.0 --port 8000
```

或者直接执行：

```bash
python main.py
```

## GitHub Webhook 设置

1. 在 GitHub 仓库中前往 Settings -> Webhooks -> Add webhook
2. Payload URL 设置为 `http://你的服务器地址:8000/github-webhook`
3. Content type 选择 `application/json`
4. Secret 填写与配置文件中 `SECRET` 相同的值
5. 选择需要监听的事件（或选择 "Send me everything" 接收所有事件）
6. 启用 webhook（勾选 "Active"）
