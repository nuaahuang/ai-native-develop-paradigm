from typing import List, Dict, Optional
from urllib.parse import urljoin
from scripts.models.api_info import ApiInfo
from scripts.models.parameter import Parameter, ParameterLocation


class ExampleGenerator:
    """测试示例生成器"""

    def generate_curl(self, api: ApiInfo, base_url: str = "http://localhost:8000") -> str:
        """生成 curl 示例"""
        full_url = urljoin(base_url, api.full_path)

        # 替换路径参数占位符
        for param in api.parameters:
            if param.location == ParameterLocation.PATH:
                example = param.example or f'example_{param.name}'
                full_url = full_url.replace(f'{{{param.name}}}', example)

        lines = [f"curl -X {api.http_method} {full_url}"]

        # 添加 header
        lines.append('  -H "Content-Type: application/json"')
        lines.append('  -H "Authorization: Bearer <your-token>"')

        # 添加请求体
        body_params = [p for p in api.parameters if p.location == ParameterLocation.BODY]
        if body_params:
            body_dict = {}
            for p in body_params:
                example = p.example or f'"example_{p.name}"'
                if p.type_.lower() in ['int', 'integer']:
                    example = p.example or '1'
                elif p.type_.lower() in ['bool', 'boolean']:
                    example = p.example or 'true'
                body_dict[p.name] = example

            import json
            body_str = json.dumps(body_dict, indent=4).replace('\n', '\n  ')
            lines.append(f'  -d \'{body_str}\'')

        return ' \\\n'.join(lines)

    def generate_python(self, api: ApiInfo, base_url: str = "http://localhost:8000") -> str:
        """生成 Python requests 示例"""
        full_url = urljoin(base_url, api.full_path)

        # 替换路径参数
        for param in api.parameters:
            if param.location == ParameterLocation.PATH:
                example = param.example or f'example_{param.name}'
                full_url = full_url.replace(f'{{{param.name}}}', example)

        lines = [
            "import requests",
            "",
            f"url = '{full_url}'",
            "",
        ]

        # headers
        lines.append("headers = {")
        lines.append("    'Content-Type': 'application/json',")
        lines.append("    'Authorization': 'Bearer <your-token>',")
        lines.append("}")
        lines.append("")

        # 参数
        query_params = [p for p in api.parameters if p.location == ParameterLocation.QUERY]
        body_params = [p for p in api.parameters if p.location == ParameterLocation.BODY]

        if query_params:
            lines.append("params = {")
            for p in query_params:
                example = p.example or f"'example_{p.name}'"
                if p.type_.lower() in ['int', 'integer']:
                    example = p.example or '1'
                lines.append(f"    '{p.name}': {example},")
            lines.append("}")
            lines.append("")

        if body_params:
            lines.append("data = {")
            for p in body_params:
                example = p.example or f"'example_{p.name}'"
                if p.type_.lower() in ['int', 'integer']:
                    example = p.example or '1'
                elif p.type_.lower() in ['bool', 'boolean']:
                    example = p.example or 'True'
                lines.append(f"    '{p.name}': {example},")
            lines.append("}")
            lines.append("")

        # 请求
        lines.append(f"response = requests.{api.http_method.lower()}(")
        lines.append(f"    url,")
        if query_params:
            lines.append(f"    params=params,")
        if body_params:
            lines.append(f"    json=data,")
        lines.append(f"    headers=headers,")
        lines.append(")")
        lines.append("")
        lines.append("print(response.json())")

        return '\n'.join(lines)

    def generate_javascript(self, api: ApiInfo, base_url: str = "http://localhost:8000") -> str:
        """生成 JavaScript fetch 示例"""
        full_url = urljoin(base_url, api.full_path)

        # 替换路径参数
        for param in api.parameters:
            if param.location == ParameterLocation.PATH:
                example = param.example or f'example_{param.name}'
                full_url = full_url.replace(f'{{{param.name}}}', example)

        lines = [f"const url = '{full_url}';"]
        lines.append("")

        # options
        lines.append("const options = {")
        lines.append(f"    method: '{api.http_method}',")
        lines.append("    headers: {")
        lines.append("        'Content-Type': 'application/json',")
        lines.append("        'Authorization': 'Bearer <your-token>',")
        lines.append("    },")

        body_params = [p for p in api.parameters if p.location == ParameterLocation.BODY]
        if body_params:
            lines.append("    body: JSON.stringify({")
            for p in body_params:
                example = p.example or f"'example_{p.name}'"
                if p.type_.lower() in ['int', 'integer']:
                    example = p.example or '1'
                elif p.type_.lower() in ['bool', 'boolean']:
                    example = p.example or 'true'
                lines.append(f"        {p.name}: {example},")
            lines.append("    }),")

        lines.append("};")
        lines.append("")

        lines.append("fetch(url, options)")
        lines.append("    .then(response => response.json())")
        lines.append("    .then(data => console.log(data))")
        lines.append("    .catch(error => console.error(error));")

        return '\n'.join(lines)

    def generate_test_suggestions(self, api: ApiInfo) -> List[str]:
        """生成测试用例建议"""
        suggestions = []

        # 必填参数缺失测试
        required_params = [p for p in api.parameters if p.required]
        optional_params = [p for p in api.parameters if not p.required]

        if required_params:
            suggestions.append(f"正常请求 - 携带所有必填参数")
            suggestions.append(f"异常测试 - 缺失必填参数 {required_params[0].name}，验证错误处理")

        # 参数边界测试
        for param in required_params:
            if param.type_.lower() in ['int', 'integer', 'long']:
                suggestions.append(f"边界测试 - {param.name} 测试最小值、最大值、零值")
            if param.type_.lower() == 'string':
                suggestions.append(f"边界测试 - {param.name} 测试空字符串、超长字符串")

        # 鉴权测试
        suggestions.append("鉴权测试 - 不带 Token、Token 非法，验证 401 响应")

        # 路径参数测试
        path_params = [p for p in api.parameters if p.location == ParameterLocation.PATH]
        if path_params:
            suggestions.append(f"路径参数测试 - 测试不存在的 {path_params[0].name} 值，验证 404 响应")

        return suggestions

    def generate_all_examples(self, api: ApiInfo, base_url: str = "http://localhost:8000") -> Dict[str, str]:
        """生成所有示例"""
        examples = {}
        examples['curl'] = self.generate_curl(api, base_url)
        examples['python'] = self.generate_python(api, base_url)
        examples['javascript'] = self.generate_javascript(api, base_url)
        return examples

    def add_examples_to_api(self, api: ApiInfo, base_url: str = "http://localhost:8000"):
        """添加示例到 API 对象"""
        api.examples = self.generate_all_examples(api, base_url)
        api.test_suggestions = self.generate_test_suggestions(api)
