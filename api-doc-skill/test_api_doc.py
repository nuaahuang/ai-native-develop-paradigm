"""api-doc Skill 测试脚本"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import detect_code_type, parse_code, parse_code
from parsers.java_parser import parse_java_code
from parsers.python_parser import parse_python_code
from parsers.generic_parser import parse_generic_code


def test_java_parser():
    """测试 Java 代码解析"""
    java_code = '''@GetMapping("/ai-gxs/plan/stage-report/{reportId}")
public ResponseEntity<ApiResponse<StageReportDTO>> getStageReport(
    @PathVariable String reportId,
    @RequestParam(required = false) String status
) {
    StageReportDTO report = reportService.getById(reportId);
    return ResponseEntity.ok(ApiResponse.success(report));
}'''
    
    print("=== 测试 Java 解析器 ===")
    result = parse_java_code(java_code)
    print(f"方法: {result['method']}")
    print(f"路径: {result['path']}")
    print(f"接口名称: {result['api_name']}")
    print(f"路径参数: {result['params']}")
    print(f"查询参数: {result['query_params']}")
    print(f"响应数据: {result['response']['data']}")
    print()


def test_python_parser():
    """测试 Python 代码解析"""
    python_code = '''@app.get("/ai-gxs/plan/stage-report/{reportId}")
def get_stage_report(
    reportId: str,
    status: Optional[str] = None
) -> ApiResponse[StageReportDTO]:
    """查询阶段报告详情"""
    report = report_service.get_by_id(reportId)
    return ApiResponse.success(report)'''
    
    print("=== 测试 Python 解析器 ===")
    result = parse_python_code(python_code)
    print(f"方法: {result['method']}")
    print(f"路径: {result['path']}")
    print(f"接口名称: {result['api_name']}")
    print(f"路径参数: {result['params']}")
    print(f"查询参数: {result['query_params']}")
    print(f"响应数据: {result['response']['data']}")
    print()


def test_generic_parser():
    """测试通用解析器"""
    generic_code = 'GET /api/users/{userId}/orders'
    
    print("=== 测试通用解析器 ===")
    result = parse_generic_code(generic_code)
    print(f"方法: {result['method']}")
    print(f"路径: {result['path']}")
    print(f"接口名称: {result['api_name']}")
    print(f"路径参数: {result['params']}")
    print()


def test_code_detection():
    """测试代码类型检测"""
    java_code = '@GetMapping("/api/test")'
    python_code = '@app.get("/api/test")'
    generic_code = 'GET /api/test'
    
    print("=== 测试代码类型检测 ===")
    print(f"Java 代码检测: {detect_code_type(java_code)}")
    print(f"Python 代码检测: {detect_code_type(python_code)}")
    print(f"通用代码检测: {detect_code_type(generic_code)}")
    print()


if __name__ == '__main__':
    test_code_detection()
    test_java_parser()
    test_python_parser()
    test_generic_parser()
    print("=== 所有测试完成 ===")