import re
from typing import List, Optional
from .base_parser import BaseParser, ParseResult
from scripts.models.api_info import ApiInfo
from scripts.models.parameter import Parameter, ParameterLocation
from scripts.models.response import ResponseInfo


class PlainTextParser(BaseParser):
    """纯文本 URL 解析器"""

    # 匹配模式: GET /path
    PLAIN_PATTERN = r'^([A-Za-z]+)\s+(\/[\w\/\-{}:]+)'

    def detect(self, code: str) -> bool:
        """检测是否是纯文本 URL"""
        code = code.strip()
        # 第一行是否是 METHOD /path 格式
        first_line = code.split('\n')[0].strip()
        match = re.match(self.PLAIN_PATTERN, first_line)
        return match is not None

    def parse(self, code: str, source_file: Optional[str] = None) -> ParseResult:
        """解析纯文本 URL"""
        lines = code.strip().split('\n')
        first_line = lines[0].strip()

        match = re.match(self.PLAIN_PATTERN, first_line)
        if not match:
            return ParseResult.fail("无法解析纯文本格式，期望格式: METHOD /path")

        http_method = self.extract_http_method(match.group(1))
        path = match.group(2)
        path = self.cleanup_path(path)

        # 转换占位符格式: :id -> {id}
        path = re.sub(r':(\w+)', r'{\1}', path)

        # 提取接口名称 - 从路径最后一段
        api_name = self._extract_api_name(path)

        # 检查后续行是否有名称
        if len(lines) > 1:
            second_line = lines[1].strip()
            if second_line and not second_line.startswith('|') and not second_line.startswith('{'):
                api_name = second_line

        # 创建 ApiInfo
        api_info = ApiInfo(
            name=api_name,
            http_method=http_method,
            path=path,
            source_file=source_file,
        )

        # 解析参数
        parameters = self._parse_parameters(path)
        api_info.parameters = parameters

        # 默认成功响应
        api_info.responses.append(ResponseInfo(
            status_code=200,
            description="成功",
            example_json='{\n  "code": 200,\n  "message": "success",\n  "data": {}\n}'
        ))

        # 提取描述
        description = self._extract_description(lines)
        if description:
            api_info.description = description

        return ParseResult.ok(api_info)

    def _extract_api_name(self, path: str) -> str:
        """提取接口名称"""
        parts = path.strip('/').split('/')
        # 过滤掉占位符部分
        parts = [p for p in parts if not (p.startswith('{') and p.endswith('}'))]
        if parts:
            last_part = parts[-1]
            return last_part.replace('-', ' ').replace('_', ' ').replace('{', '').replace('}', '').title()

        return "Unknown API"

    def _extract_description(self, lines: List[str]) -> Optional[str]:
        """提取描述"""
        for line in lines[1:]:
            line = line.strip()
            if line and not line.startswith('|') and not line.startswith('{') and not line.startswith('}'):
                return line
        return None

    def _parse_parameters(self, path: str) -> List[Parameter]:
        """解析路径参数"""
        parameters = []
        path_params = re.findall(r'\{(\w+)\}', path)
        for param_name in path_params:
            parameters.append(Parameter(
                name=param_name,
                type_='string',
                required=True,
                location=ParameterLocation.PATH
            ))
        return parameters
