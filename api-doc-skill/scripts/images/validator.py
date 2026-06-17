import os
from typing import Optional
from PIL import Image


class ImageValidator:
    """图片验证器"""

    @staticmethod
    def validate_file(file_path: str) -> (bool, str):
        """验证图片文件"""
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return False, f"图片文件不存在: {file_path}"

        # 检查文件大小
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return False, f"图片文件为空: {file_path}"

        # 检查是否是有效的图片
        try:
            with Image.open(file_path) as img:
                # 验证图片可以打开
                img.verify()
            return True, "OK"
        except Exception as e:
            return False, f"图片文件损坏: {str(e)}"

    @staticmethod
    def get_image_info(file_path: str) -> Optional[dict]:
        """获取图片信息"""
        if not os.path.exists(file_path):
            return None

        try:
            with Image.open(file_path) as img:
                return {
                    "format": img.format,
                    "width": img.width,
                    "height": img.height,
                    "mode": img.mode,
                    "size_kb": os.path.getsize(file_path) // 1024,
                }
        except Exception:
            return None

    @staticmethod
    def validate_reference(image_path: str, doc_dir: str) -> (bool, str):
        """验证文档中的图片引用"""
        full_path = os.path.join(doc_dir, image_path)
        return ImageValidator.validate_file(full_path)
