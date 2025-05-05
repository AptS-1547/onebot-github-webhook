import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.matching import match_pattern

def test_exact_match():
    """测试精确匹配"""
    assert match_pattern("user/repo", "user/repo") is True
    assert match_pattern("User/Repo", "user/repo") is True  # 测试大小写不敏感
    assert match_pattern("user/repo", "user/other-repo") is False

def test_wildcard_match():
    """测试通配符匹配"""
    # 星号通配符
    assert match_pattern("user/repo", "*") is True
    assert match_pattern("user/repo", "user/*") is True
    assert match_pattern("user/sample-repo", "user/*-repo") is True
    assert match_pattern("other/repo", "user/*") is False

    # 问号通配符 - 注意问号在fnmatch中匹配单个字符
    assert match_pattern("user/repo1", "user/repo?") is True
    assert match_pattern("user/repo", "user/repo?") is False  # repo后面需要有一个字符

    # 字符集通配符
    assert match_pattern("user/repo1", "user/repo[1-3]") is True
    assert match_pattern("user/repo2", "user/repo[1-3]") is True
    assert match_pattern("user/repo4", "user/repo[1-3]") is False

def test_empty_values():
    """测试空值处理"""
    assert match_pattern("", "pattern") is False
    assert match_pattern("value", "") is False
    assert match_pattern("", "") is False

def test_special_patterns():
    """测试特殊模式"""
    # 单独的 * 匹配所有内容
    assert match_pattern("anything", "*") is True

    # 复杂模式
    assert match_pattern("org-name/api-service", "*/*-service") is True
    assert match_pattern("org-name/ui-component", "*/*-component") is True
    assert match_pattern("org-name/service", "*/*-service") is False
