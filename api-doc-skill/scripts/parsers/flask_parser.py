import re
from typing import List, Optional
from .base_parser import BaseParser, ParseResult
from scripts.models.api_info import ApiInfo
from scripts.models.parameter import Parameter, ParameterLocation
from scripts.models.response import ResponseInfo


class FlaskParser(BaseParser):
    """Flask 框架解析器"""

    # 检测特征关键词
    DETECT_PATTERNS = [
        r'@app\.route',
        r'@app\.(get|post|put|delete|patch)',  # Flask 2.0+ 简写
        r'@.*\.route',  # blueprint
        r'@.*\.(get|post|put|delete|patch)',  # blueprint 简写
        r'from flask',
        r'Flask\(',
        r'Blueprint\(',
    ]

    # 路由模式
    ROUTE_PATTERN = r'@(?:app|.*?blueprint|.*_bp)\.route\s*\(\s*(["\'])(.*?)\1\s*'
    ROUTE_PATTERN_ALT = r'@\w+\.route\s*\(\s*(["\'])(.*?)\1\s*'
    # Flask 2.0+ 简写形式 @app.get("/path")
    ROUTE_PATTERN_METHOD = r'@(\w+)\.(get|post|put|delete|patch)\s*\(\s*(["\'])(.*?)\3\s*'
    METHODS_PATTERN = r'methods\s*=\s*\[(.*?)\]'

    def detect(self, code: str) -> bool:
        """检测是否是 Flask 代码"""
        for pattern in self.DETECT_PATTERNS:
            if re.search(pattern, code):
                return True
        return False

    def parse(self, code: str, source_file: Optional[str] = None) -> ParseResult:
        """解析 Flask 代码"""
        # 提取路由路径
        path_match = re.search(self.ROUTE_PATTERN, code, re.DOTALL)
        http_method = None
        
        # 尝试匹配 Flask 2.0+ 简写形式 @app.get("/path")
        if not path_match:
            method_match = re.search(self.ROUTE_PATTERN_METHOD, code, re.DOTALL)
            if method_match:
                http_method = method_match.group(2).upper()
                path = method_match.group(4)
                path = self.cleanup_path(path)
            else:
                path_match = re.search(self.ROUTE_PATTERN_ALT, code, re.DOTALL)
                if not path_match:
                    return ParseResult.fail("无法找到 @app.route 装饰器，请确保代码包含完整路由定义")
                path = path_match.group(2)
                path = self.cleanup_path(path)
        else:
            path = path_match.group(2)
            path = self.cleanup_path(path)

        # 提取 HTTP 方法（如果还没从简写形式获取）
        if http_method is None:
            http_method = self._extract_methods(code)

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

    def _extract_methods(self, code: str) -> str:
        """提取 HTTP 方法"""
        methods_match = re.search(self.METHODS_PATTERN, code, re.DOTALL)
        if methods_match:
            methods_str = methods_match.group(1)
            methods = re.findall(r'["\'](\w+?)["\']', methods_str)
            if methods:
                return self.extract_http_method(methods[0])

        # 默认 GET
        return 'GET'

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
            name = path.strip('/').replace('-', ' ').replace('_', ' ').title()
            if name:
                return name

        return "Unknown API"

    def _extract_docstring(self, code: str) -> Optional[str]:
        """提取文档字符串"""
        func_match = re.search(r'def\s+\w+\s*\(.*?\):\s*(?:#.*\n)?\s*("""|\'\'\')(.*?)\1', code, re.DOTALL)
        if func_match:
            docstring = func_match.group(2).strip()
            # 取第一行
            first_line = docstring.split('\n')[0].strip()
            return first_line
        return None

    def _parse_parameters(self, code: str) -> List[Parameter]:
        """解析参数"""
        parameters = []

        # Flask 路径参数 <variable>
        path_params = re.findall(r'<(?:[^:]+:)?(\w+)>', code)
        for param_name in path_params:
            parameters.append(Parameter(
                name=param_name,
                type_='string',
                required=True,
                location=ParameterLocation.PATH
            ))

        # request.args.get 提取查询参数
        query_params = re.findall(r'request\.args\.get\([\'"](\w+)[\'"]', code)
        for param_name in query_params:
            parameters.append(Parameter(
                name=param_name,
                type_='string',
                required=False,
                location=ParameterLocation.QUERY
            ))

        # request.form 提取表单参数
        if 'request.form' in code:
            form_params = re.findall(r'request\.form\.get\([\'"](\w+)[\'"]', code)
            for param_name in form_params:
                parameters.append(Parameter(
                    name=param_name,
                    type_='string',
                    required=False,
                    location=ParameterLocation.FORM
                ))

        # request.get_json() 有请求体
        if 'request.get_json' in code or 'request.json' in code:
            parameters.append(Parameter(
                name='body',
                type_='object',
                required=True,
                description='JSON 请求体',
                location=ParameterLocation.BODY
            ))

        # 类型提示提取参数
        type_hint_params = self._parse_type_hints(code)
        parameters.extend(type_hint_params)

        return parameters

    def _parse_type_hints(self, code: str) -> List[Parameter]:
        """从类型提示提取参数"""
        parameters = []
        # 匹配函数定义中的类型提示
        # 只匹配函数定义行内部，避免匹配路由路径中的 <int:user_id>
        # 查找 def func_name(..., param: Type, ...):
        # 先找到函数定义行
        func_match = re.search(r'def\s+\w+\s*\((.*?)\):', code, re.DOTALL)
        if func_match:
            params_str = func_match.group(1)
            # 在参数列表中匹配
            param_matches = re.findall(r'(\w+):\s*(\w+)', params_str)
            for param_name, type_name in param_matches:
                if param_name in ['self', 'cls', 'request']:
                    continue
                # 检查是否有默认值 (optional)
                if f'{param_name}: {type_name} =' in params_str:
                    required = False
                else:
                    required = True
                parameters.append(Parameter(
                    name=param_name,
                    type_=type_name,
                    required=required,
                    location=ParameterLocation.QUERY
                ))
        return parameters
