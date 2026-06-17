from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict
from .parameter import Parameter
from .response import ResponseInfo
from .version_info import Change


@dataclass
class ApiInfo:
    """API 信息数据模型"""
    # 基本信息
    name: str
    http_method: str
    path: str
    summary: str = ""
    description: str = ""

    # 序号
    sequence: int = 0

    # 版本信息
    version: Optional[str] = None

    # 所属文件
    source_file: Optional[str] = None

    # 时间信息
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # 参数和响应
    parameters: List[Parameter] = field(default_factory=list)
    responses: List[ResponseInfo] = field(default_factory=list)

    # 变更历史
    change_history: List[Change] = field(default_factory=list)

    # UI 截图
    ui_image_path: Optional[str] = None

    # 测试示例
    examples: Dict[str, str] = field(default_factory=dict)

    # 测试用例建议
    test_suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "http_method": self.http_method,
            "path": self.path,
            "summary": self.summary,
            "description": self.description,
            "sequence": self.sequence,
            "version": self.version,
            "source_file": self.source_file,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "parameters": [p.to_dict() for p in self.parameters],
            "responses": [r.to_dict() for r in self.responses],
            "change_history": [c.to_dict() for c in self.change_history],
            "ui_image_path": self.ui_image_path,
            "examples": self.examples,
            "test_suggestions": self.test_suggestions,
        }

    @property
    def full_path(self) -> str:
        """返回带版本的完整路径"""
        if self.version and not self.path.startswith(f"/{self.version}"):
            return f"/{self.version}{self.path}"
        return self.path

    def add_change(self, change: Change):
        """添加变更记录"""
        self.change_history.append(change)
        self.updated_at = change.changed_at
