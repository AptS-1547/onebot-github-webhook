## 部署建议

### Docker 部署

```bash
docker run -d \
  --name onebot-github-webhook \
  -p 8000:8000 \
  -v $(pwd)/config.yaml:/app/config.yaml \
  e1saps/onebot-github-webhook:latest
```

或使用 Docker Compose:

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
WantedBy=multi-user.target
```

启用服务:

```bash
sudo systemctl enable onebot-github-webhook
sudo systemctl start onebot-github-webhook
```
