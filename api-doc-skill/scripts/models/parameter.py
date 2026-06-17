from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ParameterLocation(Enum):
    """参数位置枚举"""
    PATH = "path"
    QUERY = "query"
    BODY = "body"
    FORM = "form"
    HEADER = "header"


@dataclass
class Parameter:
    """参数定义"""
    name: str
    type_: str
    required: bool = False
    description: str = ""
    location: ParameterLocation = ParameterLocation.PATH
    default: Optional[str] = None
    example: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type_,
            "required": self.required,
            "description": self.description,
            "location": self.location.value,
            "default": self.default,
            "example": self.example,
        }
