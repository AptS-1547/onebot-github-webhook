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
Onebot GitHub Webhook API 模块
本模块包含应用的所有 API 路由
作者：AptS:1547
版本：0.1.0-alpha
日期：2025-04-17
本程序遵循 Apache License 2.0 许可证
"""

from fastapi import APIRouter

from .github_webhook import router as github_webhook_router

# 主路由
api_router = APIRouter()

# 注册子路由
api_router.include_router(github_webhook_router, prefix="/github-webhook", tags=["github"])

__all__ = ["api_router"]
