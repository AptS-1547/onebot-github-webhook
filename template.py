"""
OneBot GitHub Webhook 消息模板管理器
本模块用于管理 GitHub Webhook 事件的消息模板，支持动态加载和渲染模板。
作者：AptS:1547
版本：0.1.0-alpha
日期：2025-04-18
本程序遵循 GPL-3.0 许可证
"""

import pathlib
import logging
from pathlib import Path
from typing import Dict, Optional, Any
import jinja2

logger = logging.getLogger(__name__)

class TemplateManager:
    """
    管理 GitHub Webhook 事件的消息模板
    """

    def __init__(self, templates_dir: str = 'templates'):
        """
        初始化模板管理器
        
        Args:
            templates_dir: 模板目录路径
        """
        self.templates_dir = Path(templates_dir)
        self.environment = jinja2.Environment(
            loader=jinja2.FileSystemLoader(templates_dir),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )

        # 确保模板目录存在
        pathlib.Path(templates_dir).mkdir(parents=True, exist_ok=True)

        # 事件类型到默认模板的映射
        self.default_templates = {
            # 硬编码的默认模板，当文件不存在时使用
            "push": self._get_default_push_template(),
            "issues": self._get_default_issues_template(),
            "pull_request": self._get_default_pull_request_template(),
            "default": self._get_generic_template()
        }

        logger.info("模板管理器初始化完成，模板目录: %s", templates_dir)

    def get_template_path(
            self,
            event_type: str,
            template_name: Optional[str] = None
            ) -> Optional[str]:
        """
        获取模板文件路径
        
        搜索顺序:
        1. 指定的模板名称 (若提供)
        2. 事件类型的默认模板 (event_type/default.txt)
        3. 通用默认模板 (default.txt)
        
        Args:
            event_type: 事件类型 (push, issues, pull_request 等)
            template_name: 指定的模板名称 (可选)
            
        Returns:
            模板文件路径或 None (如果找不到模板)
        """
        template_paths = []

        # 1. 检查指定的模板
        if template_name and template_name != 'default':
            # 检查直接指定的路径
            if pathlib.Path(self.templates_dir / template_name).exists():
                template_paths.append(template_name)

            # 检查事件类型目录下的指定模板
            event_template = f"{event_type}/{template_name}"
            if pathlib.Path(self.templates_dir / event_template).exists():
                template_paths.append(event_template)

            # 检查带txt扩展名的模板
            if not template_name.endswith('.txt'):
                template_txt = f"{template_name}.txt"
                if pathlib.Path(self.templates_dir / template_txt).exists():
                    template_paths.append(template_txt)

                event_template_txt = f"{event_type}/{template_name}.txt"
                if pathlib.Path(self.templates_dir / event_template_txt).exists():
                    template_paths.append(event_template_txt)

        # 2. 检查事件类型的默认模板
        default_event_template = f"{event_type}/default.txt"
        if pathlib.Path(self.templates_dir / default_event_template).exists():
            template_paths.append(default_event_template)

        # 3. 检查通用默认模板
        if pathlib.Path(self.templates_dir / "default.txt").exists():
            template_paths.append("default.txt")

        # 返回第一个存在的模板路径
        for path in template_paths:
            return path

        # 都不存在，返回 None
        return None

    def render_template(
            self,
            event_type: str,
            template_name: Optional[str] = None,
            **kwargs
            ) -> str:
        """
        渲染指定事件类型的模板
        
        Args:
            event_type: GitHub 事件类型 (push, issues 等)
            template_name: 可选的指定模板名称
            **kwargs: 传递给模板的变量
            
        Returns:
            str: 渲染后的消息文本
        """
        template_path = self.get_template_path(event_type, template_name)

        try:
            if template_path:
                # 使用文件模板
                logger.info("使用模板文件: %s", template_path)
                template = self.environment.get_template(template_path)
                return template.render(**kwargs)

            # 使用内置默认模板
            logger.info("找不到模板文件, 使用内置默认模板: %s", event_type)
            default_template = self.default_templates.get(
                event_type,
                self.default_templates["default"]
            )
            template = jinja2.Template(default_template)
            return template.render(**kwargs)

        except jinja2.exceptions.TemplateError as e:
            logger.error("模板渲染错误: %s", e)
            # 错误发生时返回简单消息
            return self._render_error_template(event_type, kwargs)

    def _render_error_template(self, event_type: str, data: Dict[str, Any]) -> str:
        """在模板渲染失败时生成一个简单的错误消息"""
        repo_name = data.get('repo_name', 'unknown')
        message = f"⚠️ GitHub {event_type} 事件 ({repo_name})\n"
        message += "消息模板渲染失败，请检查日志获取详情"
        return message

    def _get_default_push_template(self) -> str:
        """获取内置的 push 事件默认模板"""
        return """📢 GitHub 推送通知
仓库：{{ repo_name }}
分支：{{ branch }}
推送者：{{ pusher }}
提交数量：{{ commit_count }}
{% for commit in commits[:3] %}
[{{ loop.index }}] {{ commit.id[:7] }} by {{ commit.author.name }}
    {{ commit.message.split('\n')[0] }}
{% endfor %}
"""

    def _get_default_issues_template(self) -> str:
        """获取内置的 issues 事件默认模板"""
        return """📋 GitHub Issue {{ action }}
仓库：{{ repo_name }}
标题：{{ issue.title }}
作者：{{ issue.user.login }}
链接：{{ issue.html_url }}
"""

    def _get_default_pull_request_template(self) -> str:
        """获取内置的 pull_request 事件默认模板"""
        return """🔄 GitHub Pull Request {{ action }}
仓库：{{ repo_name }}
标题：{{ pull_request.title }}
作者：{{ pull_request.user.login }}
从：{{ pull_request.head.label }}
到：{{ pull_request.base.label }}
链接：{{ pull_request.html_url }}
"""

    def _get_generic_template(self) -> str:
        """获取通用事件模板"""
        return """🔔 GitHub {{ event_type }} 事件
仓库：{{ repo_name }}
详情请访问仓库页面查看
"""

    def create_example_templates(self):
        """创建示例模板文件"""
        # 确保目录存在
        pathlib.Path(self.templates_dir / "push").mkdir(parents=True, exist_ok=True)
        pathlib.Path(self.templates_dir / "issues").mkdir(parents=True, exist_ok=True)
        pathlib.Path(self.templates_dir / "pull_request").mkdir(parents=True, exist_ok=True)

        # 创建示例模板
        with open(self.templates_dir / "push" / "default.txt", "w", encoding="utf-8") as f:
            f.write(self._get_default_push_template())

        with open(self.templates_dir / "issues" / "default.txt", "w", encoding="utf-8") as f:
            f.write(self._get_default_issues_template())

        with open(self.templates_dir / "pull_request" / "default.txt", "w", encoding="utf-8") as f:
            f.write(self._get_default_pull_request_template())

        with open(self.templates_dir / "default.txt", "w", encoding="utf-8") as f:
            f.write(self._get_generic_template())

        logger.info("示例模板文件已创建")


# 全局模板管理器实例
template_manager = TemplateManager()

def render_template(event_type: str, template_name: Optional[str] = None, **kwargs) -> str:
    """
    渲染指定事件类型的模板 (便捷函数)
    
    Args:
        event_type: GitHub 事件类型 (push, issues 等)
        template_name: 可选的指定模板名称
        **kwargs: 传递给模板的变量
        
    Returns:
        str: 渲染后的消息文本
    """
    return template_manager.render_template(event_type, template_name, **kwargs)


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)

    # 创建示例模板 (仅用于演示)
    template_manager.create_example_templates()

    # 测试渲染
    test_data = {
        'repo_name': 'AptS-1547/onebot-github-webhook',
        'branch': 'main',
        'pusher': 'AptS-1547',
        'commit_count': 2,
        'commits': [
            {
                'id': '1234567890abcdef',
                'message': 'Add new feature',
                'author': {'name': 'AptS-1547'}
            },
            {
                'id': '0987654321fedcba',
                'message': 'Fix bug',
                'author': {'name': 'Contributor'}
            }
        ]
    }

    # 测试不同的模板加载场景
    print("\n=== 使用事件默认模板 ===")
    print(render_template('push', **test_data))

    print("\n=== 使用指定模板 ===")
    print(render_template('push', 'custom', **test_data))

    print("\n=== 使用不存在的模板(应该回退到默认) ===")
    print(render_template('push', 'nonexistent', **test_data))

    print("\n=== 使用不存在的事件类型(应该使用通用模板) ===")
    print(render_template('unknown_event', 'custom', **test_data))
