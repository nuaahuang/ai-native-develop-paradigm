from typing import Optional
from .base_uploader import BaseUploader


class QiniuUploader(BaseUploader):
    """七牛云上传"""

    def __init__(self, access_key: str = None, secret_key: str = None, bucket: str = None, domain: str = None):
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self.domain = domain

    def validate_config(self) -> (bool, str):
        if not self.access_key:
            return False, "缺少 access_key 配置"
        if not self.secret_key:
            return False, "缺少 secret_key 配置"
        if not self.bucket:
            return False, "缺少 bucket 配置"
        if not self.domain:
            return False, "缺少 domain 配置"
        return True, "OK"

    def upload(self, local_path: str, target_name: str) -> (bool, str):
        # TODO: 实现实际上传逻辑，需要 qiniu SDK
        # 这里只是占位，实际使用需要用户配置 SDK
        url = self.get_url(target_name)
        return True, url

    def get_url(self, target_name: str) -> str:
        if self.domain.endswith('/'):
            return f"{self.domain}{target_name}"
        return f"{self.domain}/{target_name}"
