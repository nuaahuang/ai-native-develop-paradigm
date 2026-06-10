"""通用代码解析器 - 处理纯文本 URL 和其他格式"""

import re


def parse_generic_code(code: str) -> dict:
    """解析通用格式的接口代码"""
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
    
    # 尝试解析 HTTP 方法和路径
    http_pattern = r'(GET|POST|PUT|DELETE|PATCH)\s+(/(?:[\w/-]+|\{[\w]+\})+)'
    match = re.search(http_pattern, code)
    if match:
        result['method'] = match.group(1)
        result['path'] = match.group(2)
    
    # 如果没有找到，尝试其他格式
    if not result['path']:
        # 查找路径
        path_pattern = r'/(?:[\w/-]+|\{[\w]+\})+'
        match = re.search(path_pattern, code)
        if match:
            result['path'] = match.group(0)
    
    # 提取路径参数
    if result['path']:
        path_params = re.findall(r'\{(\w+)\}', result['path'])
        for param in path_params:
            result['params'].append({
                'name': param,
                'type': 'String',
                'required': True,
                'description': ''
            })
    
    # 尝试从路径推断接口名称
    if not result['api_name'] and result['path']:
        result['api_name'] = path_to_name(result['path'])
    
    # 生成示例响应数据
    if not result['response']['data']:
        result['response']['data'] = generate_sample_response(result['path'])
    
    return result


def path_to_name(path: str) -> str:
    """从路径生成接口名称"""
    mappings = {
        'get': '查询',
        'list': '列表',
        'detail': '详情',
        'create': '创建',
        'update': '更新',
        'delete': '删除',
        'report': '报告',
        'stage': '阶段',
        'plan': '计划',
        'user': '用户',
        'order': '订单',
        'product': '商品',
        'api': ''
    }
    
    # 移除前缀和后缀
    path_parts = path.strip('/').split('/')
    name_parts = []
    
    for part in path_parts:
        # 移除参数
        if '{' in part:
            continue
        # 转换
        part_lower = part.lower()
        name_parts.append(mappings.get(part_lower, part))
    
    return ''.join(name_parts)


def generate_sample_response(path: str) -> dict:
    """根据路径生成示例响应数据"""
    if 'report' in path.lower():
        return {
            'reportId': 'RPT-20240101-001',
            'stageType': 1,
            'stage': '阶段一',
            'day': 28,
            'totalDays': 90,
            'createdAt': '2024-01-28T10:30:00'
        }
    elif 'user' in path.lower():
        return {
            'userId': 'U001',
            'username': '张三',
            'email': 'zhangsan@example.com',
            'status': 1
        }
    elif 'order' in path.lower():
        return {
            'orderId': 'ORD-20240101-001',
            'userId': 'U001',
            'status': '已支付',
            'totalAmount': 199.99
        }
    else:
        return {
            'id': '1',
            'name': '示例数据'
        }