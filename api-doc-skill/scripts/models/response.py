from dataclasses import dataclass
from typing import Optional, List


@dataclass
class ResponseField:
    """响应字段定义"""
    name: str
    type_: str
    description: str = ""
    required: bool = True
    example: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type_,
            "description": self.description,
            "required": self.required,
            "example": self.example,
        }


@dataclass
class ResponseInfo:
    """响应定义"""
    status_code: int = 200
    description: str = "成功"
    fields: Optional[List[ResponseField]] = None
    example_json: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "status_code": self.status_code,
            "description": self.description,
            "fields": [f.to_dict() for f in (self.fields or [])],
            "example_json": self.example_json,
        }
