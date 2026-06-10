"""图片处理工具"""

import os
import shutil
from datetime import datetime


def save_image(image_path: str, output_dir: str, api_path: str) -> str:
    """保存图片到指定目录"""
    # 确保输出目录存在
    images_dir = os.path.join(output_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)
    
    # 生成文件名：路径转义 + 时间戳
    safe_name = api_path.strip('/').replace('/', '-').replace('{', '').replace('}', '')
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    ext = os.path.splitext(image_path)[1] or '.png'
    
    # 如果文件名太长，截断
    if len(safe_name) > 30:
        safe_name = safe_name[:30]
    
    new_filename = f"{safe_name}_{timestamp}{ext}"
    new_path = os.path.join(images_dir, new_filename)
    
    # 复制图片
    shutil.copy(image_path, new_path)
    
    return new_path