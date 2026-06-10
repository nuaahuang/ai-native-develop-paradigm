#!/usr/bin/env python3
"""
api-doc Skill - 简化版接口文档生成工具

核心功能：
1. 解析选中的接口代码
2. 支持上传 UI 截图
3. 自动判断接口是否已存在
4. 生成/更新 Markdown 格式接口文档
"""

import argparse
import os
import re
import json
from datetime import datetime
from pathlib import Path

# 导入解析器
from parsers.java_parser import parse_java_code
from parsers.python_parser import parse_python_code
from parsers.generic_parser import parse_generic_code
from templates.markdown_template import generate_api_doc
from utils.image_utils import save_image
from utils.doc_utils import read_doc, write_doc, find_api_by_path, update_doc


def detect_code_type(code: str) -> str:
    """检测代码类型"""
    if '@GetMapping' in code or '@PostMapping' in code or 'ResponseEntity' in code:
        return 'java'
    elif '@app.get' in code or '@app.post' in code or 'FastAPI' in code:
        return 'python'
    elif 'app.get(' in code or 'app.post(' in code or 'express' in code.lower():
        return 'javascript'
    elif 'r.GET(' in code or 'r.POST(' in code or 'gin' in code.lower():
        return 'go'
    elif code.strip().startswith(('GET', 'POST', 'PUT', 'DELETE', 'PATCH')):
        return 'generic'
    return 'generic'


def parse_code(code: str, code_type: str) -> dict:
    """解析代码，提取接口信息"""
    parsers = {
        'java': parse_java_code,
        'python': parse_python_code,
        'javascript': parse_generic_code,
        'go': parse_generic_code,
        'generic': parse_generic_code
    }
    return parsers.get(code_type, parse_generic_code)(code)


def main():
    parser = argparse.ArgumentParser(description='api-doc Skill - 接口文档生成工具')
    parser.add_argument('--code', type=str, help='选中的接口代码')
    parser.add_argument('--ui-image', type=str, help='UI 截图路径或URL')
    parser.add_argument('--output', type=str, required=True, help='输出 MD 文档路径')
    parser.add_argument('--api-name', type=str, help='接口名称（可选）')
    
    args = parser.parse_args()
    
    # 获取代码（优先从参数，其次从剪贴板）
    code = args.code
    if not code:
        try:
            import pyperclip
            code = pyperclip.paste()
        except ImportError:
            print("错误：请提供 --code 参数或安装 pyperclip")
            return
    
    if not code.strip():
        print("错误：请先选中接口代码")
        return
    
    # 检测代码类型并解析
    code_type = detect_code_type(code)
    print(f"检测到代码类型: {code_type}")
    
    api_info = parse_code(code, code_type)
    
    # 如果指定了接口名称，覆盖解析结果
    if args.api_name:
        api_info['api_name'] = args.api_name
    
    print(f"解析结果: {json.dumps(api_info, ensure_ascii=False, indent=2)}")
    
    # 处理图片
    image_path = None
    if args.ui_image and os.path.exists(args.ui_image):
        output_dir = os.path.dirname(args.output) or '.'
        image_path = save_image(args.ui_image, output_dir, api_info['path'])
        print(f"图片保存路径: {image_path}")
    
    # 设置图片相对路径
    if image_path:
        api_info['ui_image'] = os.path.relpath(image_path, os.path.dirname(args.output) or '.')
    
    # 读取或创建文档
    doc_path = Path(args.output)
    if doc_path.exists():
        existing_doc = read_doc(str(doc_path))
        # 检查接口是否已存在
        if find_api_by_path(existing_doc, api_info['path']):
            print(f"接口 {api_info['path']} 已存在，将更新")
            new_doc = update_doc(existing_doc, api_info)
        else:
            print(f"接口 {api_info['path']} 不存在，将新增")
            new_doc = update_doc(existing_doc, api_info, is_new=True)
    else:
        print(f"文档 {args.output} 不存在，将创建新文档")
        new_doc = generate_api_doc(api_info, is_new_doc=True)
    
    # 写入文档
    write_doc(str(doc_path), new_doc)
    print(f"文档已更新: {args.output}")


if __name__ == '__main__':
    main()