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
