import sys
import os

skill_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if skill_path not in sys.path:
    sys.path.insert(0, skill_path)

from references.core.base_test import BaseTest
from apis.order_api import OrderApi


class TestOrderApi(BaseTest):

    _stored__order__id = None
    _stored__order__status = None
    _stored__order__total_amount = None
    _stored__order_by_id__id = None
    _stored__order_by_id__items = None
    _stored__order_by_id__status = None
    _stored__order_by_id__total_amount = None
    _stored__orders__data = None
    _stored__orders__total = None

    def test_get_orders(self):
        """测试获取订单列表"""
        response = OrderApi.get_orders(self.client)
        self.assert_status_ok(response)
        data = self.assert_response_json(response, ['data', 'total'])
        self.__class__._stored__orders__data = data.get("data")
        self.__class__._stored__orders__total = data.get("total")

    def test_create_order(self):
        """测试创建订单"""
        # 根据接口数据类型自动生成
        payload = {
        "user_id": 5826,
        "product_id": 801,
        "quantity": 499
}
        response = OrderApi.post_order(self.client, payload)
        self.assert_status_created(response)
        data = self.assert_response_json(response, ['id', 'status', 'total_amount'])
        self.__class__._stored__order__id = data.get("id")
        self.__class__._stored__order__status = data.get("status")
        self.__class__._stored__order__total_amount = data.get("total_amount")

    def test_get_order_by_id(self):
        """测试获取单个订单 - 数据源: order"""
        if not self.__class__._stored__order__id:
            self.skipTest("请先执行前置测试: order")

        response = OrderApi.get_order_by_id(self.client, self.__class__._stored__order__id)
        self.assert_status_ok(response)
        data = self.assert_response_json(response, ['id', 'status', 'items', 'total_amount'])
        self.__class__._stored__order_by_id__id = data.get("id")
        self.__class__._stored__order_by_id__items = data.get("items")
        self.__class__._stored__order_by_id__status = data.get("status")
        self.__class__._stored__order_by_id__total_amount = data.get("total_amount")

