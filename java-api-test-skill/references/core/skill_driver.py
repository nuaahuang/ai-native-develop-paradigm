import argparse
import os
import json
import subprocess
import sys
import re
import random

from api_scanner import ApiScanner


# 类型约定：根据字段类型生成合适的示例值
_TYPE_SAMPLE_VALUES = {
    'string': {
        'default': lambda f: f"test_{f.get('name', 'field')}",
        'email': lambda f: "test@example.com",
        'uri': lambda f: "https://example.com",
        'date': lambda f: "2024-01-01",
        'date-time': lambda f: "2024-01-01T00:00:00Z",
        'password': lambda f: "Password123!",
        'byte': lambda f: "dGVzdA==",
        'binary': lambda f: "binary_data",
    },
    'integer': {'default': lambda f: random.randint(1, 10000)},
    'int': {'default': lambda f: random.randint(1, 10000)},
    'long': {'default': lambda f: random.randint(10000, 99999)},
    'number': {'default': lambda f: round(random.uniform(1.0, 999.99), 2)},
    'float': {'default': lambda f: round(random.uniform(1.0, 999.99), 2)},
    'double': {'default': lambda f: round(random.uniform(1.0, 999999.99), 2)},
    'boolean': {'default': lambda f: True},
    'bool': {'default': lambda f: True},
    'array': {'default': lambda f: []},
    'object': {'default': lambda f: {}},
}


def _generate_sample_value(field):
    """根据字段类型和格式生成合适的示例值"""
    field_type = field.get('type', 'string')
    field_format = field.get('format', '')
    field_name = field.get('name', 'field')
    
    type_map = _TYPE_SAMPLE_VALUES.get(field_type, {})
    if not type_map:
        return f"test_{field_name}"
    
    # 优先使用 format 匹配
    if field_format and field_format in type_map:
        return type_map[field_format](field)
    
    return type_map.get('default', lambda f: f"test_{f.get('name', 'field')}")(field)


def _generate_payload_from_fields(fields):
    """根据字段定义生成示例请求体"""
    payload = {}
    for field in fields:
        # 跳过 path 参数
        if field.get('in') == 'path':
            continue
        value = _generate_sample_value(field)
        payload[field['name']] = value
    
    return payload


def _build_dependency_chain(test_cases, base_path=''):
    """分析测试用例的依赖链
    
    规则：
    - POST 方法创建资源 (expected_status=201) → 提供 resource_id
    - 端点中包含 {id}/{pk}/{key} 等路径参数的 → 依赖 POST 创建测试
    
    Returns:
        list[dict]: 带依赖信息的测试用例列表
    """
    dep_configs = []
    
    # 先识别提供资源的测试（POST创建类）
    provider = None
    for tc in test_cases:
        method = tc.get('method', '').upper()
        if method == 'POST' and tc.get('expected_status', 200) == 201:
            provider = tc.get('endpoint_name', tc['name'])
            break
    
    for tc in test_cases:
        method = tc.get('method', '').upper()
        tc_name = tc.get('endpoint_name', tc['name'])
        
        # 判断路径是否有路径参数 {id}/{pk}/{key}
        path = tc.get('path', '')
        has_path_param = bool(re.search(r'\{(\w+)\}', path + base_path))
        
        if method == 'POST' and tc.get('expected_status', 200) == 201:
            # 创建资源的测试：存储返回的id
            dep_configs.append({
                'name': tc_name,
                'provides': 'resource_id',
                'depends_on': None,
            })
        elif has_path_param and provider:
            # 需要路径参数的测试：依赖 create 测试
            dep_configs.append({
                'name': tc_name,
                'provides': None,
                'depends_on': provider,
                'dep_param': 'resource_id',
            })
        elif method == 'PUT' and has_path_param and provider:
            dep_configs.append({
                'name': tc_name,
                'provides': 'updated_id',
                'depends_on': provider,
                'dep_param': 'resource_id',
            })
        elif method == 'DELETE' and has_path_param and provider:
            dep_configs.append({
                'name': tc_name,
                'provides': None,
                'depends_on': provider,
                'dep_param': 'resource_id',
            })
        else:
            dep_configs.append({
                'name': tc_name,
                'provides': None,
                'depends_on': None,
            })
    
    return dep_configs


def generate_api_file(module_name: str, base_path: str, endpoints: list):
    """生成接口定义文件"""
    content = '''import sys
import os

skill_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if skill_path not in sys.path:
    sys.path.insert(0, skill_path)

from references.core.http_client import HttpClient


class ''' + module_name.title() + '''Api:
    BASE_PATH = "''' + base_path + '''"

'''
    
    for endpoint in endpoints:
        method = endpoint['method'].lower()
        name = endpoint['name']
        path = endpoint.get('path', '')
        
        if method == 'get':
            content += '''    @classmethod
    def ''' + method + '_' + name + '''(cls, client: HttpClient, params=None):
        return client.get(f"{cls.BASE_PATH}''' + path + '''", params=params)

'''
        elif method in ['post', 'put']:
            content += '''    @classmethod
    def ''' + method + '_' + name + '''(cls, client: HttpClient, data):
        return client.''' + method + '''(f"{cls.BASE_PATH}''' + path + '''", json=data)

'''
        elif method == 'delete':
            content += '''    @classmethod
    def ''' + method + '_' + name + '''(cls, client: HttpClient):
        return client.''' + method + '''(f"{cls.BASE_PATH}''' + path + '''")

'''
    
    file_path = './apis/' + module_name + '_api.py'
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return file_path


def generate_test_file(module_name: str, test_cases: list, base_path: str = ''):
    """生成测试用例文件（数据类型感知 + 前置依赖链）
    
    Args:
        module_name: 模块名
        test_cases: 测试用例列表，每个元素可包含：
            - name: 方法名
            - method: HTTP方法
            - endpoint_name: 端点名
            - expected_status: 预期状态码
            - expected_keys: 预期响应键
            - fields: 字段定义列表 [{'name','type','format','required'}]
            - payload: 手动指定payload（可选，有则不用fields生成）
            - params: 查询参数（可选）
            - path: 路径后缀（可选）
        base_path: API基础路径（用于依赖分析）
    """
    class_name = module_name.title() + 'Api'
    test_class_name = 'Test' + module_name.title() + 'Api'
    
    content = '''import sys
import os

skill_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if skill_path not in sys.path:
    sys.path.insert(0, skill_path)

from references.core.base_test import BaseTest
from apis.''' + module_name + '''_api import ''' + class_name + '''


class ''' + test_class_name + '''(BaseTest):

'''
    
    # 构建依赖链
    dep_configs = _build_dependency_chain(test_cases, base_path)
    
    # 收集需要类变量的依赖
    class_vars = set()
    for dep in dep_configs:
        if dep.get('provides'):
            var_name = '_created_' + dep['provides']
            class_vars.add(var_name)
    for dep in dep_configs:
        if dep.get('dep_param'):
            var_name = '_created_' + dep['dep_param']
            class_vars.add(var_name)
    
    # 添加类变量（用于依赖共享）
    if class_vars:
        for var in sorted(class_vars):
            content += '    ' + var + ' = None\n'
        content += '\n'
    
    for i, test_case in enumerate(test_cases):
        name = test_case['name']
        desc = test_case.get('description', '测试' + name)
        method = test_case['method'].lower()
        endpoint_name = test_case.get('endpoint_name', name)
        expected_status = test_case.get('expected_status', 200)
        expected_keys = test_case.get('expected_keys', [])
        payload = test_case.get('payload')
        params = test_case.get('params')
        fields = test_case.get('fields', [])
        dep = dep_configs[i] if i < len(dep_configs) else {}
        
        # 依赖注解（注释中标注前置依赖）
        dep_annotation = ''
        if dep.get('depends_on'):
            dep_annotation = ' - 前置: ' + dep['depends_on']
        
        content += '''    def test_''' + name + '''(self):
        """''' + desc + dep_annotation + '''"""
'''
        
        if method == 'get':
            # GET 请求：可能有 params，也可能有依赖的路径参数
            if dep.get('dep_param'):
                var_name = '_created_' + dep['dep_param']
                content += '        if not self.__class__.' + var_name + ':\n'
                content += '            self.skipTest("请先执行前置测试: ' + dep['depends_on'] + '")\n\n'
                content += '        response = ' + class_name + '.' + method + '_' + endpoint_name + '(self.client, self.__class__.' + var_name + ')\n'
            elif params:
                content += '        params = ' + json.dumps(params) + '\n'
                content += '        response = ' + class_name + '.' + method + '_' + endpoint_name + '(self.client, params=params)\n'
            else:
                content += '        response = ' + class_name + '.' + method + '_' + endpoint_name + '(self.client)\n'
        
        elif method in ['post', 'put']:
            # POST/PUT：使用字段类型生成payload，或使用手动指定的payload
            if payload:
                payload_str = json.dumps(payload, indent=8, ensure_ascii=False)
                content += '        payload = ' + payload_str + '\n'
            elif fields:
                auto_payload = _generate_payload_from_fields(fields)
                payload_str = json.dumps(auto_payload, indent=8, ensure_ascii=False)
                content += '        # 根据接口数据类型自动生成\n'
                content += '        payload = ' + payload_str + '\n'
            else:
                content += '        payload = {\n            # 请求体\n        }\n'
            
            if dep.get('dep_param'):
                var_name = '_created_' + dep['dep_param']
                content += '        if not self.__class__.' + var_name + ':\n'
                content += '            self.skipTest("请先执行前置测试: ' + dep['depends_on'] + '")\n\n'
                content += '        response = ' + class_name + '.' + method + '_' + endpoint_name + '(self.client, self.__class__.' + var_name + ', payload)\n'
            else:
                content += '        response = ' + class_name + '.' + method + '_' + endpoint_name + '(self.client, payload)\n'
        
        elif method == 'delete':
            if dep.get('dep_param'):
                var_name = '_created_' + dep['dep_param']
                content += '        if not self.__class__.' + var_name + ':\n'
                content += '            self.skipTest("请先执行前置测试: ' + dep['depends_on'] + '")\n\n'
                content += '        response = ' + class_name + '.' + method + '_' + endpoint_name + '(self.client, self.__class__.' + var_name + ')\n'
            else:
                content += '        response = ' + class_name + '.' + method + '_' + endpoint_name + '(self.client)\n'
        
        # 状态码断言
        status_method = {
            200: 'ok',
            201: 'created',
            204: 'no_content',
            400: 'bad_request',
            401: 'unauthorized',
            403: 'forbidden',
            404: 'not_found'
        }.get(expected_status, 'ok')
        
        content += '        self.assert_status_' + status_method + '(response)\n'
        
        # 响应字段断言 + 存储依赖资源ID
        if expected_keys:
            content += '        data = self.assert_response_json(response, ' + str(expected_keys) + ')\n'
        else:
            content += '        data = response.json()\n'
        
        # 如果是创建资源的测试，存储返回的ID供后续测试使用
        if dep.get('provides'):
            var_name = '_created_' + dep['provides']
            # 尝试多个可能的ID字段名
            id_fields = ['id', dep['provides'], dep['provides'].replace('resource_', '')]
            for idf in id_fields:
                if idf != dep['provides'].replace('resource_', ''):
                    pass
            content += '        self.__class__.' + var_name + ' = data.get("id")\n'
        
        content += '\n'
    
    file_path = './output/tests/test_' + module_name + '.py'
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return file_path


def run_tests(include_pattern=None, exclude_pattern=None, headers=None, base_url=None):
    """执行测试并返回结果"""
    run_tests_path = os.path.join(os.path.dirname(__file__), 'run_tests.py')
    cmd = [sys.executable, run_tests_path]
    
    if include_pattern:
        cmd.extend(['--include', include_pattern])
    if exclude_pattern:
        cmd.extend(['--exclude', exclude_pattern])
    
    env = os.environ.copy()
    if headers:
        env['API_HEADERS'] = json.dumps(headers)
    if base_url:
        env['API_BASE_URL'] = base_url
    
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, cwd=os.getcwd())
    
    return {
        'stdout': result.stdout,
        'stderr': result.stderr,
        'returncode': result.returncode
    }


def list_api_modules():
    """列出所有已定义的接口模块"""
    modules = []
    api_dir = '../apis'
    
    if os.path.exists(api_dir):
        for filename in os.listdir(api_dir):
            if filename.endswith('_api.py') and not filename.startswith('__init__'):
                module_name = filename.replace('_api.py', '')
                modules.append(module_name)
    
    return modules


def list_test_files():
    """列出所有测试文件"""
    tests = []
    test_dir = '../output/tests'
    
    if os.path.exists(test_dir):
        for filename in os.listdir(test_dir):
            if filename.startswith('test_') and filename.endswith('.py'):
                tests.append(filename)
    
    return tests


def init_project():
    """初始化项目配置"""
    # 从模板目录读取配置模板
    template_path = os.path.join(
        os.path.dirname(__file__), 
        '../templates/config.yaml'
    )
    
    if not os.path.exists(template_path):
        return {'status': 'error', 'message': f'配置模板不存在: {template_path}'}
    
    with open(template_path, 'r', encoding='utf-8') as f:
        config_content = f.read()
    
    config_path = os.path.join(os.getcwd(), 'api_test_config.yaml')
    
    if os.path.exists(config_path):
        return {'status': 'warning', 'message': f'配置文件已存在: {config_path}'}
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    # 创建必要的目录
    os.makedirs('./apis', exist_ok=True)
    os.makedirs('./output/tests', exist_ok=True)
    os.makedirs('./output/reports', exist_ok=True)
    
    # 创建 apis/__init__.py
    with open('./apis/__init__.py', 'w', encoding='utf-8') as f:
        f.write('''import os
import importlib

__all__ = []

for filename in os.listdir(os.path.dirname(__file__)):
    if filename.endswith('_api.py') and filename != '__init__.py':
        module_name = filename[:-3]
        __all__.append(module_name)
        try:
            importlib.import_module(f'.{module_name}', __name__)
        except ImportError:
            pass

__version__ = '1.0.0'
''')
    
    return {
        'status': 'success',
        'message': '项目初始化完成！',
        'config_file': config_path,
        'directories': ['./apis', './output/tests', './output/reports']
    }


def scan_apis(source_type: str, source_path: str, group_by_module: bool = True, detect_changes: bool = False, save_snapshot: bool = False):
    """扫描接口并返回结果"""
    if source_type == 'java':
        apis = ApiScanner.scan_java_source(source_path)
    elif source_type == 'swagger':
        apis = ApiScanner.scan_swagger(source_path)
    else:
        return {'status': 'error', 'message': f'不支持的扫描类型: {source_type}'}
    
    result = {'status': 'success', 'total': len(apis)}
    
    if detect_changes:
        changes = ApiScanner.compare_snapshots(apis)
        result['changes'] = changes
    
    if save_snapshot:
        snapshot_path = ApiScanner.save_snapshot(apis)
        result['snapshot_path'] = snapshot_path
    
    if group_by_module:
        grouped = ApiScanner.group_by_module(apis)
        result['grouped'] = grouped
    else:
        result['apis'] = apis
    
    return result


def main():
    parser = argparse.ArgumentParser(description='Java API测试自动化工具 - Skill驱动接口')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 初始化项目
    init_parser = subparsers.add_parser('init', help='初始化项目配置')
    
    # 扫描接口
    scan_parser = subparsers.add_parser('scan', help='扫描接口')
    scan_parser.add_argument('--type', required=True, choices=['java', 'swagger'], 
                            help='扫描类型：java（源码）或 swagger（接口文档）')
    scan_parser.add_argument('--path', required=True, help='扫描路径（目录、文件或URL）')
    scan_parser.add_argument('--group', action='store_true', default=True, 
                            help='是否按模块分组')
    scan_parser.add_argument('--detect-changes', action='store_true', default=False,
                            help='检测接口变更（对比历史快照）')
    scan_parser.add_argument('--save-snapshot', action='store_true', default=False,
                            help='保存当前扫描结果为快照')
    
    # 生成接口定义
    gen_api_parser = subparsers.add_parser('gen-api', help='生成接口定义文件')
    gen_api_parser.add_argument('--module', required=True, help='模块名')
    gen_api_parser.add_argument('--base-path', required=True, help='基础路径')
    gen_api_parser.add_argument('--endpoints', required=True, help='端点定义JSON')
    
    # 生成测试用例
    gen_test_parser = subparsers.add_parser('gen-test', help='生成测试用例文件')
    gen_test_parser.add_argument('--module', required=True, help='模块名')
    gen_test_parser.add_argument('--test-cases', required=True, help='测试用例定义JSON')
    gen_test_parser.add_argument('--base-path', default='', help='API基础路径（用于依赖分析）')
    
    # 运行测试
    run_parser = subparsers.add_parser('run', help='运行测试')
    run_parser.add_argument('--all', action='store_true', help='运行所有测试')
    run_parser.add_argument('--include', help='包含的测试模块（正则）')
    run_parser.add_argument('--exclude', help='排除的测试模块（正则）')
    run_parser.add_argument('--headers', help='Headers JSON')
    run_parser.add_argument('--base-url', help='API基础URL')
    
    # 列出模块
    list_parser = subparsers.add_parser('list', help='列出可用模块')
    list_parser.add_argument('--type', choices=['api', 'test'], default='api', help='类型')
    
    args = parser.parse_args()
    
    if args.command == 'scan':
        result = scan_apis(args.type, args.path, args.group, args.detect_changes, args.save_snapshot)
        print(json.dumps(result))
    
    elif args.command == 'gen-api':
        try:
            endpoints = json.loads(args.endpoints)
            file_path = generate_api_file(args.module, args.base_path, endpoints)
            print(json.dumps({'status': 'success', 'file': file_path}))
        except Exception as e:
            print(json.dumps({'status': 'error', 'message': str(e)}))
    
    elif args.command == 'gen-test':
        try:
            test_cases = json.loads(args.test_cases)
            file_path = generate_test_file(args.module, test_cases, args.base_path)
            print(json.dumps({'status': 'success', 'file': file_path}))
        except Exception as e:
            print(json.dumps({'status': 'error', 'message': str(e)}))
    
    elif args.command == 'init':
        result = init_project()
        print(json.dumps(result))
    
    elif args.command == 'run':
        include_pattern = None if args.all else args.include
        headers = json.loads(args.headers) if args.headers else None
        result = run_tests(include_pattern, args.exclude, headers, args.base_url)
        print(json.dumps(result))
    
    elif args.command == 'list':
        if args.type == 'api':
            modules = list_api_modules()
        else:
            modules = list_test_files()
        print(json.dumps({'status': 'success', 'items': modules}))


if __name__ == '__main__':
    main()
