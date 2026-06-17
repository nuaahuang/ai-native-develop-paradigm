from typing import Optional
from .base_uploader import BaseUploader


class OssUploader(BaseUploader):
    """阿里云 OSS 上传"""

    def __init__(self, access_key_id: str = None, access_key_secret: str = None, bucket: str = None, endpoint: str = None):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.bucket = bucket
        self.endpoint = endpoint

    def validate_config(self) -> (bool, str):
        if not self.access_key_id:
            return False, "缺少 access_key_id 配置"
        if not self.access_key_secret:
            return False, "缺少 access_key_secret 配置"
        if not self.bucket:
            return False, "缺少 bucket 配置"
        if not self.endpoint:
            return False, "缺少 endpoint 配置"
        return True, "OK"

    def upload(self, local_path: str, target_name: str) -> (bool, str):
        # TODO: 实现实际上传逻辑，需要 aliyun OSS SDK
        url = self.get_url(target_name)
        return True, url

    def get_url(self, target_name: str) -> str:
        if self.endpoint.endswith('/'):
            return f"{self.endpoint}{self.bucket}/{target_name}"
        return f"{self.endpoint}/{self.bucket}/{target_name}"
