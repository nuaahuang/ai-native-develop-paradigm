"""Markdown 文档模板生成器"""

import json
from datetime import datetime


def generate_api_doc(api_info: dict, is_new_doc: bool = False) -> str:
    """生成接口文档内容"""
    if is_new_doc:
        return generate_new_doc(api_info)
    return generate_api_section(api_info)


def generate_new_doc(api_info: dict) -> str:
    """生成新文档"""
    doc = []
    doc.append("# 接口文档")
    doc.append("")
    doc.append("> 自动生成，请勿手动修改")
    doc.append("")
    doc.append("---")
    doc.append("")
    doc.append("## 目录")
    doc.append("")
    
    # 添加目录项
    api_name = api_info.get('api_name', '未命名接口')
    doc.append(f"1. [{api_name}](#接口{api_name})")
    doc.append("")
    doc.append("---")
    doc.append("")
    
    # 添加接口内容
    doc.append(generate_api_section(api_info))
    
    return '\n'.join(doc)


def generate_api_section(api_info: dict) -> str:
    """生成单个接口的文档片段"""
    lines = []
    
    # 接口标题
    api_name = api_info.get('api_name', '未命名接口')
    lines.append(f"## 接口：{api_name}")
    lines.append("")
    
    # 基本信息
    lines.append("### 基本信息")
    lines.append("")
    lines.append("| 项目 | 值 |")
    lines.append("|------|-----|")
    lines.append(f"| **接口路径** | `{api_info.get('method', 'GET')} {api_info.get('path', '')}` |")
    lines.append(f"| **最后更新** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |")
    lines.append("")
    
    # UI 截图
    if 'ui_image' in api_info and api_info['ui_image']:
        lines.append("### UI 截图")
        lines.append("")
        lines.append(f"![{api_name}]({api_info['ui_image']})")
        lines.append("")
    
    # 请求参数
    params = api_info.get('params', [])
    query_params = api_info.get('query_params', [])
    
    if params or query_params:
        lines.append("### 请求参数")
        lines.append("")
        
        if params:
            lines.append("#### 路径参数")
            lines.append("")
            lines.append("| 参数名 | 类型 | 必填 | 说明 |")
            lines.append("|--------|------|------|------|")
            for param in params:
                lines.append(f"| {param['name']} | {param['type']} | {'是' if param['required'] else '否'} | {param.get('description', '')} |")
            lines.append("")
        
        if query_params:
            lines.append("#### 查询参数")
            lines.append("")
            lines.append("| 参数名 | 类型 | 必填 | 说明 |")
            lines.append("|--------|------|------|------|")
            for param in query_params:
                lines.append(f"| {param['name']} | {param['type']} | {'是' if param['required'] else '否'} | {param.get('description', '')} |")
            lines.append("")
    
    # 响应结构
    response = api_info.get('response', {})
    lines.append("### 响应结构")
    lines.append("")
    lines.append("#### 成功响应（200 OK）")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(response, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("")
    
    # 字段说明
    data = response.get('data', {})
    if data:
        lines.append("#### 字段说明")
        lines.append("")
        lines.append("| 字段名 | 类型 | 说明 |")
        lines.append("|--------|------|------|")
        for key, value in data.items():
            field_type = type(value).__name__
            lines.append(f"| {key} | {field_type} | |")
        lines.append("")
    
    # 错误响应
    lines.append("### 错误响应")
    lines.append("")
    lines.append("| HTTP 状态码 | 说明 |")
    lines.append("|-------------|------|")
    lines.append("| 400 | 请求参数错误 |")
    lines.append("| 401 | 未授权 |")
    lines.append("| 404 | 资源不存在 |")
    lines.append("| 500 | 系统内部错误 |")
    lines.append("")
    
    return '\n'.join(lines)