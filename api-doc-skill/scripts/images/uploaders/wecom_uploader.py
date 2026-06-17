from typing import Optional
from .base_uploader import BaseUploader


class WecomUploader(BaseUploader):
    """企业微信素材上传"""

    def __init__(self, corpid: str = None, corpsecret: str = None, agentid: str = None):
        self.corpid = corpid
        self.corpsecret = corpsecret
        self.agentid = agentid

    def validate_config(self) -> (bool, str):
        if not self.corpid:
            return False, "缺少 corpid 配置"
        if not self.corpsecret:
            return False, "缺少 corpsecret 配置"
        if not self.agentid:
            return False, "缺少 agentid 配置"
        return True, "OK"

    def upload(self, local_path: str, target_name: str) -> (bool, str):
        # TODO: 实现实际上传逻辑，需要调用企业微信 API
        # 返回 media_id
        # 对于企业微信，最终还是放在文档中
        return False, "企业微信上传尚未实现，请使用 base64 模式"

    def get_url(self, target_name: str) -> str:
        return target_name
