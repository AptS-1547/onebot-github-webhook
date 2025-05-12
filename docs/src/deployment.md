## 部署建议

### Docker 部署

**⚠️ 注意: 请确保 `config.yaml` 存在于当前目录下，否则 Docker 容器将无法找到配置文件。**

首先，确保 Docker 和 Docker Compose 已安装。  
并且请你复制项目中的 `config.example.yaml` 为 `config.yaml`，并根据需要修改配置。  
然后，使用以下命令启动 Docker 容器：  

```bash
docker run -d \
  --name onebot-github-webhook \
  -p 8000:8000 \
  -v $(pwd)/config.yaml:/app/config.yaml \
  e1saps/onebot-github-webhook:latest
```

或使用 Docker Compose，参考文件 `docker/docker-compose.yml`：

```bash
cd docker
docker-compose up -d
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
ExecStart=/opt/onebot-github-webhook/.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=default.target
```

启用服务:

```bash
sudo systemctl enable onebot-github-webhook
sudo systemctl start onebot-github-webhook
```
