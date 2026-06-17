import sys
import os

# 计算skill路径：从 user_api.py -> apis -> example1 -> examples -> java-api-test-skill
skill_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if skill_path not in sys.path:
    sys.path.insert(0, skill_path)

from references.core.http_client import HttpClient


class UserApi:
    BASE_PATH = "/api/users"

    @classmethod
    def get_users(cls, client: HttpClient, params=None):
        return client.get(f"{cls.BASE_PATH}", params=params)

    @classmethod
    def get_user_by_id(cls, client: HttpClient, user_id, params=None):
        return client.get(f"{cls.BASE_PATH}/{user_id}", params=params)

    @classmethod
    def post_user(cls, client: HttpClient, data):
        return client.post(f"{cls.BASE_PATH}", json=data)

    @classmethod
    def put_user_by_id(cls, client: HttpClient, user_id, data):
        return client.put(f"{cls.BASE_PATH}/{user_id}", json=data)

    @classmethod
    def delete_user_by_id(cls, client: HttpClient, user_id):
        return client.delete(f"{cls.BASE_PATH}/{user_id}")