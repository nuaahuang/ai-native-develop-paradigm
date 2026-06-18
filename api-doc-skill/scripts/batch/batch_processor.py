from typing import List, Tuple, Dict
from scripts.parsers.base_parser import BaseParser, ParseResult
from scripts.parsers import (
    JavaSpringParser,
    FastAPIParser,
    DjangoRestFrameworkParser,
    FlaskParser,
    ExpressParser,
    GoGinParser,
    PlainTextParser,
)
from scripts.models.api_info import ApiInfo
from scripts.config import Config


class BatchProcessor:
    """批量处理器"""

    def __init__(self):
        # 注册所有解析器，按优先级尝试
        self.parsers: List[BaseParser] = [
            DjangoRestFrameworkParser(),
            FlaskParser(),
            FastAPIParser(),
            JavaSpringParser(),
            ExpressParser(),
            GoGinParser(),
            PlainTextParser(),
        ]

    def detect_parser(self, code: str, file_path: str) -> BaseParser:
        """检测使用哪个解析器"""
        ext = file_path.split('.')[-1].lower() if '.' in file_path else ''

        # 根据扩展名优先尝试对应解析器
        if ext == 'py':
            # Python 文件，先试 Django，再试 Flask，再试 FastAPI
            for parser in [DjangoRestFrameworkParser(), FlaskParser(), FastAPIParser(), PlainTextParser()]:
                if parser.detect(code):
                    return parser
        elif ext in ['java']:
            parser = JavaSpringParser()
            if parser.detect(code):
                return parser
        elif ext in ['js', 'ts']:
            parser = ExpressParser()
            if parser.detect(code):
                return parser
        elif ext in ['go']:
            parser = GoGinParser()
            if parser.detect(code):
                return parser
        elif ext in ['proto']:
            # TODO: gRPC parser
            pass
        elif ext in ['graphql', 'gql']:
            # TODO: GraphQL parser
            pass

        # 通用检测
        for parser in self.parsers:
            if parser.detect(code):
                return parser

        return PlainTextParser()

    def process_file(self, file_path: str, content: str) -> List[ApiInfo]:
        """处理单个文件，提取所有找到的接口"""
        results: List[ApiInfo] = []

        # 按行分割，尝试分段找到多个接口定义
        # 这是简单分割，实际解析器会处理完整函数
        lines = content.split('\n')
        current_block = []
        in_function = False

        for line in lines:
            stripped = line.strip()

            # 检测函数/方法开始
            if stripped.startswith('def ') or \
               stripped.startswith('public ') or \
               stripped.startswith('private ') or \
               ('func ' in stripped and '(' in stripped) or \
               (stripped.startswith('@') and len(stripped) > 1):
                if in_function and current_block:
                    # 处理之前的块
                    block_content = '\n'.join(current_block)
                    api = self._try_parse(block_content, file_path)
                    if api:
                        results.append(api)
                    current_block = []
                in_function = True

            if in_function:
                current_block.append(line)

        # 处理最后一个块
        if current_block:
            block_content = '\n'.join(current_block)
            api = self._try_parse(block_content, file_path)
            if api:
                results.append(api)

        # 如果没有找到任何接口，尝试整块解析
        if not results:
            api = self._try_parse(content, file_path)
            if api:
                results.append(api)

        return results

    def _try_parse(self, code: str, file_path: str) -> ApiInfo:
        """尝试解析代码，如果成功返回 ApiInfo"""
        parser = self.detect_parser(code, file_path)
        result = parser.parse(code, file_path)
        if result.success and result.api_info:
            return result.api_info
        return None

    def process_all(self, files: List[Tuple[str, str]]) -> List[ApiInfo]:
        """处理所有文件"""
        all_apis: List[ApiInfo] = []
        for file_path, content in files:
            apis = self.process_file(file_path, content)
            all_apis.extend(apis)
        return all_apis

    def get_statistics(self, apis: List[ApiInfo]) -> Dict[str, int]:
        """获取统计信息"""
        by_method: Dict[str, int] = {}

        for api in apis:
            method = api.http_method
            by_method[method] = by_method.get(method, 0) + 1

        return {
            'total': len(apis),
            'by_method': by_method,
        }