from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Pydantic 类型检查和验证"""

    ENV: str = Field(default="production")

    WS_URL: str = Field(default="")
    WS_ACCESS_TOKEN: str = Field(default="")
    GITHUB_WEBHOOK_SECRET: str = Field(default="")
    GITHUB_REPO: List[str] = Field(default=[ "AptS-1547/AptS-1547" ])
    QQ_GROUP: List[int] = Field(default=[ 123456789 ])

    class Config:           # pylint: disable=too-few-public-methods
        """Pydantic 配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"

    @field_validator("WS_URL")
    @classmethod
    def check_ws_url(cls, value):
        """检查 WS_URL 的格式"""
        if not value.startswith("ws://") and not value.startswith("wss://"):
            raise ValueError("WS_URL must start with 'ws://' or 'wss://'")
        return value
