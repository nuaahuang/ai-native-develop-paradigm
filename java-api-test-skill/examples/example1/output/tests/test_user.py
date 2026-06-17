import sys
import os

skill_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if skill_path not in sys.path:
    sys.path.insert(0, skill_path)

from references.core.base_test import BaseTest
from apis.user_api import UserApi


class TestUserApi(BaseTest):

    _created_resource_id = None

    def test_get_users(self):
        """测试获取用户列表"""
        response = UserApi.get_users(self.client)
        self.assert_status_ok(response)
        data = self.assert_response_json(response, ['data', 'total'])

    def test_create_user(self):
        """测试创建用户"""
        # 根据接口数据类型自动生成
        payload = {
        "username": "test_username",
        "email": "test@example.com",
        "password": "Password123!",
        "age": 5433
}
        response = UserApi.post_user(self.client, payload)
        self.assert_status_created(response)
        data = self.assert_response_json(response, ['id', 'username'])
        self.__class__._created_resource_id = data.get("id")

    def test_get_user_by_id(self):
        """测试获取单个用户 - 前置: user"""
        if not self.__class__._created_resource_id:
            self.skipTest("请先执行前置测试: user")

        response = UserApi.get_user_by_id(self.client, self.__class__._created_resource_id)
        self.assert_status_ok(response)
        data = self.assert_response_json(response, ['id', 'username'])

