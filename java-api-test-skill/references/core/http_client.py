import requests
import os
import json
import urllib.parse
from typing import Optional, Dict, Any

# 允许的网络范围（根据企业安全策略调整）
# 允许: localhost/127.0.0.1、内网IP、常见企业域名后缀
ALLOWED_DOMAINS = {
    'localhost', '127.0.0.1', '0.0.0.0',
    'internal', 'local', 'intranet',
}

# 禁止的敏感网络目标
FORBIDDEN_PATTERNS = [
    'metadata', 'aws', 'alibaba', 'tencent', 'cloud',
    '169.254.',  # cloud metadata
    '100.',  # internal cloud networking
    'kubernetes', 'k8s', 'docker', 'container',
]


class HttpClient:
    def __init__(self, base_url: str, headers: Optional[Dict] = None, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self._validate_base_url(base_url)
        self._setup_default_headers(headers or {})
    
    def _validate_base_url(self, base_url: str):
        """验证base_url是否在允许范围内"""
        parsed = urllib.parse.urlparse(base_url)
        host = parsed.netloc.split(':')[0].lower()
        
        # 检查是否包含禁止模式
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in host:
                raise ValueError(f"目标域名 '{host}' 包含禁止模式 '{pattern}'，不允许访问")
        
        # 检查localhost/内网，这是安全的（用户自己的测试环境）
        # 如果需要严格限制，可以在这里添加企业域名白名单检查
        # 本Skill定位是测试工具，允许用户测试自己的内网服务
        
        # 禁止HTTP明文（可选）
        if parsed.scheme == 'http' and not host in ['localhost', '127.0.0.1', '0.0.0.0']:
            # 只允许本地HTTP，外部必须HTTPS
            raise ValueError("外部非本地服务必须使用HTTPS协议，禁止HTTP明文传输")
    
    def _setup_default_headers(self, custom_headers: Dict):
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        env_headers = self._parse_env_headers()
        headers.update(env_headers)
        
        headers.update(custom_headers)
        
        self.session.headers.update(headers)
    
    def _parse_env_headers(self) -> Dict:
        headers = {}
        
        env_headers_str = os.getenv('API_HEADERS')
        if env_headers_str:
            try:
                headers.update(json.loads(env_headers_str))
            except json.JSONDecodeError:
                pass
        
        env_token = os.getenv('API_AUTH_TOKEN')
        if env_token and 'Authorization' not in headers:
            headers['Authorization'] = f'Bearer {env_token}'
        
        return headers
    
    def add_header(self, key: str, value: str):
        self.session.headers[key] = value
    
    def set_headers(self, headers: Dict):
        self.session.headers.update(headers)
    
    def get(self, endpoint: str, params: Optional[Dict] = None, **kwargs) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        return self.session.get(url, params=params, timeout=self.timeout, **kwargs)
    
    def post(self, endpoint: str, json: Optional[Dict] = None, data: Optional[Any] = None, **kwargs) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        return self.session.post(url, json=json, data=data, timeout=self.timeout, **kwargs)
    
    def put(self, endpoint: str, json: Optional[Dict] = None, data: Optional[Any] = None, **kwargs) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        return self.session.put(url, json=json, data=data, timeout=self.timeout, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        return self.session.delete(url, timeout=self.timeout, **kwargs)
    
    def patch(self, endpoint: str, json: Optional[Dict] = None, **kwargs) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        return self.session.patch(url, json=json, timeout=self.timeout, **kwargs)
    
    def request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        return self.session.request(method, url, timeout=self.timeout, **kwargs)
