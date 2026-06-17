from typing import List, Dict, Optional
from datetime import datetime
from scripts.models.api_info import ApiInfo
from scripts.models.version_info import VersionInfo, Change


class VersionManager:
    """版本管理器"""

    def __init__(self):
        self.versions: Dict[str, VersionInfo] = {}

    def add_version(self, version: str, change_log: str = "") -> VersionInfo:
        """添加新版本"""
        now = datetime.now()
        info = VersionInfo(
            version=version,
            created_at=now,
            updated_at=now,
            change_log=change_log,
        )
        self.versions[version] = info
        return info

    def get_version(self, version: str) -> Optional[VersionInfo]:
        """获取版本信息"""
        return self.versions.get(version)

    def list_versions(self) -> List[str]:
        """列出所有版本"""
        return sorted(self.versions.keys())

    def update_version(self, version: str, interface_path: str):
        """更新版本，添加接口"""
        if version in self.versions:
            info = self.versions[version]
            if interface_path not in info.interfaces:
                info.interfaces.append(interface_path)
            info.updated_at = datetime.now()
        else:
            self.add_version(version, f"初始版本，包含 {interface_path}")

    def group_by_version(self, interfaces: List[ApiInfo]) -> Dict[str, List[ApiInfo]]:
        """按版本分组接口"""
        groups: Dict[str, List[ApiInfo]] = {}

        for api in interfaces:
            version = api.version or 'v1'
            if version not in groups:
                groups[version] = []
            groups[version].append(api)

        # 每个分组按序号排序
        for v in groups:
            groups[v].sort(key=lambda x: x.sequence)

        return groups

    def add_change(self, api: ApiInfo, version: str, change_type: str, change_log: str, author: str = None):
        """添加接口变更记录"""
        from scripts.models.version_info import Change
        change = Change(
            version=version,
            changed_at=datetime.now(),
            change_type=change_type,
            change_log=change_log,
            author=author,
        )
        api.add_change(change)
        api.updated_at = change.changed_at

    def detect_changes(self, old_api: ApiInfo, new_api: ApiInfo) -> Optional[str]:
        """检测接口变更，返回变更描述"""
        changes = []

        # 参数变更
        old_params = {(p.name, p.location): p for p in old_api.parameters}
        new_params = {(p.name, p.location): p for p in new_api.parameters}

        added_params = set(new_params.keys()) - set(old_params.keys())
        removed_params = set(old_params.keys()) - set(new_params.keys())

        if added_params:
            changes.append(f"新增参数: {', '.join(n[0] for n in added_params)}")
        if removed_params:
            changes.append(f"移除参数: {', '.join(n[0] for n in removed_params)}")

        # 路径变更
        if old_api.path != new_api.path:
            changes.append(f"路径变更: {old_api.path} → {new_api.path}")

        # HTTP 方法变更
        if old_api.http_method != new_api.http_method:
            changes.append(f"方法变更: {old_api.http_method} → {new_api.http_method}")

        if changes:
            return "; ".join(changes)
        return None
