from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict
from .parameter import Parameter
from .response import ResponseInfo


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

    # 所属文件
    source_file: Optional[str] = None

    # 时间信息
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # 参数和响应
    parameters: List[Parameter] = field(default_factory=list)
    responses: List[ResponseInfo] = field(default_factory=list)

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
            "source_file": self.source_file,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "parameters": [p.to_dict() for p in self.parameters],
            "responses": [r.to_dict() for r in self.responses],
            "ui_image_path": self.ui_image_path,
            "examples": self.examples,
            "test_suggestions": self.test_suggestions,
        }

    @property
    def full_path(self) -> str:
        """返回完整路径"""
        return self.path