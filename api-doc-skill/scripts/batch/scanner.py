import os
import re
from typing import List, Tuple, Iterator, Optional
from scripts.config import Config, ScanConfig


class ProjectScanner:
    """项目目录扫描器"""

    # 敏感目录/文件模式，禁止扫描
    SENSITIVE_PATTERNS = [
        '.ssh', '.aws', '.git-credentials', '.npmrc',
        'id_rsa', 'id_dsa', 'id_ecdsa', 'id_ed25519',
        'passwd', 'shadow', 'sudoers',
        '.env', '.env.local', '.env.*',
        'credentials', 'config',
    ]

    def __init__(self, config: ScanConfig = None):
        self.config = config or ScanConfig()
        # 添加敏感模式到排除列表
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern not in self.config.exclude_patterns:
                self.config.exclude_patterns.append(pattern)

    def should_exclude(self, path: str) -> bool:
        """判断是否应该排除"""
        name = os.path.basename(path)

        # 检查敏感文件
        for sensitive in self.SENSITIVE_PATTERNS:
            if name == sensitive or name.endswith(f'.{sensitive}'):
                return True

        # 排除目录
        if os.path.isdir(path):
            if name in self.config.exclude_dirs:
                return True

        # 检查排除模式
        for pattern in self.config.exclude_patterns:
            # 简单的 glob 匹配，只支持末尾通配符
            if pattern.startswith('*.'):
                ext = pattern[2:]
                if name.endswith('.' + ext):
                    return True
            elif pattern == name:
                return True

        return False

    def has_matching_extension(self, filename: str) -> bool:
        """检查文件扩展名是否匹配"""
        for ext in self.config.include_extensions:
            if filename.endswith(ext):
                return True
        return False

    def _is_safe_path(self, root_dir: str, file_path: str) -> bool:
        """检查路径是否在允许的工作目录范围内"""
        # 解析绝对路径
        root_abs = os.path.abspath(root_dir)
        file_abs = os.path.abspath(file_path)

        # 标准化处理
        root_abs = os.path.normpath(root_abs)
        file_abs = os.path.normpath(file_abs)

        # 检查是否在根目录范围内
        # 如果文件路径是以根目录开头，说明在范围内
        if not file_abs.startswith(root_abs + os.sep):
            # 完全相等也可以
            if file_abs != root_abs:
                return False

        # 禁止遍历到上级目录
        if '..' in os.path.relpath(file_abs, root_abs):
            return False

        return True

    def scan(self, root_dir: str) -> Iterator[Tuple[str, str]]:
        """扫描目录，返回 (文件路径, 内容)"""
        # 规范化根目录
        root_dir = os.path.abspath(root_dir)

        for root, dirs, files in os.walk(root_dir, topdown=True):
            # 过滤要排除的目录
            dirs[:] = [d for d in dirs if not self.should_exclude(os.path.join(root, d))]

            for file in files:
                file_path = os.path.join(root, file)

                # 安全检查：确保不越出工作目录
                if not self._is_safe_path(root_dir, file_path):
                    continue

                if self.should_exclude(file_path):
                    continue
                if not self.has_matching_extension(file):
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    yield file_path, content
                except UnicodeDecodeError:
                    # 二进制文件，跳过
                    continue
                except Exception:
                    # 其他读取错误，跳过
                    continue

    def count_files(self, root_dir: str) -> int:
        """统计将要扫描的文件数量"""
        count = 0
        for _, _ in self.scan(root_dir):
            count += 1
        return count

    def add_exclude_patterns(self, patterns: List[str]):
        """添加额外排除模式"""
        self.config.exclude_patterns.extend(patterns)
