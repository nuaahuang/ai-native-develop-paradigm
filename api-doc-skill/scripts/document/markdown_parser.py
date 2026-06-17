import re
from dataclasses import dataclass
from typing import List, Optional, Dict
from scripts.models.api_info import ApiInfo


@dataclass
class ParsedDocument:
    """解析后的文档"""
    title: str
    interfaces: List[ApiInfo]
    version_interfaces: Dict[str, List[ApiInfo]] = None

    def __post_init__(self):
        if self.version_interfaces is None:
            self.version_interfaces = {}

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
        # 检查带版本的路径
        for version, apis in self.version_interfaces.items():
            for api in apis:
                if api.path == path:
                    return api
        return None


class MarkdownDocumentParser:
    """Markdown 文档解析器"""

    # 匹配接口标题: ## 1-接口：名称 或 ## v1-1-接口：名称
    # 使用更精确的正则：(version)(sequence)-接口：name
    INTERFACE_TITLE_PATTERN = r'^##\s+(?:([^\s-]+)-)?(\d+)-接口：\s*(.+)$'
    # 基本信息表格
    PATH_PATTERN = r'\*\*接口路径\*\*\s*\|\s*`([A-Z]+)\s+([^`]+)`'
    SEQUENCE_PATTERN = r'\*\*接口序号\*\*\s*\|\s*(\d+)'
    VERSION_PATTERN = r'\*\*版本\*\*\s*\|\s*(.+)'

    def parse(self, content: str) -> ParsedDocument:
        """解析 Markdown 文档"""
        lines = content.split('\n')
        parsed = ParsedDocument(
            title="接口文档",
            interfaces=[],
            version_interfaces={}
        )

        current_api: Optional[ApiInfo] = None
        current_version: Optional[str] = None

        for i, line in enumerate(lines):
            line = line.rstrip()

            # 一级标题作为文档标题
            if line.startswith('# '):
                parsed.title = line[2:].strip()
                continue

            # 版本分组: ## v1 版本
            version_match = re.match(r'^##\s+(\w+)\s+版本\s*$', line)
            if version_match:
                current_version = version_match.group(1)
                if current_version not in parsed.version_interfaces:
                    parsed.version_interfaces[current_version] = []
                continue

            # 接口标题
            title_match = re.match(self.INTERFACE_TITLE_PATTERN, line)
            if title_match:
                # 如果有当前正在处理的接口，保存它
                if current_api:
                    self._add_api(parsed, current_api, current_version)
                    current_api = None

                version_part = title_match.group(1)  # 版本部分，可能 None
                sequence = int(title_match.group(2))
                name = title_match.group(3).strip()

                if version_part:
                    current_version = version_part.strip()

                current_api = ApiInfo(
                    name=name,
                    http_method='',
                    path='',
                    sequence=sequence,
                    version=current_version,
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

                version_match = re.search(self.VERSION_PATTERN, line)
                if version_match:
                    current_api.version = version_match.group(1).strip()

        # 保存最后一个接口
        if current_api:
            self._add_api(parsed, current_api, current_version)

        # 合并版本接口到总列表
        for version, apis in parsed.version_interfaces.items():
            parsed.interfaces.extend(apis)

        return parsed

    def _add_api(self, parsed: ParsedDocument, api: ApiInfo, version: Optional[str]):
        """添加接口到解析结果"""
        if version and version in parsed.version_interfaces:
            parsed.version_interfaces[version].append(api)
        else:
            parsed.interfaces.append(api)

    def extract_existing_interfaces(self, content: str) -> List[ApiInfo]:
        """提取已存在的所有接口"""
        parsed = self.parse(content)
        return parsed.interfaces
