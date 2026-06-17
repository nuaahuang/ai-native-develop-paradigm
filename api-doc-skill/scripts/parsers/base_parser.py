from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from scripts.models.api_info import ApiInfo


@dataclass
class ParseResult:
    """解析结果"""
    success: bool
    api_info: Optional[ApiInfo] = None
    errors: List[str] = None
    message: str = ""

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    @classmethod
    def ok(cls, api_info: ApiInfo) -> 'ParseResult':
        return cls(success=True, api_info=api_info)

    @classmethod
    def fail(cls, message: str, errors: List[str] = None) -> 'ParseResult':
        return cls(success=False, message=message, errors=errors or [])


class BaseParser(ABC):
    """解析器基类"""

    @abstractmethod
    def detect(self, code: str) -> bool:
        """检测给定代码是否能被此解析器处理"""
        pass

    @abstractmethod
    def parse(self, code: str, source_file: Optional[str] = None) -> ParseResult:
        """解析代码返回 ApiInfo"""
        pass

    def cleanup_path(self, path: str) -> str:
        """清理接口路径，去除多余引号等"""
        path = path.strip()
        # 去除引号
        if (path.startswith('"') and path.endswith('"')) or \
           (path.startswith("'") and path.endswith("'")):
            path = path[1:-1].strip()
        # 去除括号
        if path.startswith('(') and path.endswith(')'):
            path = path[1:-1].strip()
        # 确保以 / 开头
        if not path.startswith('/'):
            path = '/' + path
        return path

    def extract_http_method(self, method: str) -> str:
        """标准化 HTTP 方法"""
        method = method.strip().upper()
        known_methods = {'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'}
        if method in known_methods:
            return method
        return 'GET'  # 默认返回 GET
