import pathlib
from typing import List, Literal

import yaml
from pydantic import field_validator, BaseModel

class OnebotTarget(BaseModel):
    """OneBot 目标类型"""
    type: Literal["private", "group"]
    id: int

class WebhookConfig(BaseModel):
    """Webhook 配置类"""
    NAME: str
    REPO: List[str]
    BRANCH: List[str]
    SECRET: str
    EVENTS: List[str]
    ONEBOT: List[OnebotTarget]

class Settings(BaseModel):
    """配置类"""

    ENV: str = "production"
    WS_URL: str = ""
    WS_ACCESS_TOKEN: str = ""
    GITHUB_WEBHOOK: List[WebhookConfig] = []

    @field_validator("WS_URL")
    @classmethod
    def check_ws_url(cls, value):
        """检查 WS_URL 的格式"""
        if value and not value.startswith("ws://") and not value.startswith("wss://"):
            raise ValueError("WS_URL must start with 'ws://' or 'wss://'")
        return value

    @classmethod
    def from_yaml(cls, yaml_file: str = "config.yaml"):
        """从YAML文件加载配置"""
        config_path = pathlib.Path(__file__).parent / yaml_file

        # 使用默认值初始化
        settings = cls()

        # 如果配置文件存在，则加载
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            if config_data:
                # 处理 WEBHOOK 字段，使其符合 OnebotTarget 模型
                if "WEBHOOK" in config_data:
                    for webhook in config_data["WEBHOOK"]:
                        if "ONEBOT" in webhook:
                            for i, target in enumerate(webhook["ONEBOT"]):
                                # 确保每个target是一个OnebotTarget对象
                                if isinstance(target, dict):
                                    webhook["ONEBOT"][i] = OnebotTarget(**target)

                # 使用 model_validate 创建实例
                try:
                    return cls.model_validate(config_data)
                except Exception as e:
                    print(f"配置验证失败: {e}")
                    print("使用部分配置和默认值")

                    # 更新基本配置
                    for key, value in config_data.items():
                        if key != "WEBHOOK" and hasattr(settings, key):
                            setattr(settings, key, value)
        else:
            print(f"警告：配置文件 {yaml_file} 不存在，使用默认配置")

            # 创建默认配置文件
            default_config = {
                "ENV": "production",
                "WS_URL": "",
                "WS_ACCESS_TOKEN": "",
                "GITHUB_WEBHOOK": [
                    {
                        "NAME": "github",
                        "REPO": ["AptS-1547/onebot-github-webhook"],
                        "BRANCH": ["main"],
                        "SECRET": "",
                        "EVENTS": ["push", "pull_request", "issues", "issue_comment", "release"],
                        "ONEBOT": [
                            {"type": "group", "id": 123456789}
                        ]
                    }
                ]
            }

            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, indent=2, sort_keys=False, default_flow_style=False, allow_unicode=True)

            print(f"已创建默认配置文件：{config_path}")

        return settings
