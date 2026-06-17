import sys
import os

skill_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if skill_path not in sys.path:
    sys.path.insert(0, skill_path)

from references.core.http_client import HttpClient


class OrderApi:
    BASE_PATH = "/api/orders"

    @classmethod
    def get_orders(cls, client: HttpClient, params=None):
        return client.get(f"{cls.BASE_PATH}", params=params)

    @classmethod
    def get_order_by_id(cls, client: HttpClient, order_id):
        return client.get(f"{cls.BASE_PATH}/{order_id}")

    @classmethod
    def post_order(cls, client: HttpClient, data):
        return client.post(f"{cls.BASE_PATH}", json=data)
