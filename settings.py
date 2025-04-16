"""
Onebot Github Webhook 配置类
本文件用于定义 Onebot Github Webhook 的配置类和验证逻辑。
作者：AptS:1547
版本：0.1.0-alpha
日期：2025-04-17
本程序遵循 GPL-3.0 许可证
"""

import pathlib
from typing import List, Literal

import yaml
from pydantic import model_validator, BaseModel

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
    ONEBOT_URL: str = ""
    ONEBOT_TYPE: Literal["http", "ws"] = "ws"
    ONEBOT_ACCESS_TOKEN: str = ""
    GITHUB_WEBHOOK: List[WebhookConfig] = []

    @model_validator(mode='after')
    def validate_onebot_url(self) -> 'Settings':
        """验证 ONEBOT_URL 的格式是否与 ONEBOT_TYPE 匹配"""
        if self.ONEBOT_URL:
            if self.ONEBOT_TYPE == "ws" and not (self.ONEBOT_URL.startswith("ws://") or self.ONEBOT_URL.startswith("wss://")):          # pylint: disable=line-too-long
                raise ValueError("当 ONEBOT_TYPE 为 ws 时，ONEBOT_URL 必须以 'ws://' 或 'wss://' 开头")
            if self.ONEBOT_TYPE == "http" and not (self.ONEBOT_URL.startswith("http://") or self.ONEBOT_URL.startswith("https://")):    # pylint: disable=line-too-long
                raise ValueError("当 ONEBOT_TYPE 为 http 时，ONEBOT_URL 必须以 'http://' 或 'https://' 开头")
        return self

    @classmethod
    def from_yaml(cls, yaml_file: str = "config.yaml"):
        """从YAML文件加载配置"""
        config_path = pathlib.Path(__file__).parent / yaml_file

        # 使用默认值初始化
        settings = cls()

        # 如果配置文件存在，则加载
        if config_path.exists():         # pylint: disable=too-many-nested-blocks
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            if config_data:
                # 处理 WEBHOOK 字段，使其符合 OnebotTarget 模型
                if "GITHUB_WEBHOOK" in config_data:
                    for webhook in config_data["GITHUB_WEBHOOK"]:
                        if "ONEBOT" in webhook:
                            for i, target in enumerate(webhook["ONEBOT"]):
                                # 确保每个target是一个OnebotTarget对象
                                if isinstance(target, dict):
                                    webhook["ONEBOT"][i] = OnebotTarget(**target)

                # 使用 model_validate 创建实例
                try:
                    return cls.model_validate(config_data)
                except Exception as e:                # pylint: disable=broad-except
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
                "ONEBOT_URL": "",
                "ONEBOT_TYPE": "ws",
                "ONEBOT_ACCESS_TOKEN": "",
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

            with open(config_path, 'w', encoding='utf-8') as file:
                yaml.dump(default_config,
                          file,
                          indent=2,
                          sort_keys=False,
                          default_flow_style=False,
                          allow_unicode=True
                          )

            print(f"已创建默认配置文件：{config_path}")

        return settings
