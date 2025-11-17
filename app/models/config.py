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
支持 TOML 和 YAML 格式（YAML 已弃用）。

作者：AptS:1547
版本：0.2.0-alpha
日期：2025-04-18
本程序遵循 Apache License 2.0 许可证
"""

import pathlib
import logging
import sys
from typing import List, Literal, Optional, Dict, Any

import yaml
from pydantic import model_validator, BaseModel, ValidationError, Field, ConfigDict

# Python 3.11+ 使用内置 tomllib，否则使用 tomli
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

logger = logging.getLogger(__name__)


# ============================================================================
# 应用配置
# ============================================================================

class AppConfig(BaseModel):
    """
    应用全局配置。

    Attributes:
        env: 运行环境（production/development）
        log_level: 日志级别
    """
    env: str = "production"
    log_level: str = "INFO"


# ============================================================================
# Bot 后端配置
# ============================================================================

class BotConnectionConfig(BaseModel):
    """
    Bot 连接配置（动态字段）。

    不同平台的连接参数不同，使用 extra="allow" 允许额外字段。

    Examples:
        OneBot: {"protocol": "http", "url": "http://...", "access_token": "..."}
        Telegram: {"token": "bot_token"}
        企业微信: {"webhook_url": "https://..."}
    """
    model_config = ConfigDict(extra="allow")


class BotBackendConfig(BaseModel):
    """
    单个 Bot 后端配置。

    Attributes:
        name: Bot 实例名称（用户自定义，全局唯一）
        platform: Bot 平台类型（onebot/telegram/wecom 等）
        enabled: 是否启用
        module: 客户端模块路径（可选，默认为 app.botclient.{platform}）
        connection: 连接配置（平台特定）
    """
    name: str
    platform: str
    enabled: bool = True
    module: Optional[str] = None
    connection: BotConnectionConfig


# ============================================================================
# Webhook 数据源配置
# ============================================================================

class WebhookTargetConfig(BaseModel):
    """
    Webhook 消息目标配置（内联定义时使用）。

    Attributes:
        bot: 引用的 bot_backends.name
        type: 目标类型（如 group/private/channel 等，平台特定）
        id: 目标 ID（字符串，兼容各平台）
    """
    bot: str
    type: str
    id: str


class NamedTargetConfig(WebhookTargetConfig):
    """
    具名的消息目标配置（全局定义时使用）。

    继承 WebhookTargetConfig 的所有字段，并添加唯一标识。

    Attributes:
        name: 目标名称（唯一标识，用于引用）
        bot: 引用的 bot_backends.name
        type: 目标类型（如 group/private/channel 等，平台特定）
        id: 目标 ID（字符串，兼容各平台）
    """
    name: str


class WebhookSourceConfig(BaseModel):
    """
    单个 Webhook 数据源配置。

    Attributes:
        name: 数据源名称（用户自定义）
        type: 数据源类型（github/gitlab/gitea/generic 等）
        secret: Webhook 签名密钥
        repos: 仓库过滤列表
        branches: 分支过滤列表
        events: 事件类型列表
        targets: 消息目标列表（字符串数组，引用全局 targets 的 name）
    """
    name: str
    type: str
    secret: str = ""
    repos: List[str] = Field(default_factory=list)
    branches: List[str] = Field(default_factory=list)
    events: List[str] = Field(default_factory=list)
    targets: List[str] = Field(default_factory=list)  # 改为字符串数组


# ============================================================================
# 主配置类
# ============================================================================

class Config(BaseModel):
    """
    主配置类。

    Attributes:
        app: 应用配置
        bot_backends: Bot 后端列表
        targets: 全局消息目标列表
        webhook_sources: Webhook 数据源列表
    """
    app: AppConfig = Field(default_factory=AppConfig)
    bot_backends: List[BotBackendConfig] = Field(default_factory=list)
    targets: List[NamedTargetConfig] = Field(default_factory=list)
    webhook_sources: List[WebhookSourceConfig] = Field(default_factory=list)

    @model_validator(mode='after')
    def validate_target_references(self) -> 'Config':
        """
        验证 webhook_sources 中引用的 target 名称是否存在。

        Returns:
            Config: 验证后的配置对象

        Raises:
            ValueError: 如果引用的 target 不存在
        """
        # 构建 target 名称集合
        target_names = {t.name for t in self.targets}

        # 验证每个 source 的 targets 引用
        for source in self.webhook_sources:
            for target_name in source.targets:
                if target_name not in target_names:
                    raise ValueError(
                        f"Webhook 源 '{source.name}' 引用了不存在的 target: '{target_name}'. "
                        f"可用的 targets: {sorted(target_names)}"
                    )

        return self

    def get_target_by_name(self, name: str) -> Optional[NamedTargetConfig]:
        """
        根据名称查找 target 配置。

        Args:
            name: Target 名称

        Returns:
            Optional[NamedTargetConfig]: Target 配置，如果不存在则返回 None
        """
        for target in self.targets:
            if target.name == name:
                return target
        return None

    @property
    def GITHUB_WEBHOOK(self) -> List['WebhookConfig']:
        """
        向后兼容属性：将新配置格式转换为旧格式。

        仅支持 GitHub 类型的 webhook 源。

        Returns:
            List[WebhookConfig]: 旧格式的 webhook 配置列表
        """
        legacy_webhooks: List[WebhookConfig] = []

        for source in self.webhook_sources:
            # 只转换 GitHub 类型的源
            if source.type != "github":
                continue

            # 转换目标配置
            onebot_targets = []
            for target_name in source.targets:
                # 查找 target 定义
                target = self.get_target_by_name(target_name)
                if not target:
                    logger.warning(f"Target '{target_name}' 未找到，跳过")
                    continue

                # 只转换 onebot 类型的目标
                if target.bot == "onebot":
                    onebot_targets.append(
                        OnebotTarget(
                            type=target.type,  # type: ignore
                            id=int(target.id)
                        )
                    )

            # 创建旧格式的配置
            legacy_webhook = WebhookConfig(
                NAME=source.name,
                REPO=source.repos,
                BRANCH=source.branches,
                SECRET=source.secret,
                EVENTS=source.events,
                ONEBOT=onebot_targets
            )
            legacy_webhooks.append(legacy_webhook)

        return legacy_webhooks

    @model_validator(mode='after')
    def validate_bot_references(self) -> 'Config':
        """
        验证 targets 中引用的 bot 名称是否存在。

        Returns:
            Config: 验证后的配置实例

        Raises:
            ValueError: 当引用的 bot 不存在时
        """
        bot_names = {backend.name for backend in self.bot_backends}

        # 验证全局 targets 中的 bot 引用
        for target in self.targets:
            if target.bot not in bot_names:
                raise ValueError(
                    f"Target '{target.name}' 引用了不存在的 bot: '{target.bot}'. "
                    f"可用的 bots: {sorted(bot_names)}"
                )

        return self

    @classmethod
    def from_toml(cls, toml_file: str = "config.toml") -> 'Config':
        """
        从 TOML 文件加载配置。

        Args:
            toml_file: TOML 配置文件路径

        Returns:
            Config: 配置实例

        Raises:
            FileNotFoundError: 配置文件不存在
            ValidationError: 配置验证失败
        """
        config_path = pathlib.Path.cwd() / toml_file

        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_path, 'rb') as f:
            config_data = tomllib.load(f)

        try:
            return cls.model_validate(config_data)
        except ValidationError as e:
            logger.error("TOML 配置验证失败: %s", e)
            for error in e.errors():
                logger.error("  %s: %s", error['loc'], error['msg'])
            raise

    @classmethod
    def from_yaml_legacy(cls, yaml_file: str = "config.yaml") -> 'Config':
        """
        从 YAML 文件加载配置（向后兼容，已弃用）。

        将旧的 YAML 配置结构转换为新的配置模型。

        Args:
            yaml_file: YAML 配置文件路径

        Returns:
            Config: 配置实例

        Raises:
            FileNotFoundError: 配置文件不存在
            ValidationError: 配置验证失败
        """
        config_path = pathlib.Path.cwd() / yaml_file

        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            old_config = yaml.safe_load(f)

        # 转换为新的配置结构
        new_config_data: Dict[str, Any] = {
            "app": {
                "env": old_config.get("ENV", "production"),
                "log_level": old_config.get("LOG_LEVEL", "INFO")
            },
            "bot_backends": [],
            "webhook_sources": []
        }

        # 转换 OneBot 配置
        if old_config.get("ONEBOT_URL"):
            bot_config = {
                "name": "onebot",
                "platform": "onebot",
                "enabled": True,
                "connection": {
                    "protocol": old_config.get("ONEBOT_PROTOCOL_TYPE", "http"),
                    "url": old_config.get("ONEBOT_URL", ""),
                    "access_token": old_config.get("ONEBOT_ACCESS_TOKEN", "")
                }
            }
            new_config_data["bot_backends"].append(bot_config)

        # 转换 Webhook 配置
        for webhook in old_config.get("GITHUB_WEBHOOK", []):
            source_config = {
                "name": webhook["NAME"],
                "type": "github",
                "secret": webhook.get("SECRET", ""),
                "repos": webhook.get("REPO", []),
                "branches": webhook.get("BRANCH", []),
                "events": webhook.get("EVENTS", []),
                "targets": []
            }

            # 转换目标配置
            for target in webhook.get("ONEBOT", []):
                target_config = {
                    "bot": "onebot",
                    "type": target["type"],
                    "id": str(target["id"])
                }
                source_config["targets"].append(target_config)

            new_config_data["webhook_sources"].append(source_config)

        try:
            return cls.model_validate(new_config_data)
        except ValidationError as e:
            logger.error("YAML 配置转换失败: %s", e)
            for error in e.errors():
                logger.error("  %s: %s", error['loc'], error['msg'])
            raise

    def to_toml_file(self, toml_file: str = "config.toml") -> None:
        """
        将配置保存为 TOML 文件。

        Args:
            toml_file: TOML 配置文件路径
        """
        config_path = pathlib.Path.cwd() / toml_file

        config_dict = self.model_dump()

        with open(config_path, 'wb') as f:
            tomli_w.dump(config_dict, f)

        logger.info("配置已保存到 %s", config_path)

    @classmethod
    def create_default_toml(cls, toml_file: str = "config.toml") -> 'Config':
        """
        创建默认 TOML 配置文件。

        Args:
            toml_file: TOML 配置文件路径

        Returns:
            Config: 默认配置实例
        """
        default_config = cls(
            app=AppConfig(
                env="production",
                log_level="INFO"
            ),
            bot_backends=[
                BotBackendConfig(
                    name="onebot",
                    platform="onebot",
                    enabled=True,
                    connection=BotConnectionConfig(
                        protocol="http",
                        url="http://localhost:8080",
                        access_token="your_token_here"
                    )
                )
            ],
            webhook_sources=[
                WebhookSourceConfig(
                    name="github-main",
                    type="github",
                    secret="",
                    repos=["your/repo"],
                    branches=["main"],
                    events=["push", "pull_request", "issues"],
                    targets=[
                        WebhookTargetConfig(
                            bot="onebot",
                            type="group",
                            id="123456789"
                        )
                    ]
                )
            ]
        )

        default_config.to_toml_file(toml_file)
        logger.info("已创建默认配置文件: %s", toml_file)

        return default_config


# ============================================================================
# 向后兼容的旧配置类
# ============================================================================

class OnebotTarget(BaseModel):
    """OneBot 目标类型（向后兼容）"""
    type: Literal["private", "group"]
    id: int


class WebhookConfig(BaseModel):
    """Webhook 配置类（向后兼容）"""
    NAME: str
    REPO: List[str]
    BRANCH: List[str]
    SECRET: str
    EVENTS: List[str]
    ONEBOT: List[OnebotTarget]


class LegacyConfig(BaseModel):
    """旧配置类（向后兼容，已弃用）"""
    ENV: str = "production"
    ONEBOT_URL: str = ""
    ONEBOT_PROTOCOL_TYPE: Literal["http", "ws"] = "ws"
    ONEBOT_ACCESS_TOKEN: str = ""
    GITHUB_WEBHOOK: List[WebhookConfig] = Field(default_factory=list)


# ============================================================================
# 全局配置实例管理
# ============================================================================

_config_instance: Optional[Config] = None


def get_settings() -> Config:
    """
    获取应用配置（单例模式）。

    自动检测配置文件类型（TOML 优先，YAML 降级）。

    Returns:
        Config: 应用配置实例

    Raises:
        FileNotFoundError: 配置文件不存在
    """
    global _config_instance  # pylint: disable=global-statement

    if _config_instance is None:
        toml_path = pathlib.Path.cwd() / "config.toml"
        yaml_path = pathlib.Path.cwd() / "config.yaml"

        # 优先加载 TOML
        if toml_path.exists():
            logger.info("使用 TOML 配置: %s", toml_path)
            _config_instance = Config.from_toml()

        # 降级到 YAML（发出弃用警告）
        elif yaml_path.exists():
            logger.warning("=" * 60)
            logger.warning("警告：检测到 YAML 配置文件（已弃用）")
            logger.warning("请尽快迁移到 TOML 格式")
            logger.warning("迁移方法：python tools/migrate_config.py")
            logger.warning("=" * 60)
            _config_instance = Config.from_yaml_legacy()

        # 创建默认配置
        else:
            logger.warning("未找到配置文件，创建默认 TOML 配置")
            _config_instance = Config.create_default_toml()

    return _config_instance


def reload_settings() -> Config:
    """
    重新加载配置。

    Returns:
        Config: 新的配置实例
    """
    global _config_instance  # pylint: disable=global-statement

    _config_instance = None
    return get_settings()
