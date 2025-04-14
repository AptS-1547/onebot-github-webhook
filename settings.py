import pathlib
from typing import List

import yaml
from pydantic import field_validator, BaseModel

class Settings(BaseModel):
    """配置类"""

    ENV: str = "production"

    WS_URL: str = ""
    WS_ACCESS_TOKEN: str = ""
    GITHUB_WEBHOOK_SECRET: str = ""
    GITHUB_REPO: List[str] = ["AptS-1547/AptS-1547"]
    GITHUB_BRANCH: List[str] = ["main"]
    QQ_GROUP: List[int] = [123456789]

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
                # 更新配置
                for key, value in config_data.items():
                    if hasattr(settings, key):
                        setattr(settings, key, value)
        else:
            print(f"警告：配置文件 {yaml_file} 不存在，使用默认配置")

            # 创建默认配置文件
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(settings.model_dump(), f, indent=2, sort_keys=False, default_flow_style=False, allow_unicode=True)

            print(f"已创建默认配置文件：{config_path}")

        return settings
