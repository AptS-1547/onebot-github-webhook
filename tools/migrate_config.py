#!/usr/bin/env python3
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
配置文件迁移工具

将 YAML 配置迁移到 TOML 格式。

Usage:
    python tools/migrate_config.py [--yaml FILE] [--toml FILE] [--keep-backup]

作者：AptS:1547
版本：0.2.0-alpha
日期：2025-04-18
"""

import argparse
import pathlib
import shutil
import sys
import logging

# 添加项目根目录到 Python 路径
project_root = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.models.config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_config(
    yaml_file: str = "config.yaml",
    toml_file: str = "config.toml",
    keep_backup: bool = True
) -> bool:
    """
    迁移配置文件从 YAML 到 TOML。

    Args:
        yaml_file: YAML 配置文件路径
        toml_file: TOML 配置文件路径
        keep_backup: 是否保留 YAML 备份

    Returns:
        bool: 迁移是否成功
    """
    yaml_path = pathlib.Path(yaml_file)
    toml_path = pathlib.Path(toml_file)

    # 检查 YAML 文件是否存在
    if not yaml_path.exists():
        logger.error("YAML 配置文件不存在: %s", yaml_path)
        return False

    # 检查 TOML 文件是否已存在
    if toml_path.exists():
        logger.warning("TOML 配置文件已存在: %s", toml_path)
        response = input("是否覆盖？(y/N): ")
        if response.lower() != 'y':
            logger.info("取消迁移")
            return False

    try:
        # 加载 YAML 配置
        logger.info("正在加载 YAML 配置: %s", yaml_path)
        config = Config.from_yaml_legacy(str(yaml_file))

        # 保存为 TOML
        logger.info("正在保存 TOML 配置: %s", toml_path)
        config.to_toml_file(str(toml_file))

        # 处理 YAML 文件
        if keep_backup:
            backup_path = yaml_path.with_suffix('.yaml.bak')
            logger.info("创建 YAML 备份: %s", backup_path)
            shutil.copy2(yaml_path, backup_path)

        logger.info("=" * 60)
        logger.info("✓ 配置迁移成功！")
        logger.info("  YAML: %s", yaml_path)
        logger.info("  TOML: %s", toml_path)
        if keep_backup:
            logger.info("  备份: %s", backup_path)
        logger.info("=" * 60)

        # 显示迁移后的配置摘要
        logger.info("配置摘要：")
        logger.info("  Bot 后端数量: %d", len(config.bot_backends))
        for backend in config.bot_backends:
            logger.info("    - %s (%s)", backend.name, backend.platform)

        logger.info("  Webhook 源数量: %d", len(config.webhook_sources))
        for source in config.webhook_sources:
            logger.info("    - %s (%s): %d 个目标",
                       source.name, source.type, len(source.targets))

        return True

    except Exception as e:  # pylint: disable=broad-except
        logger.error("迁移失败: %s", e, exc_info=True)
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="将 YAML 配置迁移到 TOML 格式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认文件名迁移
  python tools/migrate_config.py

  # 指定文件名
  python tools/migrate_config.py --yaml old_config.yaml --toml new_config.toml

  # 不保留备份
  python tools/migrate_config.py --no-keep-backup
        """
    )

    parser.add_argument(
        '--yaml',
        default='config.yaml',
        help='YAML 配置文件路径 (默认: config.yaml)'
    )
    parser.add_argument(
        '--toml',
        default='config.toml',
        help='TOML 配置文件路径 (默认: config.toml)'
    )
    parser.add_argument(
        '--keep-backup',
        action='store_true',
        default=True,
        help='保留 YAML 备份文件 (默认: True)'
    )
    parser.add_argument(
        '--no-keep-backup',
        action='store_false',
        dest='keep_backup',
        help='不保留 YAML 备份文件'
    )

    args = parser.parse_args()

    success = migrate_config(
        yaml_file=args.yaml,
        toml_file=args.toml,
        keep_backup=args.keep_backup
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
