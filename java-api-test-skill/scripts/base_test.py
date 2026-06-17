import pytest
import os
import json
from .http_client import HttpClient


class BaseTest:
    BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8080')
    
    @pytest.fixture(autouse=True)
    def setup(self):
        headers = self._load_headers_from_env()
        self.client = HttpClient(self.BASE_URL, headers=headers)
        yield
        self.client.session.close()
    
    def _load_headers_from_env(self) -> dict:
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
    
    def assert_status_ok(self, response):
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def assert_status_created(self, response):
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"
    
    def assert_status_no_content(self, response):
        assert response.status_code == 204, f"Expected 204, got {response.status_code}"
    
    def assert_status_bad_request(self, response):
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    def assert_status_unauthorized(self, response):
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def assert_status_forbidden(self, response):
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    
    def assert_status_not_found(self, response):
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def assert_has_key(self, data, key):
        assert key in data, f"Missing key: {key}"
    
    def assert_response_json(self, response, expected_keys=None):
        try:
            data = response.json()
        except ValueError:
            pytest.fail("Response is not valid JSON")
        
        if expected_keys:
            for key in expected_keys:
                self.assert_has_key(data, key)
        
        return data
    
    def assert_response_ok(self, response, expected_keys=None):
        self.assert_status_ok(response)
        return self.assert_response_json(response, expected_keys)
    
    def assert_response_created(self, response, expected_keys=None):
        self.assert_status_created(response)
        return self.assert_response_json(response, expected_keys)
