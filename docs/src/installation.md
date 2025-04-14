# 安装与配置

## 安装步骤

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

在 `.env` 文件中设置以下环境变量：

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `WS_URL` | OneBot WebSocket 连接地址 | `ws://localhost:8080/ws` |
| `WS_ACCESS_TOKEN` | OneBot 访问令牌 | `your_token` |
| `GITHUB_WEBHOOK_SECRET` | GitHub Webhook 密钥 | `your_secret` |
| `GITHUB_REPO` | 监听的仓库列表 | `["username/repo"]` |
| `GITHUB_BRANCH` | 监听的分支列表 | `["main", "develop"]` |
| `QQ_GROUP` | 通知的 QQ 群号列表 | `[123456789]` |