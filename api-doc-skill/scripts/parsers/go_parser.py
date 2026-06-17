import re
from typing import List, Optional
from .base_parser import BaseParser, ParseResult
from scripts.models.api_info import ApiInfo
from scripts.models.parameter import Parameter, ParameterLocation
from scripts.models.response import ResponseInfo


class GoGinParser(BaseParser):
    """Go Gin 框架解析器"""

    DETECT_PATTERNS = [
        r'r\.GET',
        r'r\.POST',
        r'r\.PUT',
        r'r\.DELETE',
        r'gin\.New',
        'gin.Context',
    ]

    ROUTE_PATTERNS = [
        r'(?:r|router|engine)\.(GET|POST|PUT|DELETE|PATCH)\s*\(\s*(["\'])(.*?)\2',
        r'(?:r|router|engine)\.(GET|POST|PUT|DELETE|PATCH)\s*\(\s*(.*?)\s*[,)]',
    ]

    def detect(self, code: str) -> bool:
        """检测是否是 Go Gin 代码"""
        for pattern in self.DETECT_PATTERNS:
            if re.search(pattern, code):
                return True
        return False

    def parse(self, code: str, source_file: Optional[str] = None) -> ParseResult:
        """解析 Go Gin 代码"""
        # 尝试多种模式匹配
        http_method, path = None, None
        for pattern in self.ROUTE_PATTERNS:
            match = re.search(pattern, code, re.DOTALL)
            if match:
                http_method = self.extract_http_method(match.group(1))
                if len(match.groups()) >= 3 and match.group(3):
                    path = match.group(3)
                else:
                    path = match.group(2)
                break

        if not path:
            return ParseResult.fail("无法找到路由定义，请确保代码包含 r.GET/r.POST 调用")

        path = self.cleanup_path(path)
        # Gin :id -> {id}
        path = re.sub(r':(\w+)', r'{\1}', path)

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

        # 默认成功响应
        if not api_info.responses:
            api_info.responses.append(ResponseInfo(
                status_code=200,
                description="成功",
                example_json='{\n  "code": 200,\n  "message": "success",\n  "data": {}\n}'
            ))

        # 从注释提取描述
        comment = self._extract_comment(code)
        if comment:
            api_info.description = comment

        return ParseResult.ok(api_info)

    def _extract_api_name(self, code: str, path: str) -> str:
        """提取接口名称"""
        # 寻找处理函数名
        handler_match = re.search(r',\s*(\w+)\s*\)', code)
        if handler_match:
            handler_name = handler_match.group(1)
            readable = handler_name.replace('_', ' ').title()
            return readable

        # 从路径提取
        if path:
            name = path.strip('/').replace('-', ' ').replace('_', ' ').replace('{', '').replace('}', '').title()
            if name:
                return name

        return "Unknown API"

    def _extract_comment(self, code: str) -> Optional[str]:
        """提取注释"""
        # 单行注释
        comment_match = re.search(r'//\s*(.+)', code)
        if comment_match:
            return comment_match.group(1).strip()

        return None

    def _parse_parameters(self, code: str) -> List[Parameter]:
        """解析参数"""
        parameters = []

        # Gin 路径参数 :id -> {id}
        path_params = re.findall(r'{(\w+)}', path) if 'path' in locals() else []
        for param_name in path_params:
            parameters.append(Parameter(
                name=param_name,
                type_='string',
                required=True,
                location=ParameterLocation.PATH
            ))

        # gin 提取参数方式 c.Query
        query_params = re.findall(r'c\.Query\([\'"](\w+)[\'"]', code)
        for param_name in query_params:
            parameters.append(Parameter(
                name=param_name,
                type_='string',
                required=False,
                location=ParameterLocation.QUERY
            ))

        # ShouldBind 绑定 JSON body
        if 'ShouldBind' in code or 'BindJSON' in code:
            # 提取结构体类型
            bind_match = re.search(r'c\.ShouldBind\(&?(\w+)\)?', code)
            type_name = 'object'
            if bind_match:
                type_name = bind_match.group(1)
            parameters.append(Parameter(
                name='body',
                type_=type_name,
                required=True,
                description='JSON 请求体',
                location=ParameterLocation.BODY
            ))

        return parameters
