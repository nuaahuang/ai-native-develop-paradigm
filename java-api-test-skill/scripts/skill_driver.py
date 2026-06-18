import argparse
import os
import json
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
    """智能构建前置依赖链：匹配输入参数 ↔ 响应字段
    
    对每个接口，提取其"输入需求"（路径参数/查询参数/请求体字段），
    与其他接口的"响应提供"（响应字段）做交叉匹配，构建数据流链。
    
    例如：
      POST /users → 响应 {id, username, email}
      GET /users/{user_id} → 需要 user_id ← 匹配到 POST 的 id
      POST /orders {user_id} → 需要 user_id ← 匹配到 POST 的 id
    
    Returns:
        list[dict]: 每个元素包含:
            - name: 用例名
            - needs: set[str] 需要的外部输入
            - provides: set[str] 能提供的响应字段
            - depends_on: dict[str, str] {需要参数 → 提供该参数的测试名}
    """
    # Step 1: 提取每个测试用例的"需求"和"供给"
    test_info = []
    for tc in test_cases:
        tc_name = tc.get('endpoint_name', tc['name'])
        method = tc.get('method', '').upper()
        expected_status = tc.get('expected_status', 200)
        
        # 提取输入的参数名
        # - 路径参数: 外部依赖（需要从其他API获取）
        # - 查询参数: 外部依赖（需要从其他API获取）
        # - 请求体字段: 仅 _id 结尾的引用字段才作为外部依赖
        needs = set()
        path = tc.get('path', '')
        path_params = re.findall(r'\{(\w+)\}', path + base_path)
        needs.update(p.lower() for p in path_params)
        
        params = tc.get('params', {})
        if params:
            needs.update(k.lower() for k in params.keys())
        
        fields = tc.get('fields', [])
        if fields:
            for f in fields:
                fn = f.get('name', '').lower()
                # 只有引用字段（_id结尾）才作为外部依赖
                if fn.endswith('_id') or fn.endswith('_ids'):
                    needs.add(fn)
        
        # 提取响应的字段名（从 expected_keys + 自动推理）
        provides = set()
        for key in tc.get('expected_keys', []):
            provides.add(key.lower())
        
        # POST 201 自动提供 id
        if method == 'POST' and expected_status == 201:
            provides.add('id')
        
        # 如果路径有 {id}，且方法不是 POST，说明消费资源
        is_consumer = bool(path_params) and method != 'POST'
        
        test_info.append({
            'name': tc_name,
            'needs': needs,
            'provides': provides,
            'method': method,
            'expected_status': expected_status,
            'path_params': [p.lower() for p in path_params],
        })
    
    # Step 2: 交叉匹配构建依赖图
    # 匹配规则：测试B的"需求" ↔ 测试A的"供给"
    # - 精确匹配: 参数名 == 字段名
    # - 后缀匹配: user_id → id (如果 user_id 没精确匹配到，但 A 提供了 id)
    dep_configs = []
    
    for i, info in enumerate(test_info):
        dep = {
            'name': info['name'],
            'needs': info['needs'],
            'provides': info['provides'],
            'depends_on': {},       # {参数名: 提供该参数的测试名}
            'dep_mapping': {},      # {参数名: 存储变量名}
        }
        
        for need in info['needs']:
            # 精确匹配（只向前查找，防止循环依赖）
            matched = None
            for j, other in enumerate(test_info):
                if j >= i:  # 只能依赖排在前面的测试
                    break
                if need in other['provides']:
                    matched = (other['name'], need)
                    break
            
            # 后缀匹配: xxx_id → id, xxx_name → name（只向前查找）
            if not matched:
                for j, other in enumerate(test_info):
                    if j >= i:
                        break
                    for provide in other['provides']:
                        if need.endswith('_' + provide) or need.endswith(provide):
                            matched = (other['name'], provide)
                            break
                    if matched:
                        break
            
            if matched:
                provider_name, provide_key = matched
                dep['depends_on'][need] = provider_name
                dep['dep_mapping'][need] = '_stored__' + provider_name + '__' + provide_key
        
        dep_configs.append(dep)
    
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
    
    file_path = './output/apis/' + module_name + '_api.py'
    os.makedirs('./output/apis', exist_ok=True)
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
from output.apis.''' + module_name + '''_api import ''' + class_name + '''


class ''' + test_class_name + '''(BaseTest):

'''
    
    # 构建依赖链
    dep_configs = _build_dependency_chain(test_cases, base_path)
    
    # 收集所有需要存储到类变量的字段
    # 格式: {变量名 → 提供该值的测试名.字段名 注释}
    all_store_vars = {}
    for dep in dep_configs:
        # 提供者：需要存储响应字段
        for provide_field in dep.get('provides', set()):
            var_name = '_stored__' + dep['name'] + '__' + provide_field
            all_store_vars[var_name] = (dep['name'], provide_field)
        
        # 消费者：依赖的变量也需要声明
        for need, mapping_var in dep.get('dep_mapping', {}).items():
            all_store_vars[mapping_var] = (mapping_var, '')
    
    # 添加类变量声明（所有存储变量初始化为 None）
    if all_store_vars:
        for var_name in sorted(all_store_vars.keys()):
            content += '    ' + var_name + ' = None\n'
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
        
        # 依赖注解（标注数据从哪个测试来）
        dep_annotation = ''
        if dep.get('depends_on'):
            providers = sorted(set(dep['depends_on'].values()))
            dep_annotation = ' - 数据源: ' + ', '.join(providers)
        
        content += '''    def test_''' + name + '''(self):
        """''' + desc + dep_annotation + '''"""
'''
        
        # 依赖检查：所有前置依赖的值必须存在
        if dep.get('dep_mapping'):
            all_providers = sorted(set(dep['dep_mapping'].values()))
            provider_names = sorted(set(dep['depends_on'].values()))
            for provider_name in provider_names:
                # 找这个提供者的所有依赖变量
                provider_vars = []
                for need, mapping_var in dep['dep_mapping'].items():
                    if dep['depends_on'].get(need) == provider_name:
                        provider_vars.append(mapping_var)
                
                # 生成 skip 检查
                check_conditions = []
                for mapping_var in provider_vars:
                    check_conditions.append('not self.__class__.' + mapping_var)
                if check_conditions:
                    condition_str = ' or '.join(check_conditions)
                    content += '        if ' + condition_str + ':\n'
                    content += '            self.skipTest("请先执行前置测试: ' + provider_name + '")\n'
                content += '\n'
        
        # 构建 API 调用参数
        # 确定需要从存储变量中作为参数传递给 API 调用的值
        call_kwargs = []
        path_arg = None  # 路径参数的实参
        
        # 检查路径参数
        path = test_case.get('path', '')
        path_params = re.findall(r'\{(\w+)\}', path + base_path)
        if path_params:
            first_path_param = path_params[0].lower()
            if first_path_param in dep.get('dep_mapping', {}):
                path_arg = dep['dep_mapping'][first_path_param]
        
        # 检查查询参数 - 如果有依赖则在方法内构建
        has_param_deps = False
        if params:
            for param_key in params:
                param_lower = param_key.lower()
                if param_lower in dep.get('dep_mapping', {}):
                    has_param_deps = True
            
        # GET 请求
        if method == 'get':
            if path_arg:
                content += '        response = ' + class_name + '.' + method + '_' + endpoint_name + '(self.client, self.__class__.' + path_arg + ')\n'
            elif has_param_deps:
                content += '        params = {\n'
                for param_key, param_val in params.items():
                    param_lower = param_key.lower()
                    if param_lower in dep.get('dep_mapping', {}):
                        content += '            "' + param_key + '": self.__class__.' + dep['dep_mapping'][param_lower] + ',\n'
                    else:
                        content += '            "' + param_key + '": ' + json.dumps(param_val) + ',\n'
                content += '        }\n'
                content += '        response = ' + class_name + '.' + method + '_' + endpoint_name + '(self.client, params=params)\n'
            elif params:
                content += '        params = ' + json.dumps(params) + '\n'
                content += '        response = ' + class_name + '.' + method + '_' + endpoint_name + '(self.client, params=params)\n'
            else:
                content += '        response = ' + class_name + '.' + method + '_' + endpoint_name + '(self.client)\n'
        
        # POST/PUT 请求
        elif method in ['post', 'put']:
            # 构建 payload
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
            
            # 检查 payload 中是否有字段需要从依赖获取
            payload_has_deps = False
            if fields:
                for field in fields:
                    field_name = field.get('name', '').lower()
                    if field_name in dep.get('dep_mapping', {}):
                        payload_has_deps = True
                        break
            
            if payload_has_deps:
                # 用依赖值覆盖 payload 中的对应字段
                content += '        # 用前置依赖数据覆盖 payload\n'
                for field in fields:
                    field_name = field.get('name', '').lower()
                    if field_name in dep.get('dep_mapping', {}):
                        mapping_var = dep['dep_mapping'][field_name]
                        content += '        payload["' + field.get('name', '') + '"] = self.__class__.' + mapping_var + '\n'
                content += '\n'
            
            if path_arg:
                content += '        response = ' + class_name + '.' + method + '_' + endpoint_name + '(self.client, self.__class__.' + path_arg + ', payload)\n'
            else:
                content += '        response = ' + class_name + '.' + method + '_' + endpoint_name + '(self.client, payload)\n'
        
        # DELETE 请求
        elif method == 'delete':
            if path_arg:
                content += '        response = ' + class_name + '.' + method + '_' + endpoint_name + '(self.client, self.__class__.' + path_arg + ')\n'
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
        
        # 响应字段断言
        if expected_keys:
            content += '        data = self.assert_response_json(response, ' + str(expected_keys) + ')\n'
        else:
            content += '        data = response.json()\n'
        
        # 存储该测试能提供的所有响应值（供后续测试依赖）
        for provide_field in sorted(dep.get('provides', set())):
            if provide_field == 'id' and provide_field not in test_case.get('expected_keys', []):
                # id 是自动推理的，用 data.get("id")
                content += '        self.__class__._stored__' + dep['name'] + '__id = data.get("id")\n'
            elif provide_field in [k.lower() for k in expected_keys]:
                content += '        self.__class__._stored__' + dep['name'] + '__' + provide_field + ' = data.get("' + provide_field + '")\n'
        
        content += '\n'
    
    file_path = './output/tests/test_' + module_name + '.py'
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return file_path


def list_api_modules():
    """列出所有已定义的接口模块"""
    modules = []
    api_dir = './output/apis'
    
    if os.path.exists(api_dir):
        for filename in os.listdir(api_dir):
            if filename.endswith('_api.py') and not filename.startswith('__init__'):
                module_name = filename.replace('_api.py', '')
                modules.append(module_name)
    
    return modules


def generate_exec_scripts():
    """生成测试执行脚本到用户项目目录"""
    scripts_dir = os.path.dirname(__file__)
    
    # 生成 run_tests.py
    run_tests_src = os.path.join(scripts_dir, 'run_tests.py')
    if os.path.exists(run_tests_src):
        with open(run_tests_src, 'r', encoding='utf-8') as f:
            run_tests_content = f.read()
        
        # 修改导入路径
        run_tests_content = run_tests_content.replace(
            'from report_generator import ReportGenerator',
            'from output.scripts.report_generator import ReportGenerator'
        )
        
        os.makedirs('./output', exist_ok=True)
        with open('./output/run_tests.py', 'w', encoding='utf-8') as f:
            f.write(run_tests_content)
    
    # 生成 report_generator.py
    report_gen_src = os.path.join(scripts_dir, 'report_generator.py')
    if os.path.exists(report_gen_src):
        with open(report_gen_src, 'r', encoding='utf-8') as f:
            report_gen_content = f.read()
        
        os.makedirs('./output/scripts', exist_ok=True)
        with open('./output/scripts/report_generator.py', 'w', encoding='utf-8') as f:
            f.write(report_gen_content)
    
    # 生成测试运行器 wrapper
    runner_content = '''#!/usr/bin/env python3
"""API测试执行器 - 运行生成的测试用例"""

import subprocess
import sys
import os

def run_all_tests():
    """运行所有测试用例"""
    print("开始执行API测试...")
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', 'output/tests/', '-v'],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print("错误输出:", result.stderr)
    return result.returncode

def run_module_tests(module_name):
    """运行指定模块的测试"""
    print(f"开始执行模块 [{module_name}] 的测试...")
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', f'output/tests/test_{module_name}.py', '-v'],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print("错误输出:", result.stderr)
    return result.returncode

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='API测试执行器')
    parser.add_argument('--all', action='store_true', help='运行所有测试')
    parser.add_argument('--module', help='运行指定模块的测试')
    args = parser.parse_args()
    
    if args.all:
        exit(run_all_tests())
    elif args.module:
        exit(run_module_tests(args.module))
    else:
        print("请使用 --all 或 --module 参数")
        exit(1)
'''
    
    with open('./output/run_api_tests.py', 'w', encoding='utf-8') as f:
        f.write(runner_content)
    
    return {
        'status': 'success',
        'message': '测试执行脚本生成完成！',
        'files': ['./output/run_tests.py', './output/scripts/report_generator.py', './output/run_api_tests.py']
    }


def list_test_files():
    """列出所有测试文件"""
    tests = []
    test_dir = './output/tests'
    
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
        '../references/templates/config.yaml'
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
    os.makedirs('./output/apis', exist_ok=True)
    os.makedirs('./output/tests', exist_ok=True)
    os.makedirs('./output/reports', exist_ok=True)
    
    # 创建 output/apis/__init__.py
    with open('./output/apis/__init__.py', 'w', encoding='utf-8') as f:
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
        'directories': ['./output/apis', './output/tests', './output/reports']
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
    
    # 生成执行脚本
    gen_exec_parser = subparsers.add_parser('gen-exec', help='生成测试执行脚本（用户可自行执行）')
    
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
    
    elif args.command == 'gen-exec':
        result = generate_exec_scripts()
        print(json.dumps(result))
    
    elif args.command == 'list':
        if args.type == 'api':
            modules = list_api_modules()
        else:
            modules = list_test_files()
        print(json.dumps({'status': 'success', 'items': modules}))


if __name__ == '__main__':
    main()
