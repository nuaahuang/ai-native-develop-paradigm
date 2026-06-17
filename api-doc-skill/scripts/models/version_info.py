from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class Change:
    """接口变更记录"""
    version: str
    changed_at: datetime
    change_type: str  # added, modified, deprecated, removed
    change_log: str
    author: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "changed_at": self.changed_at.isoformat(),
            "change_type": self.change_type,
            "change_log": self.change_log,
            "author": self.author,
        }


@dataclass
class VersionInfo:
    """版本信息"""
    version: str
    created_at: datetime
    updated_at: datetime
    change_log: str = ""
    interfaces: List[str] = None

    def __post_init__(self):
        if self.interfaces is None:
            self.interfaces = []

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "change_log": self.change_log,
            "interfaces": self.interfaces,
        }
