import re
from dataclasses import dataclass
from typing import List, Optional
from scripts.models.api_info import ApiInfo


@dataclass
class ParsedDocument:
    """解析后的文档"""
    title: str
    interfaces: List[ApiInfo]

    def get_max_sequence(self) -> int:
        """获取最大序号"""
        if not self.interfaces:
            return 0
        return max(api.sequence for api in self.interfaces)

    def find_by_path(self, path: str) -> Optional[ApiInfo]:
        """根据路径查找接口"""
        for api in self.interfaces:
            if api.path == path:
                return api
        return None


class MarkdownDocumentParser:
    """Markdown 文档解析器"""

    # 匹配接口标题: ## 1-接口：名称
    INTERFACE_TITLE_PATTERN = r'^##\s+(\d+)-接口：\s*(.+)$'
    # 基本信息表格
    PATH_PATTERN = r'\*\*接口路径\*\*\s*\|\s*`([A-Z]+)\s+([^`]+)`'
    SEQUENCE_PATTERN = r'\*\*接口序号\*\*\s*\|\s*(\d+)'

    def parse(self, content: str) -> ParsedDocument:
        """解析 Markdown 文档"""
        lines = content.split('\n')
        parsed = ParsedDocument(
            title="接口文档",
            interfaces=[]
        )

        current_api: Optional[ApiInfo] = None

        for i, line in enumerate(lines):
            line = line.rstrip()

            # 一级标题作为文档标题
            if line.startswith('# '):
                parsed.title = line[2:].strip()
                continue

            # 接口标题
            title_match = re.match(self.INTERFACE_TITLE_PATTERN, line)
            if title_match:
                # 如果有当前正在处理的接口，保存它
                if current_api:
                    parsed.interfaces.append(current_api)
                    current_api = None

                sequence = int(title_match.group(1))
                name = title_match.group(2).strip()

                current_api = ApiInfo(
                    name=name,
                    http_method='',
                    path='',
                    sequence=sequence,
                )
                continue

            # 解析基本信息表格
            if current_api:
                path_match = re.search(self.PATH_PATTERN, line)
                if path_match:
                    current_api.http_method = path_match.group(1)
                    current_api.path = path_match.group(2)

                seq_match = re.search(self.SEQUENCE_PATTERN, line)
                if seq_match:
                    current_api.sequence = int(seq_match.group(1))

        # 保存最后一个接口
        if current_api:
            parsed.interfaces.append(current_api)

        return parsed

    def extract_existing_interfaces(self, content: str) -> List[ApiInfo]:
        """提取已存在的所有接口"""
        parsed = self.parse(content)
        return parsed.interfaces