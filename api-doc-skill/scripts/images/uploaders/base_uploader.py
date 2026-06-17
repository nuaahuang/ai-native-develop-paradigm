from abc import ABC, abstractmethod
from typing import Optional


class BaseUploader(ABC):
    """云存储上传器基类"""

    @abstractmethod
    def upload(self, local_path: str, target_name: str) -> (bool, str):
        """上传图片，返回 (成功, 访问URL / 错误信息)"""
        pass

    @abstractmethod
    def get_url(self, target_name: str) -> str:
        """获取访问 URL"""
        pass

    def validate_config(self) -> (bool, str):
        """验证配置是否完整"""
        return True, "OK"
