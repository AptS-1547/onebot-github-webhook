## 本地开发

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
cp config.example.yaml config.yaml
```

### 运行

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

或者直接执行：

```bash
python main.py
```
