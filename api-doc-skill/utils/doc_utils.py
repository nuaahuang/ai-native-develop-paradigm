"""文档处理工具"""

import re
from templates.markdown_template import generate_api_section


def read_doc(file_path: str) -> str:
    """读取文档内容"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def write_doc(file_path: str, content: str):
    """写入文档内容"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def find_api_by_path(doc_content: str, api_path: str) -> bool:
    """检查接口是否已存在"""
    # 查找是否有相同路径的接口
    pattern = rf"`[A-Z]+\s+{re.escape(api_path)}`"
    return re.search(pattern, doc_content) is not None


def update_doc(existing_doc: str, api_info: dict, is_new: bool = False) -> str:
    """更新文档内容"""
    if is_new:
        return add_new_api(existing_doc, api_info)
    else:
        return replace_api(existing_doc, api_info)


def add_new_api(doc_content: str, api_info: dict) -> str:
    """添加新接口到文档"""
    # 生成新接口内容
    new_api_section = generate_api_section(api_info)
    
    # 更新目录
    api_name = api_info.get('api_name', '未命名接口')
    doc_content = update_table_of_contents(doc_content, api_name)
    
    # 在文档末尾添加新接口
    return doc_content + "\n" + new_api_section


def replace_api(doc_content: str, api_info: dict) -> str:
    """替换已存在的接口内容"""
    api_path = api_info.get('path', '')
    api_name = api_info.get('api_name', '未命名接口')
    
    # 找到接口位置并替换
    # 匹配模式：找到以 "## 接口：XXX" 开头，到下一个 "## 接口：" 或文档结束
    pattern = rf"(## 接口：[^#]+?)(?=\n## 接口：|\Z)"
    new_section = generate_api_section(api_info)
    
    def replace_match(match):
        # 检查是否是目标接口
        if api_path in match.group(1):
            return new_section
        return match.group(1)
    
    return re.sub(pattern, replace_match, doc_content, flags=re.DOTALL)


def update_table_of_contents(doc_content: str, api_name: str) -> str:
    """更新目录"""
    # 查找目录部分
    toc_pattern = r"(## 目录\n\n)(.*?)(\n---)"
    match = re.search(toc_pattern, doc_content, re.DOTALL)
    
    if match:
        existing_toc = match.group(2)
        # 查找最后一个编号
        last_num_pattern = r"(\d+)\."
        nums = re.findall(last_num_pattern, existing_toc)
        if nums:
            next_num = int(nums[-1]) + 1
        else:
            next_num = 1
        
        # 添加新目录项
        new_toc = existing_toc.strip() + f"\n{next_num}. [{api_name}](#接口{api_name})"
        return doc_content[:match.start(2)] + new_toc + doc_content[match.end(2):]
    
    return doc_content