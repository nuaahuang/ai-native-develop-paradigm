import re
from typing import List, Optional
from .base_parser import BaseParser, ParseResult
from scripts.models.api_info import ApiInfo
from scripts.models.parameter import Parameter, ParameterLocation
from scripts.models.response import ResponseInfo


class FastAPIParser(BaseParser):
    """Python FastAPI 解析器"""

    DETECT_PATTERNS = [
        r'@app\.get',
        r'@app\.post',
        r'@app\.put',
        r'@app\.delete',
        r'@router\.get',
        r'@router\.post',
        r'FastAPI',
    ]

    # 路由模式匹配多种写法
    ROUTE_PATTERNS = [
        r'@(?:app|router|api)\.(get|post|put|delete|patch)\s*\(\s*(["\'])(.*?)\2',
        r'@(?:app|router|api)\.(get|post|put|delete|patch)\s*\(\s*(.*?)\s*[,)]',
    ]

    def detect(self, code: str) -> bool:
        """检测是否是 FastAPI 代码"""
        for pattern in self.DETECT_PATTERNS:
            if re.search(pattern, code):
                return True
        return False

    def parse(self, code: str, source_file: Optional[str] = None) -> ParseResult:
        """解析 FastAPI 代码"""
        # 尝试多种模式匹配路由
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
            return ParseResult.fail("无法找到路由定义，请确保代码包含 @app.get/post 装饰器")

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

        # 默认成功响应
        if not api_info.responses:
            api_info.responses.append(ResponseInfo(
                status_code=200,
                description="成功",
                example_json='{\n  "code": 200,\n  "message": "success",\n  "data": {}\n}'
            ))

        # 从文档字符串提取描述
        docstring = self._extract_docstring(code)
        if docstring:
            api_info.description = docstring

        return ParseResult.ok(api_info)

    def _extract_api_name(self, code: str, path: str) -> str:
        """提取接口名称"""
        # 从函数名提取
        func_match = re.search(r'def\s+(\w+)\s*\(', code)
        if func_match:
            func_name = func_match.group(1)
            readable = func_name.replace('_', ' ').title()
            return readable

        # 从路径提取
        if path:
            name = path.strip('/').replace('-', ' ').replace('_', ' ').replace('{', '').replace('}', '').title()
            if name:
                return name

        return "Unknown API"

    def _extract_docstring(self, code: str) -> Optional[str]:
        """提取文档字符串"""
        func_match = re.search(r'def\s+\w+\s*\(.*?\):\s*(?:#.*\n)?\s*("""|\'\'\')(.*?)\1', code, re.DOTALL)
        if func_match:
            docstring = func_match.group(2).strip()
            first_line = docstring.split('\n')[0].strip()
            return first_line
        return None

    def _parse_parameters(self, code: str) -> List[Parameter]:
        """解析参数"""
        parameters = []

        # FastAPI 路径参数 {param}
        path_params = re.findall(r'\{(\w+)\}', code)
        for param_name in path_params:
            parameters.append(Parameter(
                name=param_name,
                type_='string',
                required=True,
                location=ParameterLocation.PATH
            ))

        # 从函数参数提取类型提示
        # 模式: param_name: Type = ...
        param_matches = re.findall(r'(\w+):\s*([\w\[\]]+)', code)
        for param_name, type_name in param_matches:
            if param_name in ['self', 'cls']:
                continue
            if 'Request' in type_name or 'Depends' in type_name:
                continue

            # 判断是否必需
            required = '= ' not in param_name + ': ' + type_name
            required = not required  # 反转逻辑: 有默认值就是不需要

            # 判断参数位置
            # FastAPI 中，路径参数已经提取，query参数是函数参数，body需要看是否有 Body/Pydantic 模型
            location = ParameterLocation.QUERY

            if 'body' in param_name.lower() or 'data' in param_name.lower():
                location = ParameterLocation.BODY

            parameters.append(Parameter(
                name=param_name,
                type_=type_name,
                required=required,
                location=location
            ))

        return parameters
