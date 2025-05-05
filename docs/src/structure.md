## 项目结构

```
onebot-github-webhook/
│
├── app/                      # 应用程序核心模块
│   ├── api/                  # API 接口
|   ├   └── github_webhook.py # GitHub Webhook 接口
│   ├── core/                 # 核心功能
│   │   └── github.py         # GitHub Webhook 处理逻辑
│   ├── models/               # 数据模型
│   │   └── config.py         # 配置模型
|   ├── onebot/               # OneBot 发送器
│   │   └── onebot.py         # OneBot 消息发送客户端
│   └── utils/                # 工具函数
|       ├── exceptions.py     # 异常处理
│       └── matching.py       # 匹配规则工具
│
├── config/                   # 配置文件目录
│   ├── config.example.yaml   # 示例配置文件
│   └── templates/            # 消息模板目录
│       ├── push/             # 推送事件模板
│       ├── issues/           # Issue 事件模板
│       └── pull_request/     # Pull Request 事件模板
│
├── docs/                     # 文档目录
│   └── src/                  # mdBook 文档源
│
├── tests/                    # 测试目录
│   ├── test_matching.py      # 匹配规则测试
│   ├── test_onebot_sender.py # OneBot 发送器测试
│   └── test_webhook_signature.py # Webhook 签名验证测试
│
├── docker/                   # Docker 相关文件
│   └── docker-compose.yml    # Docker Compose 配置文件
│
├── main.py                   # 应用程序入口点
├── Dockerfile                # Docker 构建文件
├── pyproject.toml            # Python 项目配置
├── poetry.lock               # Poetry 依赖锁定文件
└── README.md                 # 项目说明文档
```
