# Copyright 2025 AptS-1547
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Onebot Github Webhook 配置类
本文件用于定义 Onebot Github Webhook 的配置类和验证逻辑。
作者：AptS:1547
版本：0.1.0-alpha
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

import pathlib
import logging
from typing import List, Literal
from functools import lru_cache

import yaml
from pydantic import model_validator, BaseModel, ValidationError

logger = logging.getLogger(__name__)

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

class Config(BaseModel):
    """配置类"""

    ENV: str = "production"
    ONEBOT_URL: str = ""
    ONEBOT_PROTOCOL_TYPE: Literal["http", "ws"] = "ws"
    ONEBOT_ACCESS_TOKEN: str = ""
    GITHUB_WEBHOOK: List[WebhookConfig] = []

    @model_validator(mode='after')
    def validate_onebot_url(self) -> 'Config':
        """验证 ONEBOT_URL 的格式是否与 ONEBOT_TYPE 匹配"""
        if self.ONEBOT_URL:
            if self.ONEBOT_PROTOCOL_TYPE == "ws" and not (self.ONEBOT_URL.startswith("ws://") or self.ONEBOT_URL.startswith("wss://")):          # pylint: disable=line-too-long
                raise ValueError("当 ONEBOT_TYPE 为 ws 时，ONEBOT_URL 必须以 'ws://' 或 'wss://' 开头")
            if self.ONEBOT_PROTOCOL_TYPE == "http" and not (self.ONEBOT_URL.startswith("http://") or self.ONEBOT_URL.startswith("https://")):    # pylint: disable=line-too-long
                raise ValueError("当 ONEBOT_TYPE 为 http 时，ONEBOT_URL 必须以 'http://' 或 'https://' 开头")
        return self

    @classmethod
    def from_yaml(cls, yaml_file: str = "config.yaml"):
        """从YAML文件加载配置"""
        config_path = pathlib.Path.cwd() / yaml_file

        config = cls()

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
                except yaml.YAMLError as e:
                    logger.error("YAML配置加载失败: %s", e)
                    raise
                except ValidationError as e:
                    logger.error("Pydantic配置验证失败: %s", e)
                    for error in e.errors():
                        logger.error("  %s: %s", error['loc'], error['msg'])
                    raise

        else:
            logger.warning("警告：配置文件 %s 不存在，使用默认配置", config_path)

            # 创建默认配置文件
            default_config = {
                "ENV": "production",
                "ONEBOT_URL": "",
                "ONEBOT_PROTOCOL_TYPE": "ws",
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

            logger.info("已创建默认配置文件 %s，请根据需要修改", config_path)

        return config

@lru_cache()
def get_settings():
    """获取应用配置（缓存结果）"""
    return Config().from_yaml()
