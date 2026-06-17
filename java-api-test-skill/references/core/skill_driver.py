import argparse
import os
import json
import subprocess
import sys

from api_scanner import ApiScanner


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


def generate_test_file(module_name: str, test_cases: list):
    """生成测试用例文件"""
    content = '''import sys
import os

skill_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if skill_path not in sys.path:
    sys.path.insert(0, skill_path)

from references.core.base_test import BaseTest
from apis.''' + module_name + '''_api import ''' + module_name.title() + '''Api


class Test''' + module_name.title() + '''Api(BaseTest):

'''
    
    for test_case in test_cases:
        name = test_case['name']
        desc = test_case.get('description', '测试' + name)
        method = test_case['method'].lower()
        endpoint_name = test_case.get('endpoint_name', name)
        expected_status = test_case.get('expected_status', 200)
        expected_keys = test_case.get('expected_keys', [])
        payload = test_case.get('payload')
        params = test_case.get('params')
        
        content += '''    def test_''' + name + '''(self):
        """''' + desc + '''"""
'''
        
        if method == 'get':
            if params:
                content += '        params = ' + json.dumps(params) + '\n'
                content += '        response = ' + module_name.title() + 'Api.' + method + '_' + endpoint_name + '(self.client, params=params)\n'
            else:
                content += '        response = ' + module_name.title() + 'Api.' + method + '_' + endpoint_name + '(self.client)\n'
        elif method in ['post', 'put']:
            if payload:
                content += '        payload = ' + json.dumps(payload, ensure_ascii=False) + '\n'
            else:
                content += '        payload = {\n            # 请求体\n        }\n'
            content += '        response = ' + module_name.title() + 'Api.' + method + '_' + endpoint_name + '(self.client, payload)\n'
        elif method == 'delete':
            content += '        response = ' + module_name.title() + 'Api.' + method + '_' + endpoint_name + '(self.client)\n'
        
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
        
        if expected_keys:
            content += '        self.assert_response_json(response, ' + str(expected_keys) + ')\n'
        
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
            file_path = generate_test_file(args.module, test_cases)
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
