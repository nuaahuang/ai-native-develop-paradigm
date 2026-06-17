import os
import re
import json
import yaml
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional


def _sanitize_scan_path(scan_path: str) -> str:
    """安全检查扫描路径，严格限制扫描范围
    
    Security rules:
    1. 必须在当前工作目录范围内
    2. 只能扫描允许的子目录：src/, src/main/, swagger/, api/, controller/, controllers/
    3. 禁止扫描敏感目录和文件
    4. 路径规范化，防止..绕过
    
    Args:
        scan_path: 用户提供的扫描路径
        
    Returns:
        规范化后的绝对路径
        
    Raises:
        ValueError: 如果路径超出限制或包含敏感模式
    """
    cwd = os.path.abspath(os.getcwd())
    abs_path = os.path.abspath(os.path.expanduser(scan_path))
    
    # 检查是否在当前工作目录内（防止 .. 绕过）
    if not abs_path.startswith(cwd):
        raise ValueError(
            f"[SECURITY] 扫描路径 '{abs_path}' 超出当前工作目录 '{cwd}'\n"
            "安全限制：只能扫描当前工作目录范围内的文件"
        )
    
    # 白名单：允许扫描的目录后缀
    ALLOWED_DIR_SUFFIXES = [
        '/src', '/src/', '/src/main', '/src/main/',
        '/swagger', '/swagger/',
        '/api', '/api/',
        '/controller', '/controllers',
        '/controller/', '/controllers/',
    ]
    
    # 检查路径是否在允许的白名单目录内
    allowed = False
    for suffix in ALLOWED_DIR_SUFFIXES:
        if abs_path.endswith(suffix) or suffix in abs_path:
            allowed = True
            break
    
    # 允许直接在当前工作目录扫描（有些项目结构可能不同）
    # 但单个文件仍然需要检查扩展名
    if abs_path == cwd:
        allowed = True
    
    # 允许具体的单个文件（仅允许指定扩展名）
    if os.path.isfile(abs_path):
        # 允许.java/.json/.yml/.yaml 文件
        ext = os.path.splitext(abs_path)[1].lower()
        if ext in ['.java', '.json', '.yml', '.yaml', '.swagger']:
            allowed = True
        else:
            # 如果已经被目录白名单放过了（比如在src下的非java文件），保持allowed
            if not allowed:
                allowed = False
    
    if not allowed:
        raise ValueError(
            f"[SECURITY] 扫描路径 '{abs_path}' 不在允许的白名单目录内\n"
            f"允许的目录：{ALLOWED_DIR_SUFFIXES}\n"
            "允许的文件：.java, .json, .yml, .yaml\n"
            "安全提示：本工具仅用于扫描项目源码和API文档，请将扫描路径限制在src/或swagger/目录下"
        )
    
    # 禁止扫描敏感目录
    forbidden_patterns = [
        '/etc/', '/root/', '/home/', '/var/', '/usr/', '/tmp/',
        '.ssh', '.git', '.config', '.aws', '.docker', '.npm',
        'id_rsa', 'id_dsa', 'authorized_keys',
        'password', 'secret', 'token', 'key', '.env',
    ]
    for pattern in forbidden_patterns:
        if pattern in abs_path.lower():
            raise ValueError(
                f"[SECURITY] 扫描路径 '{abs_path}' 包含敏感目录/文件名 '{pattern}'，禁止扫描"
            )
    
    return abs_path


class ApiScanner:
    """接口扫描器，支持多种扫描方式和变更检测"""
    
    _SNAPSHOT_DIR = '.api_snapshots'
    
    @staticmethod
    def _get_api_key(api: Dict) -> str:
        """生成接口唯一标识key"""
        return f"{api.get('method', '')}_{api.get('endpoint', '')}"
    
    @staticmethod
    def _get_api_hash(api: Dict) -> str:
        """生成接口内容哈希值（用于检测修改）"""
        content = json.dumps(api, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    @staticmethod
    def save_snapshot(apis: List[Dict], snapshot_name: str = None):
        """保存接口快照"""
        os.makedirs(ApiScanner._SNAPSHOT_DIR, exist_ok=True)
        
        if not snapshot_name:
            snapshot_name = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'apis': apis,
            'api_keys': {ApiScanner._get_api_key(api): ApiScanner._get_api_hash(api) for api in apis}
        }
        
        snapshot_path = os.path.join(ApiScanner._SNAPSHOT_DIR, f'{snapshot_name}.json')
        with open(snapshot_path, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
        
        return snapshot_path
    
    @staticmethod
    def load_snapshot(snapshot_name: str = None) -> Optional[Dict]:
        """加载接口快照"""
        if not snapshot_name:
            snapshots = []
            if os.path.exists(ApiScanner._SNAPSHOT_DIR):
                for filename in os.listdir(ApiScanner._SNAPSHOT_DIR):
                    if filename.endswith('.json'):
                        snapshots.append(filename)
            
            if not snapshots:
                return None
            
            snapshots.sort()
            snapshot_name = snapshots[-1].replace('.json', '')
        
        snapshot_path = os.path.join(ApiScanner._SNAPSHOT_DIR, f'{snapshot_name}.json')
        if os.path.exists(snapshot_path):
            with open(snapshot_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return None
    
    @staticmethod
    def compare_snapshots(current_apis: List[Dict], previous_snapshot: Dict = None) -> Dict:
        """对比接口变化
        
        Returns:
            {
                'added': 新增的接口列表,
                'removed': 删除的接口列表,
                'modified': 修改的接口列表,
                'unchanged': 未变化的接口列表,
                'summary': 变更摘要
            }
        """
        if not previous_snapshot:
            previous_snapshot = ApiScanner.load_snapshot()
        
        if not previous_snapshot:
            return {
                'added': current_apis,
                'removed': [],
                'modified': [],
                'unchanged': [],
                'summary': {
                    'total_current': len(current_apis),
                    'total_previous': 0,
                    'added': len(current_apis),
                    'removed': 0,
                    'modified': 0,
                    'unchanged': 0
                }
            }
        
        previous_keys = previous_snapshot.get('api_keys', {})
        previous_apis = {ApiScanner._get_api_key(api): api for api in previous_snapshot.get('apis', [])}
        
        current_keys = {ApiScanner._get_api_key(api): ApiScanner._get_api_hash(api) for api in current_apis}
        current_apis_map = {ApiScanner._get_api_key(api): api for api in current_apis}
        
        added = []
        removed = []
        modified = []
        unchanged = []
        
        for key, current_hash in current_keys.items():
            if key not in previous_keys:
                added.append(current_apis_map[key])
            else:
                if current_hash != previous_keys[key]:
                    modified.append({
                        'current': current_apis_map[key],
                        'previous': previous_apis.get(key)
                    })
                else:
                    unchanged.append(current_apis_map[key])
        
        for key in previous_keys:
            if key not in current_keys:
                removed.append(previous_apis.get(key))
        
        return {
            'added': added,
            'removed': removed,
            'modified': modified,
            'unchanged': unchanged,
            'summary': {
                'total_current': len(current_apis),
                'total_previous': len(previous_apis),
                'added': len(added),
                'removed': len(removed),
                'modified': len(modified),
                'unchanged': len(unchanged)
            }
        }
    
    @staticmethod
    def scan_java_source(source_path: str) -> List[Dict]:
        """扫描Java源码中的接口定义
        
        Args:
            source_path: Java源码目录或文件路径
        
        Returns:
            接口定义列表
        """
        # 安全检查：限制只能在当前工作目录内扫描
        source_path = _sanitize_scan_path(source_path)
        
        apis = []
        
        if os.path.isfile(source_path):
            files = [source_path]
        else:
            files = []
            for root, dirs, filenames in os.walk(source_path):
                for filename in filenames:
                    if filename.endswith('.java'):
                        files.append(os.path.join(root, filename))
        
        for file_path in files:
            file_apis = ApiScanner._parse_java_file(file_path)
            apis.extend(file_apis)
        
        return apis
    
    @staticmethod
    def _parse_java_file(file_path: str) -> List[Dict]:
        """解析单个Java文件"""
        apis = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return apis
        
        class_name = ApiScanner._extract_class_name(content)
        base_path = ApiScanner._extract_base_path(content)
        
        method_pattern = r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|RequestMapping)\s*\(\s*["\']([^"\']+)["\']\s*\)'
        matches = re.finditer(method_pattern, content)
        
        for match in matches:
            annotation = match.group(1)
            path = match.group(2)
            
            http_method = ApiScanner._get_http_method(annotation, content, match)
            full_path = f"{base_path}{path}" if base_path else path
            
            api_info = {
                'module': class_name.lower().replace('controller', '') if class_name else 'unknown',
                'method': http_method,
                'endpoint': full_path,
                'controller': class_name,
                'file': os.path.basename(file_path)
            }
            apis.append(api_info)
        
        return apis
    
    @staticmethod
    def _extract_class_name(content: str) -> str:
        match = re.search(r'class\s+(\w+)\s*Controller', content)
        if match:
            return match.group(1)
        match = re.search(r'class\s+(\w+)', content)
        return match.group(1) if match else ''
    
    @staticmethod
    def _extract_base_path(content: str) -> str:
        match = re.search(r'@RequestMapping\s*\(\s*["\']([^"\']+)["\']\s*\)', content)
        return match.group(1) if match else ''
    
    @staticmethod
    def _get_http_method(annotation: str, content: str, match) -> str:
        if annotation == 'GetMapping':
            return 'GET'
        elif annotation == 'PostMapping':
            return 'POST'
        elif annotation == 'PutMapping':
            return 'PUT'
        elif annotation == 'DeleteMapping':
            return 'DELETE'
        elif annotation == 'RequestMapping':
            line_start = content[:match.start()].rfind('\n')
            line_end = content[match.end():].find('\n')
            if line_end == -1:
                line_end = len(content)
            line = content[line_start:match.end() + line_end]
            
            method_match = re.search(r'method\s*=\s*RequestMethod\.(\w+)', line)
            if method_match:
                return method_match.group(1)
            
            return 'GET'
        
        return 'GET'
    
    @staticmethod
    def scan_swagger(swagger_path: str) -> List[Dict]:
        """扫描Swagger/OpenAPI文档
        
        Args:
            swagger_path: Swagger JSON/YAML文件路径或URL
        
        Returns:
            接口定义列表
        """
        apis = []
        
        if not (swagger_path.startswith('http://') or swagger_path.startswith('https://')):
            # 本地文件需要安全检查
            swagger_path = _sanitize_scan_path(swagger_path)
        
        if swagger_path.startswith('http://') or swagger_path.startswith('https://'):
            try:
                import requests
                response = requests.get(swagger_path)
                response.raise_for_status()
                try:
                    spec = response.json()
                except:
                    spec = yaml.safe_load(response.text)
            except Exception:
                return apis
        else:
            try:
                with open(swagger_path, 'r', encoding='utf-8') as f:
                    try:
                        spec = json.load(f)
                    except:
                        f.seek(0)
                        spec = yaml.safe_load(f)
            except Exception:
                return apis
        
        apis = ApiScanner._parse_swagger_spec(spec)
        return apis
    
    @staticmethod
    def _parse_swagger_spec(spec: Dict) -> List[Dict]:
        """解析Swagger/OpenAPI规范"""
        apis = []
        
        if 'swagger' in spec:
            apis.extend(ApiScanner._parse_swagger_v2(spec))
        elif 'openapi' in spec:
            apis.extend(ApiScanner._parse_openapi_v3(spec))
        
        return apis
    
    @staticmethod
    def _parse_swagger_v2(spec: Dict) -> List[Dict]:
        """解析Swagger V2规范"""
        apis = []
        base_path = spec.get('basePath', '')
        definitions = spec.get('definitions', {})
        
        for path, path_item in spec.get('paths', {}).items():
            full_path = f"{base_path}{path}"
            
            for http_method, operation in path_item.items():
                if http_method.lower() not in ['get', 'post', 'put', 'delete', 'patch']:
                    continue
                
                tags = operation.get('tags', [])
                module = tags[0] if tags else 'unknown'
                
                # 提取请求参数（字段类型定义）
                fields = []
                parameters = operation.get('parameters', [])
                for param in parameters:
                    if param.get('in') == 'body':
                        schema = param.get('schema', {})
                        fields = ApiScanner._extract_fields_from_schema(schema, definitions)
                    elif param.get('in') in ['query', 'path']:
                        fields.append(ApiScanner._param_to_field(param))
                
                # 提取响应字段
                responses = operation.get('responses', {})
                response_keys = ApiScanner._extract_response_keys(responses, definitions)
                
                api_info = {
                    'module': module.lower(),
                    'method': http_method.upper(),
                    'endpoint': full_path,
                    'description': operation.get('summary', '') or operation.get('description', ''),
                    'tags': tags,
                    'fields': fields,
                    'response_fields': response_keys
                }
                apis.append(api_info)
        
        return apis
    
    @staticmethod
    def _extract_fields_from_schema(schema: Dict, definitions: Dict) -> List[Dict]:
        """从schema定义中提取字段列表"""
        fields = []
        
        # 处理 $ref 引用
        ref = schema.get('$ref', '')
        if ref:
            ref_name = ref.split('/')[-1]
            schema = definitions.get(ref_name, {})
        
        properties = schema.get('properties', {})
        required_list = schema.get('required', [])
        
        for field_name, field_schema in properties.items():
            field_type = field_schema.get('type', 'string')
            field_format = field_schema.get('format', '')
            
            # 处理嵌套 $ref
            if '$ref' in field_schema:
                field_type = 'object'
            
            field = {
                'name': field_name,
                'type': field_type,
                'format': field_format,
                'required': field_name in required_list,
                'description': field_schema.get('description', '')
            }
            fields.append(field)
        
        return fields
    
    @staticmethod
    def _param_to_field(param: Dict) -> Dict:
        """将Swagger参数转换为字段定义"""
        return {
            'name': param.get('name', ''),
            'type': param.get('type', 'string'),
            'format': param.get('format', ''),
            'required': param.get('required', False),
            'description': param.get('description', ''),
            'in': param.get('in', '')
        }
    
    @staticmethod
    def _extract_response_keys(responses: Dict, definitions: Dict) -> List[str]:
        """从响应定义中提取关键字段"""
        keys = []
        for status_code, response in responses.items():
            if not status_code.startswith('2'):
                continue
            
            schema = response.get('schema', {})
            if '$ref' in schema:
                ref_name = schema['$ref'].split('/')[-1]
                schema = definitions.get(ref_name, {})
            
            properties = schema.get('properties', {})
            keys.extend(list(properties.keys()))
        
        # 去重但保持顺序
        seen = set()
        return [k for k in keys if not (k in seen or seen.add(k))]
    
    @staticmethod
    def _parse_openapi_v3(spec: Dict) -> List[Dict]:
        """解析OpenAPI V3规范"""
        apis = []
        servers = spec.get('servers', [])
        base_path = servers[0].get('url', '') if servers else ''
        schemas = spec.get('components', {}).get('schemas', {})
        
        for path, path_item in spec.get('paths', {}).items():
            full_path = f"{base_path}{path}"
            
            for http_method, operation in path_item.items():
                if http_method.lower() not in ['get', 'post', 'put', 'delete', 'patch']:
                    continue
                
                tags = operation.get('tags', [])
                module = tags[0] if tags else 'unknown'
                
                # 提取请求字段
                fields = []
                request_body = operation.get('requestBody', {})
                content = request_body.get('content', {})
                json_content = content.get('application/json', {})
                schema = json_content.get('schema', {})
                if schema:
                    fields = ApiScanner._extract_fields_from_schema(schema, schemas)
                
                # 也提取 query/path 参数
                parameters = operation.get('parameters', [])
                for param in parameters:
                    if param.get('in') in ['query', 'path']:
                        fields.append(ApiScanner._param_to_field(param))
                
                # 提取响应字段
                responses = operation.get('responses', {})
                response_keys = ApiScanner._extract_openapi_response_keys(responses, schemas)
                
                api_info = {
                    'module': module.lower(),
                    'method': http_method.upper(),
                    'endpoint': full_path,
                    'description': operation.get('summary', '') or operation.get('description', ''),
                    'tags': tags,
                    'fields': fields,
                    'response_fields': response_keys
                }
                apis.append(api_info)
        
        return apis
    
    @staticmethod
    def _extract_openapi_response_keys(responses: Dict, schemas: Dict) -> List[str]:
        """从OpenAPI V3响应中提取关键字段"""
        keys = []
        for status_code, response in responses.items():
            if not status_code.startswith('2'):
                continue
            
            content = response.get('content', {})
            json_content = content.get('application/json', {})
            schema = json_content.get('schema', {})
            
            if '$ref' in schema:
                ref_name = schema['$ref'].split('/')[-1]
                schema = schemas.get(ref_name, {})
            
            properties = schema.get('properties', {})
            keys.extend(list(properties.keys()))
        
        seen = set()
        return [k for k in keys if not (k in seen or seen.add(k))]
    
    @staticmethod
    def scan_multiple_sources(sources: List[Dict]) -> List[Dict]:
        """扫描多个来源
        
        Args:
            sources: 来源配置列表，每个元素包含type和path
            
        Returns:
            合并后的接口定义列表
        """
        all_apis = []
        
        for source in sources:
            source_type = source.get('type')
            source_path = source.get('path')
            
            if source_type == 'java_source':
                apis = ApiScanner.scan_java_source(source_path)
            elif source_type == 'swagger':
                apis = ApiScanner.scan_swagger(source_path)
            else:
                continue
            
            all_apis.extend(apis)
        
        return all_apis
    
    @staticmethod
    def group_by_module(apis: List[Dict]) -> Dict[str, List[Dict]]:
        """按模块分组接口"""
        grouped = {}
        
        for api in apis:
            module = api.get('module', 'unknown')
            if module not in grouped:
                grouped[module] = []
            grouped[module].append(api)
        
        return grouped


# 示例用法
if __name__ == '__main__':
    # 扫描Java源码
    java_apis = ApiScanner.scan_java_source('/path/to/java/source')
    print(f"从Java源码扫描到 {len(java_apis)} 个接口")
    
    # 扫描Swagger文档
    swagger_apis = ApiScanner.scan_swagger('/path/to/swagger.json')
    print(f"从Swagger文档扫描到 {len(swagger_apis)} 个接口")
    
    # 按模块分组
    grouped = ApiScanner.group_by_module(java_apis + swagger_apis)
    for module, apis in grouped.items():
        print(f"\n模块 {module}: {len(apis)} 个接口")
        for api in apis:
            print(f"  {api['method']} {api['endpoint']}")
