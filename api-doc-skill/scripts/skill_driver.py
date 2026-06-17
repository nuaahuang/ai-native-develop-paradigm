#!/usr/bin/env python3
"""
api-doc-skill 主驱动
自动生成和更新 Markdown 格式接口文档
"""

import argparse
import os
import sys
from datetime import datetime
from typing import List, Optional, Dict

from scripts.models.api_info import ApiInfo
from scripts.config import Config, OutputConfig
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
from scripts.document.markdown_parser import MarkdownDocumentParser
from scripts.document.markdown_generator import MarkdownGenerator
from scripts.document.version_manager import VersionManager
from scripts.batch.scanner import ProjectScanner
from scripts.batch.batch_processor import BatchProcessor
from scripts.exporters.openapi_exporter import OpenApiExporter
from scripts.examples.example_generator import ExampleGenerator
from scripts.validation.input_validator import InputValidator, ValidationResult
from scripts.images.validator import ImageValidator


class ApiDocSkill:
    """api-doc 技能主类"""

    def __init__(self, config: Config):
        self.config = config
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
        self.markdown_generator = MarkdownGenerator(config)
        self.version_manager = VersionManager()
        self.example_generator = ExampleGenerator()
        self.input_validator = InputValidator()

    def detect_parser(self, code: str) -> Optional:
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

    def process_single(self, code: str, output_config: OutputConfig, source_file: str = None) -> (List[ApiInfo], str):
        """处理单个接口"""
        # 输入验证
        val_result = self.input_validator.validate_code(code)
        if not val_result.is_valid():
            return [], '\n'.join(val_result.get_error_messages())

        val_result = self.input_validator.validate_output_path(output_config.output_file)
        if not val_result.is_valid():
            return [], '\n'.join(val_result.get_error_messages())

        # 解析
        result = self.parse_code(code, source_file)
        if not result.success or not result.api_info:
            return [], result.message

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
        all_apis = self.markdown_generator.assign_sequences(existing_apis, [api])

        # 分组
        version_groups = self.version_manager.group_by_version(all_apis)

        # 生成完整文档
        content = self.markdown_generator.generate_full_document(all_apis, version_groups)

        return all_apis, content

    def process_batch(self, scan_dir: str, output_config: OutputConfig) -> (List[ApiInfo], str, Dict):
        """批量处理目录"""
        # 输入验证
        val_result = self.input_validator.validate_scan_dir(scan_dir)
        if not val_result.is_valid():
            return [], '\n'.join(val_result.get_error_messages()), {}

        scanner = ProjectScanner(self.config.scan)
        if output_config.exclude:
            scanner.add_exclude_patterns(output_config.exclude)

        processor = BatchProcessor()

        all_files = list(scanner.scan(scan_dir))
        apis = processor.process_all(all_files, output_config.version)

        if not apis:
            return [], "未找到任何接口，请检查扫描目录和排除配置", {}

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
        all_apis = self.markdown_generator.assign_sequences(existing_apis, apis)

        # 分组
        version_groups = self.version_manager.group_by_version(all_apis)

        # 生成完整文档
        content = self.markdown_generator.generate_full_document(all_apis, version_groups)

        stats = processor.get_statistics(all_apis)

        return all_apis, content, stats

    def _read_existing_apis(self, output_file: str) -> List[ApiInfo]:
        """读取已存在的接口"""
        if not os.path.exists(output_file):
            return []

        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            parsed = self.markdown_parser.parse(content)
            return parsed.interfaces
        except Exception:
            return []

    def save_document(self, content: str, output_file: str) -> bool:
        """保存文档"""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"保存文档失败: {str(e)}")
            return False

    def export_openapi(self, apis: List[ApiInfo], output_path: str, title: str = "API 文档") -> bool:
        """导出 OpenAPI"""
        try:
            # 从输出文件名推断格式
            if output_path.endswith('.yaml') or output_path.endswith('.yml'):
                format = 'yaml'
            else:
                format = 'json'

            exporter = OpenApiExporter(title=title)
            exporter.save(apis, output_path, format)
            return True
        except Exception as e:
            print(f"导出 OpenAPI 失败: {str(e)}")
            return False


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='api-doc-skill: 自动生成接口文档')
    parser.add_argument('--output', required=True, help='输出文档路径')
    parser.add_argument('--api-name', help='接口名称（不指定则自动推断）')
    parser.add_argument('--version', help='API 版本，如 v1, v2')
    parser.add_argument('--scan-dir', help='批量扫描目录，批量生成所有接口')
    parser.add_argument('--exclude', nargs='*', help='额外排除模式')
    parser.add_argument('--export-openapi', help='导出 OpenAPI 文件路径')
    parser.add_argument('--image-format', default='local', help='图片格式: local/base64/url')
    parser.add_argument('--image-upload', help='图片上传目标: wecom/qiniu/oss')
    parser.add_argument('--image-dir', default='images', help='本地图片目录')
    parser.add_argument('--config', help='配置文件路径')
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    # 加载配置
    if args.config:
        config = Config.from_file(args.config)
    else:
        config = Config()

    # 更新配置
    config.output = OutputConfig(
        output_file=args.output,
        api_name=args.api_name,
        version=args.version,
        export_openapi=args.export_openapi,
        scan_dir=args.scan_dir,
        exclude=args.exclude,
    )
    config.image.image_format = args.image_format
    config.image.image_upload = args.image_upload
    config.image.image_dir = args.image_dir

    # 执行
    skill = ApiDocSkill(config)

    if args.scan_dir:
        # 批量扫描模式
        print(f"开始扫描目录: {args.scan_dir}")
        apis, content, stats = skill.process_batch(args.scan_dir, config.output)
        if not apis:
            print(f"错误: {content}")
            sys.exit(1)

        print(f"扫描完成，共找到 {stats['total']} 个接口")
        for version, count in stats.get('by_version', {}).items():
            print(f"  {version}: {count} 个接口")

        saved = skill.save_document(content, args.output)
        if saved:
            print(f"文档已保存到: {args.output}")
        else:
            sys.exit(1)

        # 导出 OpenAPI
        if args.export_openapi:
            exported = skill.export_openapi(apis, args.export_openapi)
            if exported:
                print(f"OpenAPI 已导出到: {args.export_openapi}")
            else:
                sys.exit(1)

    else:
        # 单接口模式，从 stdin 读取代码
        code = sys.stdin.read()
        apis, content = skill.process_single(code, config.output)
        if not apis:
            print(f"错误: {content}")
            sys.exit(1)

        saved = skill.save_document(content, args.output)
        if saved:
            print(f"文档已保存到: {args.output}")
            print(f"共 {len(apis)} 个接口")
        else:
            sys.exit(1)

        # 导出 OpenAPI
        if args.export_openapi:
            exported = skill.export_openapi(apis, args.export_openapi)
            if exported:
                print(f"OpenAPI 已导出到: {args.export_openapi}")


if __name__ == '__main__':
    main()
