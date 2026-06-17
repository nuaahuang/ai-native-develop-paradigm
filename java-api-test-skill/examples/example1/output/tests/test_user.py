import sys
import os

skill_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if skill_path not in sys.path:
    sys.path.insert(0, skill_path)

from references.core.base_test import BaseTest
from apis.user_api import UserApi


class TestUserApi(BaseTest):

    _stored__user__email = None
    _stored__user__id = None
    _stored__user__username = None
    _stored__user_by_id__email = None
    _stored__user_by_id__id = None
    _stored__user_by_id__username = None
    _stored__users__data = None
    _stored__users__total = None

    def test_get_users(self):
        """测试获取用户列表"""
        response = UserApi.get_users(self.client)
        self.assert_status_ok(response)
        data = self.assert_response_json(response, ['data', 'total'])
        self.__class__._stored__users__data = data.get("data")
        self.__class__._stored__users__total = data.get("total")

    def test_create_user(self):
        """测试创建用户"""
        # 根据接口数据类型自动生成
        payload = {
        "username": "test_username",
        "email": "test@example.com",
        "password": "Password123!"
}
        response = UserApi.post_user(self.client, payload)
        self.assert_status_created(response)
        data = self.assert_response_json(response, ['id', 'username', 'email'])
        self.__class__._stored__user__email = data.get("email")
        self.__class__._stored__user__id = data.get("id")
        self.__class__._stored__user__username = data.get("username")

    def test_get_user_by_id(self):
        """测试获取单个用户 - 数据源: user"""
        if not self.__class__._stored__user__id:
            self.skipTest("请先执行前置测试: user")

        response = UserApi.get_user_by_id(self.client, self.__class__._stored__user__id)
        self.assert_status_ok(response)
        data = self.assert_response_json(response, ['id', 'username', 'email'])
        self.__class__._stored__user_by_id__email = data.get("email")
        self.__class__._stored__user_by_id__id = data.get("id")
        self.__class__._stored__user_by_id__username = data.get("username")

