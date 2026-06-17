import os
import re
import json
import yaml
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional


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
