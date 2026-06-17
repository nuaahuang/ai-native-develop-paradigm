"""
对话式驱动 - 适配 AI 编辑器调用
用户在编辑器选中代码，对话中输入命令，skill 直接生成文档
"""

import os
import sys
from typing import Optional, List, Dict
from dataclasses import dataclass

from scripts.models.api_info import ApiInfo
from scripts.config import Config, OutputConfig
from scripts.validation.input_validator import InputValidator, ValidationResult
from scripts.batch.scanner import ProjectScanner
from scripts.batch.batch_processor import BatchProcessor
from scripts.document.markdown_parser import MarkdownDocumentParser
from scripts.document.markdown_generator import MarkdownGenerator
from scripts.document.version_manager import VersionManager
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
    code: str                    # 选中的代码（单接口模式）
    output_file: str            # 输出文档路径
    api_name: Optional[str]      # 接口名称
    version: Optional[str]       # API 版本
    scan_dir: Optional[str]      # 批量扫描目录
    exclude: Optional[List[str]] # 额外排除模式
    export_openapi: Optional[str] # 导出 OpenAPI 路径
    image_format: str = 'local'
    image_upload: Optional[str] = None
    image_dir: str = 'images'
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
        self.version_manager = VersionManager()
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
        # 更新配置
        output_config = OutputConfig(
            output_file=request.output_file,
            api_name=request.api_name,
            version=request.version,
            export_openapi=request.export_openapi,
            scan_dir=request.scan_dir,
            exclude=request.exclude,
        )
        self.config.output = output_config
        self.config.image.image_format = request.image_format
        self.config.image.image_upload = request.image_upload
        self.config.image.image_dir = request.image_dir

        # 批量扫描模式
        if request.scan_dir:
            return self._execute_batch(request, output_config)

        # 单接口模式
        return self._execute_single(request, output_config)

    def _execute_single(self, request: SkillRequest, output_config: OutputConfig) -> SkillResponse:
        """处理单接口请求"""
        # 输入验证
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

        # 解析
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
        if output_config.version:
            api.version = output_config.version
            self.version_manager.update_version(output_config.version, api.path)

        # 生成测试示例
        self.example_generator.add_examples_to_api(api)

        # 读取现有文档
        existing_apis = self._read_existing_apis(output_config.output_file)

        # 分配序号
        generator = MarkdownGenerator(self.config)
        all_apis = generator.assign_sequences(existing_apis, [api])

        # 分组
        version_groups = self.version_manager.group_by_version(all_apis)

        # 生成完整文档
        content = generator.generate_full_document(all_apis, version_groups)

        # 保存
        saved = self._save_document(content, output_config.output_file)
        if not saved:
            return SkillResponse(
                success=False,
                message=f"无法保存文档到 {output_config.output_file}",
            )

        # 导出 OpenAPI
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

    def _execute_batch(self, request: SkillRequest, output_config: OutputConfig) -> SkillResponse:
        """处理批量扫描请求"""
        # 输入验证
        val_result = self.input_validator.validate_scan_dir(request.scan_dir)
        if not val_result.is_valid():
            return SkillResponse(
                success=False,
                message='\n'.join(val_result.get_error_messages()),
                errors=val_result.get_error_messages()
            )

        # 扫描
        scanner = ProjectScanner(self.config.scan)
        if output_config.exclude:
            scanner.add_exclude_patterns(output_config.exclude)

        processor = BatchProcessor()
        all_files = list(scanner.scan(request.scan_dir))
        apis = processor.process_all(all_files, output_config.version)

        if not apis:
            return SkillResponse(
                success=False,
                message=f"在目录 {request.scan_dir} 中未找到任何接口，请检查配置",
            )

        # 设置版本
        if output_config.version:
            for api in apis:
                api.version = output_config.version
                self.version_manager.update_version(output_config.version, api.path)

        # 生成测试示例
        for api in apis:
            self.example_generator.add_examples_to_api(api)

        # 读取现有文档
        existing_apis = self._read_existing_apis(output_config.output_file)

        # 分配序号
        generator = MarkdownGenerator(self.config)
        all_apis = generator.assign_sequences(existing_apis, apis)

        # 分组
        version_groups = self.version_manager.group_by_version(all_apis)

        # 生成完整文档
        content = generator.generate_full_document(all_apis, version_groups)

        # 保存
        saved = self._save_document(content, output_config.output_file)
        if not saved:
            return SkillResponse(
                success=False,
                message=f"无法保存文档到 {output_config.output_file}",
            )

        # 导出 OpenAPI
        openapi_exported = False
        if output_config.export_openapi:
            title = os.path.basename(request.output_file).replace('.md', '')
            exporter = OpenApiExporter(title=title)
            exporter.save(all_apis, output_config.export_openapi)
            openapi_exported = True

        # 统计
        stats = processor.get_statistics(all_apis)

        return SkillResponse(
            success=True,
            message=self._format_batch_success(stats, output_config, openapi_exported),
            api_count=stats['total'],
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
        if config.version:
            msg += f"   版本: {config.version}\n"
        if openapi_exported:
            msg += f"   OpenAPI 已导出到 {config.export_openapi}\n"
        return msg

    def _format_batch_success(self, stats: Dict, config: OutputConfig, openapi_exported: bool) -> str:
        """格式化批量成功消息"""
        msg = f"✅ 批量扫描完成，文档已保存到 `{config.output_file}`\n"
        msg += f"   共扫描找到 {stats['total']} 个接口\n"
        if 'by_version' in stats:
            for version, count in stats['by_version'].items():
                if version != 'none':
                    msg += f"   {version}: {count} 个接口\n"
        if openapi_exported:
            msg += f"   OpenAPI 已导出到 {config.export_openapi}\n"
        return msg


def parse_command_args(args_text: str) -> SkillRequest:
    """从对话命令参数解析请求"""
    # args_text 是 "--output=./docs/api.md --api-name=xxx --version=v1" 格式
    request = SkillRequest(
        code="",
        output_file="",
    )

    # 简单解析参数
    import re
    patterns = {
        'output': r'--output\s*=\s*["\']?([^"\']+)["\']?',
        'api-name': r'--api-name\s*=\s*["\']?([^"\']+)["\']?',
        'version': r'--version\s*=\s*["\']?([^"\']+)["\']?',
        'scan-dir': r'--scan-dir\s*=\s*["\']?([^"\']+)["\']?',
        'export-openapi': r'--export-openapi\s*=\s*["\']?([^"\']+)["\']?',
        'image-format': r'--image-format\s*=\s*["\']?([^"\']+)["\']?',
        'image-upload': r'--image-upload\s*=\s*["\']?([^"\']+)["\']?',
        'image-dir': r'--image-dir\s*=\s*["\']?([^"\']+)["\']?',
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, args_text)
        if match:
            value = match.group(1).strip()
            setattr(request, key.replace('-', '_'), value)

    # 解析 exclude
    exclude_match = re.findall(r'--exclude\s+([^\s]+)', args_text)
    if exclude_match:
        request.exclude = exclude_match

    return request
