"""
对话式驱动 - 适配 AI 编辑器调用
用户在编辑器选中代码，对话中输入命令，skill 直接生成文档
"""

import os
from typing import Optional, List
from dataclasses import dataclass

from scripts.models.api_info import ApiInfo
from scripts.config import Config, OutputConfig
from scripts.validation.input_validator import InputValidator
from scripts.document.markdown_parser import MarkdownDocumentParser
from scripts.document.markdown_generator import MarkdownGenerator
from scripts.exporters.openapi_exporter import OpenApiExporter
from scripts.examples.example_generator import ExampleGenerator
from scripts.parsers.base_parser import ParseResult
from scripts.parsers import (
    DjangoRestFrameworkParser,
    FlaskParser,
    FastAPIParser,
    JavaSpringParser,
    ExpressParser,
    GoGinParser,
    PlainTextParser,
)


@dataclass
class SkillRequest:
    """Skill 请求"""
    code: str                    # 选中的代码
    output_file: str            # 输出文档路径
    api_name: Optional[str]      # 接口名称
    export_openapi: Optional[str] # 导出 OpenAPI 路径
    source_file: Optional[str] = None  # 选中代码所属文件


@dataclass
class SkillResponse:
    """Skill 响应"""
    success: bool
    message: str
    api_count: int = 0
    openapi_exported: bool = False
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class ApiDocSkillDialog:
    """对话式驱动主类"""

    def __init__(self):
        self.config = Config()
        self.parsers = [
            DjangoRestFrameworkParser(),
            FlaskParser(),
            FastAPIParser(),
            JavaSpringParser(),
            ExpressParser(),
            GoGinParser(),
            PlainTextParser(),
        ]
        self.markdown_parser = MarkdownDocumentParser()
        self.example_generator = ExampleGenerator()
        self.input_validator = InputValidator()

    def detect_parser(self, code: str):
        """检测使用哪个解析器"""
        for parser in self.parsers:
            if parser.detect(code):
                return parser
        return None

    def parse_code(self, code: str, source_file: str = None) -> ParseResult:
        """解析代码"""
        parser = self.detect_parser(code)
        if not parser:
            return ParseResult.fail("无法识别代码框架，请检查代码格式")
        return parser.parse(code, source_file)

    def execute(self, request: SkillRequest) -> SkillResponse:
        """执行 Skill 请求"""
        output_config = OutputConfig(
            output_file=request.output_file,
            api_name=request.api_name,
            export_openapi=request.export_openapi,
        )
        self.config.output = output_config

        return self._execute_single(request, output_config)

    def _execute_single(self, request: SkillRequest, output_config: OutputConfig) -> SkillResponse:
        """处理单接口请求"""
        val_result = self.input_validator.validate_code(request.code)
        if not val_result.is_valid():
            return SkillResponse(
                success=False,
                message='\n'.join(val_result.get_error_messages()),
                errors=val_result.get_error_messages()
            )

        val_result = self.input_validator.validate_output_path(output_config.output_file)
        if not val_result.is_valid():
            return SkillResponse(
                success=False,
                message='\n'.join(val_result.get_error_messages()),
                errors=val_result.get_error_messages()
            )

        result = self.parse_code(request.code, request.source_file)
        if not result.success or not result.api_info:
            return SkillResponse(
                success=False,
                message=result.message,
                errors=[result.message]
            )

        api = result.api_info
        if output_config.api_name:
            api.name = output_config.api_name

        self.example_generator.add_examples_to_api(api)

        existing_apis = self._read_existing_apis(output_config.output_file)

        generator = MarkdownGenerator(self.config)
        all_apis = generator.assign_sequences(existing_apis, [api])

        content = generator.generate_full_document(all_apis)

        saved = self._save_document(content, output_config.output_file)
        if not saved:
            return SkillResponse(
                success=False,
                message=f"无法保存文档到 {output_config.output_file}",
            )

        openapi_exported = False
        if output_config.export_openapi:
            exporter = OpenApiExporter(title=f"{api.name} API")
            exporter.save([api], output_config.export_openapi)
            openapi_exported = True

        return SkillResponse(
            success=True,
            message=self._format_success_message(len(all_apis), output_config, openapi_exported),
            api_count=len(all_apis),
            openapi_exported=openapi_exported,
        )

    def _read_existing_apis(self, output_file: str) -> List[ApiInfo]:
        """读取已有接口"""
        if not os.path.exists(output_file):
            return []
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            parsed = self.markdown_parser.parse(content)
            return parsed.interfaces
        except Exception:
            return []

    def _save_document(self, content: str, output_file: str) -> bool:
        """保存文档"""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False

    def _format_success_message(self, count: int, config: OutputConfig, openapi_exported: bool) -> str:
        """格式化成功消息"""
        msg = f"✅ 文档已生成并保存到 `{config.output_file}`\n"
        msg += f"   当前文档共 {count} 个接口\n"
        if openapi_exported:
            msg += f"   OpenAPI 已导出到 {config.export_openapi}\n"
        return msg


def parse_command_args(args_text: str) -> SkillRequest:
    """从对话命令参数解析请求"""
    request = SkillRequest(
        code="",
        output_file="",
    )

    import re
    patterns = {
        'output': r'--output\s*=\s*["\']?([^"\']+)["\']?',
        'api-name': r'--api-name\s*=\s*["\']?([^"\']+)["\']?',
        'export-openapi': r'--export-openapi\s*=\s*["\']?([^"\']+)["\']?',
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, args_text)
        if match:
            value = match.group(1).strip()
            setattr(request, key.replace('-', '_'), value)

    return request