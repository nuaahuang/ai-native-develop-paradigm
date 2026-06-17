import re
from typing import List, Optional
from .base_parser import BaseParser, ParseResult
from scripts.models.api_info import ApiInfo
from scripts.models.parameter import Parameter, ParameterLocation
from scripts.models.response import ResponseInfo, ResponseField


class DjangoRestFrameworkParser(BaseParser):
    """Django REST Framework 解析器"""

    # 检测特征关键词
    DETECT_PATTERNS = [
        r'@api_view',
        r'api_view',
        r'ViewSet',
        r'GenericAPIView',
        r'@action',
        r'rest_framework',
    ]

    # 路由装饰器模式
    API_VIEW_PATTERN = r'@api_view\s*\(\s*\[(.*?)\]\s*\)'
    ACTION_PATTERN = r'@action\s*\(.*?methods\s*=\s*(.*?)\s*.*?\)'
    ACTION_PATTERN_ALT = r'@action\s*\(.*?detail\s*=\s*\w+\s*,\s*methods\s*=\s*(.*?)\)'
    URL_PATTERN = r'url\s*\(.*?r"([^"]+)"'

    def detect(self, code: str) -> bool:
        """检测是否是 Django REST Framework 代码"""
        for pattern in self.DETECT_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                return True
        return False

    def parse(self, code: str, source_file: Optional[str] = None) -> ParseResult:
        """解析 Django REST Framework 代码"""
        # 收集 HTTP 方法
        http_methods = []

        # 匹配 @api_view
        api_view_match = re.search(self.API_VIEW_PATTERN, code, re.DOTALL)
        if api_view_match:
            methods_str = api_view_match.group(1)
            # 提取方法，如 ['GET', 'POST']
            methods = re.findall(r'["\'](\w+?)["\']', methods_str)
            http_methods.extend(methods)

        # 匹配 @action
        action_match = re.search(self.ACTION_PATTERN_ALT, code, re.DOTALL)
        if not action_match:
            action_match = re.search(self.ACTION_PATTERN, code, re.DOTALL)
        if action_match:
            methods_str = action_match.group(1)
            methods = re.findall(r'["\'](\w+?)["\']', methods_str)
            http_methods.extend(methods)

        if not http_methods:
            # 默认 GET
            http_methods = ['GET']

        # 取第一个方法作为主要方法
        http_method = self.extract_http_method(http_methods[0])

        # 提取路径 - 尝试从 urls.py 模式提取
        path = self._extract_path(code)
        if not path:
            # 从方法名推断
            method_name_match = re.search(r'def\s+(\w+)\s*\(', code)
            if method_name_match:
                method_name = method_name_match.group(1)
                path = '/' + method_name.lower().replace('_', '-') + '/'

        if not path:
            return ParseResult.fail("无法提取接口路径，请确保代码包含路由信息")

        path = self.cleanup_path(path)

        # 提取接口名称
        api_name = self._extract_api_name(code, path)

        # 创建 ApiInfo
        api_info = ApiInfo(
            name=api_name,
            http_method=http_method,
            path=path,
            source_file=source_file,
        )

        # 解析参数
        parameters = self._parse_parameters(code)
        api_info.parameters = parameters

        # 解析响应（从序列化器）
        response = self._parse_response(code)
        if response:
            api_info.responses.append(response)

        # 默认成功响应
        if not api_info.responses:
            api_info.responses.append(ResponseInfo(
                status_code=200,
                description="成功",
                example_json='{\n  "code": 200,\n  "message": "success",\n  "data": {}\n}'
            ))

        return ParseResult.ok(api_info)

    def _extract_path(self, code: str) -> Optional[str]:
        """提取路径"""
        # 尝试从 url 模式提取
        url_match = re.search(self.URL_PATTERN, code)
        if url_match:
            return url_match.group(1)

        # 尝试从类视图的 get_object 等方法推断
        # 查找 .as_view() 附近的路径
        as_view_match = re.search(r'(\w+)\.as_view\(\)', code)
        if as_view_match:
            view_name = as_view_match.group(1).lower()
            return '/' + view_name + '/'

        return None

    def _extract_api_name(self, code: str, path: str) -> str:
        """提取接口名称"""
        # 从函数名提取
        func_match = re.search(r'def\s+(\w+)\s*\(', code)
        if func_match:
            func_name = func_match.group(1)
            # 转换为可读名称
            readable = func_name.replace('_', ' ').title()
            return readable

        # 从路径提取
        if path:
            name = path.strip('/').replace('-', ' ').replace('_', ' ').title()
            if name:
                return name

        return "Unknown API"

    def _parse_parameters(self, code: str) -> List[Parameter]:
        """解析参数"""
        parameters = []

        # 查找 URL 参数（<pk> 格式）
        path_params = re.findall(r'<(\w+)>', code)
        for param_name in path_params:
            parameters.append(Parameter(
                name=param_name,
                type_='string',
                required=True,
                location=ParameterLocation.PATH
            ))

        # 查找 query 参数 - 通过 self.request.query_params.get
        query_params = re.findall(r'request\.query_params\.get\([\'"](\w+)[\'"]', code)
        for param_name in query_params:
            parameters.append(Parameter(
                name=param_name,
                type_='string',
                required=False,
                location=ParameterLocation.QUERY
            ))

        # 查找 body 参数 - 通过 request.data
        if 'request.data' in code or 'self.request.data' in code:
            # 查找序列化器
            serializer_match = re.search(r'(\w+Serializer)\s*\(\s*data=request', code)
            if serializer_match:
                serializer_name = serializer_match.group(1)
                parameters.append(Parameter(
                    name=serializer_name,
                    type_='object',
                    required=True,
                    description=f'请求体，使用 {serializer_name} 序列化',
                    location=ParameterLocation.BODY
                ))

        return parameters

    def _parse_response(self, code: str) -> Optional[ResponseInfo]:
        """解析响应"""
        # 查找序列化器返回
        serializer_match = re.search(r'return\s+Response\(\s*(\w+Serializer)', code)
        if serializer_match:
            serializer_name = serializer_match.group(1)
            return ResponseInfo(
                status_code=200,
                description=f"成功，使用 {serializer_name} 序列化",
            )

        return None
