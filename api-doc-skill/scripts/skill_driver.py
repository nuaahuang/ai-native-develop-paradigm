#!/usr/bin/env python3
"""
api-doc-skill 主驱动
自动生成和更新 Markdown 格式接口文档
"""

import argparse
import os
import sys
from typing import List

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
from scripts.exporters.openapi_exporter import OpenApiExporter
from scripts.examples.example_generator import ExampleGenerator
from scripts.validation.input_validator import InputValidator


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

    def process_single(self, code: str, output_config: OutputConfig, source_file: str = None) -> (List[ApiInfo], str):
        """处理单个接口"""
        val_result = self.input_validator.validate_code(code)
        if not val_result.is_valid():
            return [], '\n'.join(val_result.get_error_messages())

        val_result = self.input_validator.validate_output_path(output_config.output_file)
        if not val_result.is_valid():
            return [], '\n'.join(val_result.get_error_messages())

        result = self.parse_code(code, source_file)
        if not result.success or not result.api_info:
            return [], result.message

        api = result.api_info
        if output_config.api_name:
            api.name = output_config.api_name

        self.example_generator.add_examples_to_api(api)

        existing_apis = self._read_existing_apis(output_config.output_file)

        all_apis = self.markdown_generator.assign_sequences(existing_apis, [api])

        content = self.markdown_generator.generate_full_document(all_apis)

        return all_apis, content

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
    parser.add_argument('--export-openapi', help='导出 OpenAPI 文件路径')
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    config = Config()

    config.output = OutputConfig(
        output_file=args.output,
        api_name=args.api_name,
        export_openapi=args.export_openapi,
    )

    skill = ApiDocSkill(config)

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

    if args.export_openapi:
        exported = skill.export_openapi(apis, args.export_openapi)
        if exported:
            print(f"OpenAPI 已导出到: {args.export_openapi}")


if __name__ == '__main__':
    main()