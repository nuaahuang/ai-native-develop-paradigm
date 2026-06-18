from dataclasses import dataclass, field
from typing import List, Optional
import os
import json


@dataclass
class ScanConfig:
    """批量扫描配置"""
    # 默认排除目录
    exclude_dirs: List[str] = field(default_factory=lambda: [
        'node_modules',
        'venv',
        '.venv',
        '.git',
        '__pycache__',
        'tests',
        'test',
        'build',
        'dist',
    ])
    # 默认排除文件模式
    exclude_patterns: List[str] = field(default_factory=lambda: [
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '.DS_Store',
    ])
    # 包含的文件扩展名
    include_extensions: List[str] = field(default_factory=lambda: [
        '.py',
        '.java',
        '.js',
        '.ts',
        '.go',
        '.proto',
        '.graphql',
        '.gql',
    ])


@dataclass
class ImageConfig:
    """图片处理配置"""
    image_dir: str = "images"


@dataclass
class OutputConfig:
    """输出配置"""
    output_file: str
    api_name: Optional[str] = None
    version: Optional[str] = None
    export_openapi: Optional[str] = None
    scan_dir: Optional[str] = None
    exclude: Optional[List[str]] = None


@dataclass
class Config:
    """全局配置"""
    scan: ScanConfig = field(default_factory=ScanConfig)
    image: ImageConfig = field(default_factory=ImageConfig)
    output: OutputConfig = None

    @classmethod
    def from_file(cls, path: str) -> 'Config':
        """从配置文件加载"""
        if not os.path.exists(path):
            return cls()

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        config = cls()
        if 'scan' in data:
            config.scan = ScanConfig(**data['scan'])
        if 'image' in data:
            img_dir = data['image'].get('image_dir', 'images')
            config.image = ImageConfig(image_dir=img_dir)

        return config

    def add_exclude_patterns(self, patterns: List[str]):
        """添加额外排除模式"""
        self.scan.exclude_patterns.extend(patterns)

    def get_image_dir(self, output_file: str) -> str:
        """获取图片目录绝对路径"""
        output_dir = os.path.dirname(os.path.abspath(output_file))
        return os.path.join(output_dir, self.image.image_dir)
