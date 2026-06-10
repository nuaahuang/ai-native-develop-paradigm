"""Java Spring Boot 代码解析器"""

import re


def parse_java_code(code: str) -> dict:
    """解析 Java Spring Boot 接口代码"""
    result = {
        'method': 'GET',
        'path': '',
        'api_name': '',
        'params': [],
        'query_params': [],
        'response': {
            'code': 200,
            'message': 'success',
            'data': {}
        },
        'file_name': ''
    }
    
    # 提取 HTTP 方法和路径
    method_pattern = r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\s*\(\s*["\']([^"\']+)["\']\s*\)'
    match = re.search(method_pattern, code)
    if match:
        result['method'] = match.group(1).replace('Mapping', '')
        result['path'] = match.group(2)
    
    # 提取方法名作为接口名称（支持多行和泛型）
    method_name_pattern = r'public\s+[\w<>\[\].,]+\s+(\w+)\s*\('
    match = re.search(method_name_pattern, code.replace('\n', ' '))
    if match:
        result['api_name'] = camel_case_to_chinese(match.group(1))
    
    # 提取路径参数 @PathVariable
    path_var_pattern = r'@PathVariable\s*(?:\w+)?\s*(\w+)'
    path_vars = re.findall(path_var_pattern, code)
    for var in path_vars:
        result['params'].append({
            'name': var,
            'type': 'String',
            'required': True,
            'description': ''
        })
    
    # 提取查询参数 @RequestParam
    query_param_pattern = r'@RequestParam\s*(?:\(.*?\))?\s*(?:\w+)?\s*(\w+)'
    query_params = re.findall(query_param_pattern, code)
    for var in query_params:
        result['query_params'].append({
            'name': var,
            'type': 'String',
            'required': False,
            'description': ''
        })
    
    # 提取返回类型
    return_type_pattern = r'ResponseEntity<(\w+)<(\w+)>>'
    match = re.search(return_type_pattern, code)
    if match:
        result['response']['data'] = generate_sample_data(match.group(2))
    
    return result


def camel_case_to_chinese(name: str) -> str:
    """将驼峰命名转换为中文描述"""
    mappings = {
        'get': '查询',
        'post': '创建',
        'create': '创建',
        'put': '更新',
        'update': '更新',
        'delete': '删除',
        'list': '列表',
        'detail': '详情',
        'report': '报告',
        'stage': '阶段',
        'plan': '计划',
        'user': '用户',
        'order': '订单',
        'product': '商品',
        'Stage': '阶段',
        'Plan': '计划',
        'ById': '详情',
        'By': '按'
    }
    
    # 分割驼峰
    words = re.findall(r'[A-Z][a-z]*', name)
    if not words:
        words = [name]
    
    # 转换每个单词
    result = []
    for word in words:
        lower_word = word.lower()
        result.append(mappings.get(word, mappings.get(lower_word, word)))
    
    return ''.join(result)


def generate_sample_data(class_name: str) -> dict:
    """根据类名生成示例数据"""
    sample_data = {
        'StageReportDTO': {
            'reportId': 'RPT-20240101-001',
            'stageType': 1,
            'stageTypeDesc': '中间阶段',
            'day': 28,
            'stage': '阶段一',
            'totalDays': 90,
            'achievements': '完成基础体能训练',
            'currentChanges': '睡眠质量提升',
            'createdAt': '2024-01-28T10:30:00'
        },
        'UserDTO': {
            'userId': 'U001',
            'username': '张三',
            'email': 'zhangsan@example.com',
            'status': 1
        },
        'OrderDTO': {
            'orderId': 'ORD-20240101-001',
            'userId': 'U001',
            'status': '已支付',
            'totalAmount': 199.99,
            'createTime': '2024-01-28T10:30:00'
        }
    }
    return sample_data.get(class_name, {'id': '1', 'name': '示例数据'})