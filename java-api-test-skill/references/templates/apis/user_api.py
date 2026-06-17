from core.http_client import HttpClient


class UserApi:
    BASE_PATH = "/api/users"

    @classmethod
    def get_users(cls, client: HttpClient, params=None):
        return client.get(f"{cls.BASE_PATH}", params=params)

    @classmethod
    def get_user_by_id(cls, client: HttpClient, user_id):
        return client.get(f"{cls.BASE_PATH}/{user_id}")

    @classmethod
    def create_user(cls, client: HttpClient, data):
        return client.post(f"{cls.BASE_PATH}", json=data)

    @classmethod
    def update_user(cls, client: HttpClient, user_id, data):
        return client.put(f"{cls.BASE_PATH}/{user_id}", json=data)

    @classmethod
    def delete_user(cls, client: HttpClient, user_id):
        return client.delete(f"{cls.BASE_PATH}/{user_id}")
