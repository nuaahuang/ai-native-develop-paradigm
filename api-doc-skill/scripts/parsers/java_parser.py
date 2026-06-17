import re
from typing import List, Optional
from .base_parser import BaseParser, ParseResult
from scripts.models.api_info import ApiInfo
from scripts.models.parameter import Parameter, ParameterLocation
from scripts.models.response import ResponseInfo


class JavaSpringParser(BaseParser):
    """Java Spring Boot 解析器"""

    DETECT_PATTERNS = [
        r'@GetMapping',
        r'@PostMapping',
        r'@PutMapping',
        r'@DeleteMapping',
        r'@RequestMapping',
        r'@RestController',
        r'SpringBoot',
    ]

    # 多种匹配模式，支持不同写法
    MAPPING_PATTERNS = [
        r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\s*\(\s*value\s*=\s*(["\'])(.*?)\2',
        r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\s*\(\s*(["\'])(.*?)\2',
        r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\s*\(\s*(.*?)\s*[,)]',
    ]

    def detect(self, code: str) -> bool:
        """检测是否是 Java Spring 代码"""
        for pattern in self.DETECT_PATTERNS:
            if re.search(pattern, code):
                return True
        return False

    def parse(self, code: str, source_file: Optional[str] = None) -> ParseResult:
        """解析 Java Spring 代码"""
        # 尝试多种模式匹配
        http_method, path = None, None
        for pattern in self.MAPPING_PATTERNS:
            match = re.search(pattern, code, re.DOTALL)
            if match:
                annotation = match.group(1)
                # 从注解名提取 HTTP 方法
                if annotation == 'RequestMapping':
                    # 查找 method 属性
                    method_match = re.search(r'method\s*=\s*RequestMethod\.(\w+)', code)
                    if method_match:
                        http_method = self.extract_http_method(method_match.group(1))
                    else:
                        http_method = 'GET'
                else:
                    # @GetMapping -> GET
                    http_method = self.extract_http_method(annotation.replace('Mapping', ''))

                if len(match.groups()) >= 3 and match.group(3):
                    path = match.group(3)
                else:
                    path = match.group(2)
                break

        if not path:
            return ParseResult.fail("无法找到映射注解，请确保代码包含 @GetMapping/@PostMapping 等注解")

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

        # 从 JavaDoc 提取描述
        javadoc = self._extract_javadoc(code)
        if javadoc:
            api_info.description = javadoc

        return ParseResult.ok(api_info)

    def _extract_api_name(self, code: str, path: str) -> str:
        """提取接口名称"""
        # 从方法名提取
        method_match = re.search(r'public\s+\w+\s+(\w+)\s*\(', code)
        if not method_match:
            method_match = re.search(r'(\w+)\s*\(\s*.*?\s*\)\s*\{', code)
        if method_match:
            method_name = method_match.group(1)
            readable = method_name.replace('_', ' ').title()
            return readable

        # 从路径提取
        if path:
            name = path.strip('/').replace('-', ' ').replace('_', ' ').replace('{', '').replace('}', '').title()
            if name:
                return name

        return "Unknown API"

    def _extract_javadoc(self, code: str) -> Optional[str]:
        """提取 JavaDoc"""
        javadoc_match = re.search(r'/\*\*\s*(.*?)\s*\*/', code, re.DOTALL)
        if javadoc_match:
            content = javadoc_match.group(1).strip()
            # 去除 * 前缀，取第一行
            lines = content.split('\n')
            first_line = lines[0].strip().lstrip('* ').strip()
            if first_line:
                return first_line
            # 尝试第二行
            for line in lines[1:]:
                cleaned = line.strip().lstrip('* ').strip()
                if cleaned:
                    return cleaned
        return None

    def _parse_parameters(self, code: str) -> List[Parameter]:
        """解析参数"""
        parameters = []

        # @PathVariable
        path_params = re.findall(r'@PathVariable\s+(?:\w+\s+)?(\w+)', code)
        for param_name in path_params:
            parameters.append(Parameter(
                name=param_name,
                type_='String',
                required=True,
                location=ParameterLocation.PATH
            ))

        # @RequestParam
        query_params = re.findall(r'@RequestParam\s+(?:\w+\s+)?(\w+)', code)
        for param_name in query_params:
            # 检查是否必需
            required = 'required = false' not in code
            parameters.append(Parameter(
                name=param_name,
                type_='String',
                required=required,
                location=ParameterLocation.QUERY
            ))

        # @RequestBody
        if '@RequestBody' in code:
            # 提取类型
            body_match = re.search(r'@RequestBody\s+(\w+)\s+(\w+)', code)
            type_name = 'object'
            param_name = 'body'
            if body_match:
                type_name = body_match.group(1)
                param_name = body_match.group(2)
            parameters.append(Parameter(
                name=param_name,
                type_=type_name,
                required=True,
                description='请求体',
                location=ParameterLocation.BODY
            ))

        # URL 路径参数 {param}
        path_params = re.findall(r'\{(\w+)\}', code)
        for param_name in path_params:
            # 避免重复添加
            if param_name not in [p.name for p in parameters]:
                parameters.append(Parameter(
                    name=param_name,
                    type_='String',
                    required=True,
                    location=ParameterLocation.PATH
                ))

        return parameters
