"""Python FastAPI 代码解析器"""

import re


def parse_python_code(code: str) -> dict:
    """解析 Python FastAPI 接口代码"""
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
    method_pattern = r'@app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']\s*\)'
    match = re.search(method_pattern, code)
    if match:
        result['method'] = match.group(1).upper()
        result['path'] = match.group(2)
    
    # 提取函数名作为接口名称
    func_name_pattern = r'def\s+(\w+)\s*\('
    match = re.search(func_name_pattern, code)
    if match:
        result['api_name'] = snake_case_to_chinese(match.group(1))
    
    # 提取参数
    params_pattern = r'def\s+\w+\s*\((.*?)\)'
    match = re.search(params_pattern, code, re.DOTALL)
    if match:
        params_str = match.group(1)
        param_lines = params_str.replace('\n', '').split(',')
        for param in param_lines:
            param = param.strip()
            if not param:
                continue
            # 检查是否有默认值（非必填）
            if '=' in param and 'Optional' not in param:
                # 有默认值，是查询参数
                parts = param.split('=')
                name_type = parts[0].strip()
                if ':' in name_type:
                    name, type_name = name_type.split(':')
                    result['query_params'].append({
                        'name': name.strip(),
                        'type': type_name.strip().replace('Optional[', '').replace(']', ''),
                        'required': False,
                        'description': ''
                    })
                else:
                    result['query_params'].append({
                        'name': name_type,
                        'type': 'str',
                        'required': False,
                        'description': ''
                    })
            elif ':' in param:
                # 无默认值，检查是否是路径参数（路径中有同名参数）
                name_type = param.split(':')
                name = name_type[0].strip()
                type_name = name_type[1].strip().replace('Optional[', '').replace(']', '').strip()
                # 清理类型中的空格和其他字符
                type_name = type_name.split()[0] if type_name else 'str'
                if '{' + name + '}' in result['path']:
                    result['params'].append({
                        'name': name,
                        'type': type_name,
                        'required': True,
                        'description': ''
                    })
                else:
                    result['query_params'].append({
                        'name': name,
                        'type': type_name,
                        'required': True,
                        'description': ''
                    })
    
    # 提取返回类型（支持多行）
    return_type_pattern = r'->\s*(\w+)<(\w+)>'
    match = re.search(return_type_pattern, code.replace('\n', ' '))
    if match:
        result['response']['data'] = generate_sample_data(match.group(2))
    elif result['api_name']:
        # 如果没有找到返回类型，根据接口名称生成示例数据
        if 'report' in result['api_name'] or 'Report' in result['api_name']:
            result['response']['data'] = generate_sample_data('StageReportDTO')
        elif 'user' in result['api_name'] or 'User' in result['api_name']:
            result['response']['data'] = generate_sample_data('UserDTO')
        elif 'order' in result['api_name'] or 'Order' in result['api_name']:
            result['response']['data'] = generate_sample_data('OrderDTO')
    elif 'report' in result['path'].lower():
        # 根据路径中的关键词生成示例数据
        result['response']['data'] = generate_sample_data('StageReportDTO')
    
    return result


def snake_case_to_chinese(name: str) -> str:
    """将下划线命名转换为中文描述"""
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
        'product': '商品'
    }
    
    words = name.split('_')
    result = []
    for word in words:
        result.append(mappings.get(word, word))
    
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