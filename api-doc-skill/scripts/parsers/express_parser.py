import re
from typing import List, Optional
from .base_parser import BaseParser, ParseResult
from scripts.models.api_info import ApiInfo
from scripts.models.parameter import Parameter, ParameterLocation
from scripts.models.response import ResponseInfo


class ExpressParser(BaseParser):
    """Node.js Express 框架解析器"""

    DETECT_PATTERNS = [
        r'app\.get',
        r'app\.post',
        r'app\.put',
        r'app\.delete',
        r'router\.get',
        r'router\.post',
        r'express',
        'Express',
    ]

    ROUTE_PATTERNS = [
        r'(?:app|router|router)\.(get|post|put|delete|patch)\s*\(\s*(["\'])(.*?)\2',
        r'(?:app|router|router)\.(get|post|put|delete|patch)\s*\(\s*(.*?)\s*[,)]',
    ]

    def detect(self, code: str) -> bool:
        """检测是否是 Express 代码"""
        for pattern in self.DETECT_PATTERNS:
            if re.search(pattern, code):
                return True
        return False

    def parse(self, code: str, source_file: Optional[str] = None) -> ParseResult:
        """解析 Express 代码"""
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
            return ParseResult.fail("无法找到路由定义，请确保代码包含 app.get/post 调用")

        # 处理 Express :param 格式
        path = self.cleanup_path(path)
        # Express :id -> {id}
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
        # 寻找路由处理函数名
        # app.get(path, (req, res) => { ... }) 或 app.get(path, handlerName)
        handler_match = re.search(r',\s*(\w+)\s*\)?\s*(?:=>|{)', code)
        if not handler_match:
            handler_match = re.search(r',\s*function\s+(\w+)\s*\(', code)
        if handler_match:
            handler_name = handler_match.group(1)
            if not handler_name.startswith('('):
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
        # 多行注释
        comment_match = re.search(r'/\*\s*(.*?)\s*\*/', code, re.DOTALL)
        if comment_match:
            content = comment_match.group(1).strip()
            first_line = content.split('\n')[0].strip().lstrip('* ').strip()
            if first_line:
                return first_line

        # 单行注释
        comment_match = re.search(r'//\s*(.+)', code)
        if comment_match:
            return comment_match.group(1).strip()

        return None

    def _parse_parameters(self, code: str) -> List[Parameter]:
        """解析参数"""
        parameters = []

        # Express 路径参数 /:id -> {id} 已经转换
        path_params = re.findall(r'{(\w+)}', path) if 'path' in locals() else []
        for param_name in path_params:
            parameters.append(Parameter(
                name=param_name,
                type_='string',
                required=True,
                location=ParameterLocation.PATH
            ))

        # 查找 req.params.xxx
        query_params = re.findall(r'req\.query\.(\w+)', code)
        for param_name in query_params:
            parameters.append(Parameter(
                name=param_name,
                type_='any',
                required=False,
                location=ParameterLocation.QUERY
            ))

        # 查找 req.params.xxx (路径参数，虽然已经提取，但补充)
        extra_path_params = re.findall(r'req\.params\.(\w+)', code)
        for param_name in extra_path_params:
            if param_name not in [p.name for p in parameters]:
                parameters.append(Parameter(
                    name=param_name,
                    type_='any',
                    required=True,
                    location=ParameterLocation.PATH
                ))

        # 查找 req.body - 请求体
        if 'req.body' in code:
            parameters.append(Parameter(
                name='body',
                type_='object',
                required=True,
                description='JSON 请求体',
                location=ParameterLocation.BODY
            ))

        return parameters
