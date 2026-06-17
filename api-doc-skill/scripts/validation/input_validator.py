from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from scripts.models.api_info import ApiInfo


class ErrorCode(Enum):
    """错误码枚举"""
    EMPTY_CODE = "EMPTY_CODE"
    NO_FRAMEWORK_DETECTED = "NO_FRAMEWORK_DETECTED"
    NO_INTERFACE_FOUND = "NO_INTERFACE_FOUND"
    INCOMPLETE_INFO = "INCOMPLETE_INFO"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INVALID_OUTPUT_PATH = "INVALID_OUTPUT_PATH"
    PARSE_ERROR = "PARSE_ERROR"


@dataclass
class ValidationError:
    """验证错误"""
    code: ErrorCode
    message: str
    suggestion: Optional[str] = None

    def to_string(self) -> str:
        """格式化错误信息"""
        base = f"[{self.code.value}] {self.message}"
        if self.suggestion:
            base += f"\n💡 建议: {self.suggestion}"
        return base


@dataclass
class ValidationResult:
    """验证结果"""
    valid: bool
    errors: List[ValidationError] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    def add_error(self, error: ValidationError):
        self.errors.append(error)
        self.valid = False

    def get_error_messages(self) -> List[str]:
        return [e.to_string() for e in self.errors]

    def is_valid(self) -> bool:
        return self.valid and len(self.errors) == 0


class InputValidator:
    """输入验证器"""

    @staticmethod
    def validate_code(code: str) -> ValidationResult:
        """验证输入代码"""
        result = ValidationResult(valid=True)

        # 检查空代码
        code = code.strip()
        if not code:
            result.add_error(ValidationError(
                code=ErrorCode.EMPTY_CODE,
                message="选中的代码为空",
                suggestion="请在编辑器中选中包含接口定义的代码后再试"
            ))
            return result

        # 检查最小长度
        if len(code) < 10:
            result.add_error(ValidationError(
                code=ErrorCode.INCOMPLETE_INFO,
                message="选中的代码过短，可能不包含完整接口定义",
                suggestion="请选中包含完整路由注解和函数定义的代码"
            ))

        return result

    @staticmethod
    def validate_output_path(output_path: str) -> ValidationResult:
        """验证输出路径"""
        result = ValidationResult(valid=True)

        if not output_path:
            result.add_error(ValidationError(
                code=ErrorCode.INVALID_OUTPUT_PATH,
                message="输出文件路径不能为空",
                suggestion="请指定 --output 参数，例如: --output=\"./docs/api.md\""
            ))

        return result

    @staticmethod
    def validate_parse_result(api_info: Optional[ApiInfo]) -> ValidationResult:
        """验证解析结果"""
        result = ValidationResult(valid=True)

        if api_info is None:
            result.add_error(ValidationError(
                code=ErrorCode.NO_INTERFACE_FOUND,
                message="无法从选中代码中解析出接口定义",
                suggestion="请确保代码中包含完整的路由注解/装饰器定义。\n当前支持的框架: Java Spring, Python FastAPI, Django REST Framework, Flask, Express, Go Gin"
            ))
            return result

        # 检查必填字段
        if not api_info.http_method or not api_info.path:
            result.add_error(ValidationError(
                code=ErrorCode.INCOMPLETE_INFO,
                message="解析出的信息不完整，缺少 HTTP 方法或路径",
                suggestion="请检查代码格式是否正确，确保路由定义完整"
            ))

        if not api_info.name:
            # 这是警告不是错误，可以继续
            pass

        return result

    @staticmethod
    def validate_scan_dir(scan_dir: str) -> ValidationResult:
        """验证扫描目录"""
        import os
        result = ValidationResult(valid=True)

        if not os.path.exists(scan_dir):
            result.add_error(ValidationError(
                code=ErrorCode.FILE_NOT_FOUND,
                message=f"扫描目录不存在: {scan_dir}",
                suggestion="请检查目录路径是否正确"
            ))
        elif not os.path.isdir(scan_dir):
            result.add_error(ValidationError(
                code=ErrorCode.FILE_NOT_FOUND,
                message=f"{scan_dir} 不是一个目录",
                suggestion="请指定一个存在的目录路径"
            ))
        else:
            # 安全检查：确保扫描目录在当前工作目录范围内
            cwd = os.getcwd()
            cwd_abs = os.path.abspath(cwd)
            scan_abs = os.path.abspath(scan_dir)

            cwd_abs = os.path.normpath(cwd_abs)
            scan_abs = os.path.normpath(scan_abs)

            # 检查是否在当前工作目录范围内
            if not scan_abs.startswith(cwd_abs + os.sep) and scan_abs != cwd_abs:
                result.add_error(ValidationError(
                    code=ErrorCode.PERMISSION_DENIED,
                    message=f"扫描路径超出当前工作目录范围: {scan_dir}",
                    suggestion="只能扫描当前工作目录范围内的目录"
                ))

            # 禁止访问上级目录
            if '..' in os.path.relpath(scan_abs, cwd_abs):
                result.add_error(ValidationError(
                    code=ErrorCode.PERMISSION_DENIED,
                    message=f"扫描路径包含 .. ，禁止访问上级目录: {scan_dir}",
                    suggestion="请使用当前目录范围内的相对路径"
                ))

        return result
