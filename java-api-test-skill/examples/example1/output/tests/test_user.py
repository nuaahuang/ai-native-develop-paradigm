import sys
import os

# 计算skill路径：从 test_user.py -> output/tests -> output -> example1 -> examples -> java-api-test-skill
skill_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if skill_path not in sys.path:
    sys.path.insert(0, skill_path)

from references.core.base_test import BaseTest
from apis.user_api import UserApi


class TestUserApi(BaseTest):
    created_user_id = None

    def test_get_users(self):
        """测试获取用户列表"""
        response = UserApi.get_users(self.client)
        self.assert_status_ok(response)
        self.assert_response_json(response, ['data', 'total'])

    def test_create_user(self):
        """测试创建用户"""
        payload = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }
        response = UserApi.post_user(self.client, payload)
        self.assert_status_created(response)
        data = self.assert_response_json(response, ['id', 'username'])
        self.__class__.created_user_id = data.get('id')

    def test_get_user_by_id(self):
        """测试获取单个用户"""
        if self.created_user_id:
            response = UserApi.get_user_by_id(self.client, self.created_user_id)
        else:
            response = UserApi.get_user_by_id(self.client, 1)
        self.assert_status_ok(response)
        self.assert_response_json(response, ['id', 'username'])