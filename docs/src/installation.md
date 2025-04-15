
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

## 配置说明

配置文件 `config.yaml` 的结构如下：

```yaml
ENV: "production"  # 环境变量，可选值为 "production" 或 "development"
WS_URL: "ws://localhost:8080/ws"  # OneBot WebSocket 连接地址
WS_ACCESS_TOKEN: "your_token"  # OneBot 访问令牌

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
