import requests
import os
import json
import urllib.parse
from typing import Optional, Dict, Any

# 允许的网络范围（根据企业安全策略调整）
# 允许: localhost/127.0.0.1、内网IP、常见企业域名后缀
# 可以通过环境变量 API_ALLOWED_DOMAINS 配置额外允许的域名（逗号分隔）
DEFAULT_ALLOWED_DOMAINS = {
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


def _get_allowed_domains() -> set:
    """获取允许的域名集合，合并默认值和环境变量配置"""
    allowed = set(DEFAULT_ALLOWED_DOMAINS)
    env_allowed = os.getenv('API_ALLOWED_DOMAINS', '')
    if env_allowed:
        for domain in env_allowed.split(','):
            domain = domain.strip().lower()
            if domain:
                allowed.add(domain)
    return allowed


class HttpClient:
    def __init__(self, base_url: str, headers: Optional[Dict] = None, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self._validate_base_url(base_url)
        self._setup_default_headers(headers or {})
    
    def _validate_base_url(self, base_url: str):
        """验证base_url是否在允许范围内
        
        Security rules:
        1. 禁止包含敏感模式（metadata, aws, alibaba 等）
        2. 非本地服务必须使用HTTPS
        3. 用户可通过 API_ALLOWED_DOMAINS 环境变量添加允许域名
        """
        parsed = urllib.parse.urlparse(base_url)
        host = parsed.netloc.split(':')[0].lower()
        
        # 检查是否包含禁止模式
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in host:
                raise ValueError(
                    f"[SECURITY] 目标域名 '{host}' 包含禁止模式 '{pattern}'，不允许访问\n"
                    "如需放行特定域名，请设置环境变量 API_ALLOWED_DOMAINS=domain1,domain2"
                )
        
        # 禁止HTTP明文（非本地）
        if parsed.scheme == 'http' and not host in ['localhost', '127.0.0.1', '0.0.0.0']:
            raise ValueError(
                "[SECURITY] 外部非本地服务必须使用HTTPS协议，禁止HTTP明文传输\n"
                "如需测试本地HTTP服务，请使用 localhost/127.0.0.1"
            )
        
        # 检查是否在允许列表
        # 如果是完整域名匹配（例如 .example.com），允许该域名下所有子域名
        allowed = _get_allowed_domains()
        matched = False
        
        # 精确匹配
        if host in allowed:
            matched = True
        
        # 后缀匹配（允许 example.com → *.example.com）
        if not matched:
            for allowed_domain in allowed:
                if host.endswith('.' + allowed_domain) or allowed_domain in host:
                    matched = True
                    break
        
        if not matched:
            raise ValueError(
                f"[SECURITY] 目标域名 '{host}' 不在允许列表中\n"
                f"当前允许域名: {sorted(_get_allowed_domains())}\n"
                "如需添加允许域名，请设置环境变量 API_ALLOWED_DOMAINS=domain1,domain2\n"
                "安全提示：本工具用于企业内部接口测试，请仅添加可信域名"
            )
    
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
