from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OutputConfig:
    """输出配置"""
    output_file: str
    api_name: Optional[str] = None
    export_openapi: Optional[str] = None


@dataclass
class Config:
    """全局配置"""
    output: OutputConfig = None