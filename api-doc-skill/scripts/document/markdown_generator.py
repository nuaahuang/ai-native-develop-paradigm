from typing import List, Optional, Dict
from datetime import datetime
from scripts.models.api_info import ApiInfo
from scripts.models.parameter import Parameter, ParameterLocation
from scripts.models.response import ResponseInfo
from scripts.config import Config


class MarkdownGenerator:
    """Markdown 文档生成器"""

    def __init__(self, config: Config):
        self.config = config

    def generate_full_document(self, interfaces: List[ApiInfo], version_interfaces: Dict[str, List[ApiInfo]] = None) -> str:
        """生成完整文档"""
        version_interfaces = version_interfaces or {}

        lines = []
        lines.append('# 接口文档\n')
        lines.append('> 自动生成，请勿手动修改\n')
        lines.append('')
        lines.append('---')
        lines.append('')

        # 生成目录
        lines.extend(self._generate_toc(interfaces, version_interfaces))
        lines.append('')
        lines.append('---')
        lines.append('')

        # 按版本分组生成
        if version_interfaces:
            for version, apis in sorted(version_interfaces.items()):
                lines.append(f'## {version} 版本')
                lines.append('')
                for api in sorted(apis, key=lambda x: x.sequence):
                    lines.extend(self._generate_api_section(api, version))
                    lines.append('')
                    lines.append('---')
                    lines.append('')
        else:
            # 无版本，直接按序号生成
            for api in sorted(interfaces, key=lambda x: x.sequence):
                lines.extend(self._generate_api_section(api))
                lines.append('')
                lines.append('---')
                lines.append('')

        return '\n'.join(lines)

    def _generate_toc(self, interfaces: List[ApiInfo], version_interfaces: Dict[str, List[ApiInfo]]) -> List[str]:
        """生成目录"""
        lines = ['## 目录', '']

        if version_interfaces:
            # 按版本分组
            for version, apis in sorted(version_interfaces.items()):
                lines.append(f'### {version}')
                sorted_apis = sorted(apis, key=lambda x: x.sequence)
                for i, api in enumerate(sorted_apis, 1):
                    anchor = self._get_anchor(api, version)
                    name = api.name
                    lines.append(f'{i}. [{version}-{api.sequence}-{name}](#{anchor})')
                lines.append('')
        else:
            sorted_apis = sorted(interfaces, key=lambda x: x.sequence)
            for i, api in enumerate(sorted_apis, 1):
                anchor = self._get_anchor(api)
                name = api.name
                lines.append(f'{i}. [{api.sequence}-{name}](#{anchor})')

        return lines

    def _get_anchor(self, api: ApiInfo, version: Optional[str] = None) -> str:
        """获取锚点"""
        v = version or api.version
        if v:
            return f'{v}-{api.sequence}-接口{api.name}'.lower().replace(' ', '-')
        return f'{api.sequence}-接口{api.name}'.lower().replace(' ', '-')

    def _generate_api_section(self, api: ApiInfo, version: Optional[str] = None) -> List[str]:
        """生成单个接口章节"""
        lines = []

        # 标题
        v = version or api.version
        if v:
            lines.append(f'## {v}-{api.sequence}-接口：{api.name}')
        else:
            lines.append(f'## {api.sequence}-接口：{api.name}')
        lines.append('')

        # 基本信息
        lines.append('### 基本信息')
        lines.append('')
        lines.append('| 项目 | 值 |')
        lines.append('|------|-----|')
        lines.append(f'| **接口序号** | {api.sequence} |')
        lines.append(f'| **接口名称** | {api.name} |')
        if v:
            lines.append(f'| **版本** | {v} |')
        lines.append(f'| **接口路径** | `{api.http_method} {api.path}` |')
        if api.source_file:
            lines.append(f'| **所属文件** | `{api.source_file}` |')
        lines.append(f'| **最后更新** | {api.updated_at.strftime("%Y-%m-%d %H:%M:%S")} |')
        lines.append('')

        # 描述
        if api.description:
            lines.append('### 描述')
            lines.append('')
            lines.append(api.description)
            lines.append('')

        # UI 截图
        if api.ui_image_path:
            lines.append('### UI 截图')
            lines.append('')
            lines.append(f'![{api.name}]({api.ui_image_path})')
            lines.append('')

        # 请求参数
        if api.parameters:
            lines.append('### 请求参数')
            lines.append('')

            # 按位置分组
            groups: Dict[ParameterLocation, List[Parameter]] = {}
            for param in api.parameters:
                if param.location not in groups:
                    groups[param.location] = []
                groups[param.location].append(param)

            for location, params in groups.items():
                if len(groups) > 1:
                    title = {
                        ParameterLocation.PATH: '路径参数',
                        ParameterLocation.QUERY: '查询参数',
                        ParameterLocation.BODY: '请求体',
                        ParameterLocation.FORM: '表单参数',
                        ParameterLocation.HEADER: '请求头',
                    }[location]
                    lines.append(f'#### {title}')
                    lines.append('')

                lines.append('| 参数名 | 类型 | 必填 | 说明 |')
                lines.append('|--------|------|------|------|')
                for param in params:
                    required = '是' if param.required else '否'
                    desc = param.description or ''
                    lines.append(f'| {param.name} | {param.type_} | {required} | {desc} |')
                lines.append('')

        # 响应结构
        if api.responses:
            lines.append('### 响应结构')
            lines.append('')

            for response in api.responses:
                lines.append(f'#### {response.description}（{response.status_code}）')
                lines.append('')

                if response.example_json:
                    lines.append('```json')
                    lines.append(response.example_json)
                    lines.append('```')
                    lines.append('')

                if response.fields:
                    lines.append('#### 字段说明')
                    lines.append('')
                    lines.append('| 字段名 | 类型 | 必填 | 说明 |')
                    lines.append('|--------|------|------|------|')
                    for field in response.fields:
                        required = '是' if field.required else '否'
                        desc = field.description or ''
                        lines.append(f'| {field.name} | {field.type_} | {required} | {desc} |')
                    lines.append('')

        # 错误响应
        error_responses = [r for r in api.responses if r.status_code >= 400]
        if error_responses:
            lines.append('### 错误响应')
            lines.append('')
            lines.append('| HTTP 状态码 | 说明 |')
            lines.append('|-------------|------|')
            for resp in error_responses:
                lines.append(f'| {resp.status_code} | {resp.description} |')
            lines.append('')

        # 测试示例
        if api.examples:
            lines.append('### 调用示例')
            lines.append('')

            if 'curl' in api.examples:
                lines.append('#### curl')
                lines.append('')
                lines.append('```bash')
                lines.append(api.examples['curl'])
                lines.append('```')
                lines.append('')

            if 'python' in api.examples:
                lines.append('#### Python requests')
                lines.append('')
                lines.append('```python')
                lines.append(api.examples['python'])
                lines.append('```')
                lines.append('')

            if 'javascript' in api.examples:
                lines.append('#### JavaScript fetch')
                lines.append('')
                lines.append('```javascript')
                lines.append(api.examples['javascript'])
                lines.append('```')
                lines.append('')

        # 测试用例建议
        if api.test_suggestions:
            lines.append('### 测试用例建议')
            lines.append('')
            for suggestion in api.test_suggestions:
                lines.append(f'- {suggestion}')
            lines.append('')

        # 变更历史
        if api.change_history:
            lines.append('### 变更历史')
            lines.append('')
            lines.append('| 版本 | 时间 | 类型 | 变更说明 |')
            lines.append('|------|------|------|----------|')
            for change in api.change_history:
                changed_at = change.changed_at.strftime("%Y-%m-%d")
                lines.append(f'| {change.version} | {changed_at} | {change.change_type} | {change.change_log} |')
            lines.append('')

        return lines

    def assign_sequences(self, existing_interfaces: List[ApiInfo], new_interfaces: List[ApiInfo]) -> List[ApiInfo]:
        """分配序号，保持已有序号不变"""
        # 已有接口保持序号
        # 新接口从最大序号开始递增
        if existing_interfaces:
            max_seq = max(api.sequence for api in existing_interfaces)
        else:
            max_seq = 0

        result = existing_interfaces.copy()

        for new_api in new_interfaces:
            # 检查是否已经存在（同路径同版本）
            exists = False
            for i, existing in enumerate(result):
                if existing.path == new_api.path and existing.version == new_api.version:
                    # 保持原有序号，更新内容
                    new_api.sequence = existing.sequence
                    result[i] = new_api
                    exists = True
                    break
            if not exists:
                max_seq += 1
                new_api.sequence = max_seq
                result.append(new_api)

        # 按序号排序
        result.sort(key=lambda x: x.sequence)
        return result
