import requests
import os
import json
from typing import Optional, Dict, Any


class HttpClient:
    def __init__(self, base_url: str, headers: Optional[Dict] = None, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self._setup_default_headers(headers or {})
    
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
