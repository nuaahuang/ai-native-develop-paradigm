import unittest
import os
import json
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from requirement_split import RequirementItem, WorkItem, MarkdownGenerator


class TestRequirementSplit(unittest.TestCase):
    
    def test_requirement_item_from_dict(self):
        data = {
            "name": "订单创建",
            "description": "用户可以创建新订单",
            "func_type": "新增",
            "work_items": [
                {"name": "表结构设计", "hours": 1.0, "description": "设计数据表"}
            ],
            "notes": "注意点",
            "explanation": "说明",
            "clarifications": ["问题1"]
        }
        
        req = RequirementItem.from_dict(data)
        
        self.assertEqual(req.name, "订单创建")
        self.assertEqual(req.description, "用户可以创建新订单")
        self.assertEqual(req.func_type, "新增")
        self.assertEqual(len(req.work_items), 1)
        self.assertEqual(req.work_items[0].name, "表结构设计")
        self.assertEqual(req.work_items[0].hours, 1.0)
        self.assertEqual(req.notes, "注意点")
        self.assertEqual(req.explanation, "说明")
        self.assertEqual(req.clarifications, ["问题1"])

    def test_work_item(self):
        work_item = WorkItem("接口开发", 0.5, "开发接口")
        self.assertEqual(work_item.name, "接口开发")
        self.assertEqual(work_item.hours, 0.5)
        self.assertEqual(work_item.description, "开发接口")

    def test_generate_work_plan(self):
        req1 = RequirementItem("订单创建", "描述1", "新增")
        req1.work_items.append(WorkItem("表结构设计", 1.0, "设计"))
        req1.work_items.append(WorkItem("接口开发", 0.5, "开发"))
        
        md = MarkdownGenerator.generate_work_plan([req1])
        
        self.assertIn("订单创建", md)
        self.assertIn("表结构设计", md)
        self.assertIn("1.0", md)
        self.assertIn("总计", md)

    def test_generate_breakdown(self):
        req1 = RequirementItem("订单查询", "查询订单", "新增")
        req1.notes = "注意分页"
        req1.clarifications = ["是否模糊搜索?"]
        
        md = MarkdownGenerator.generate_breakdown([req1], ["规则1"])
        
        self.assertIn("订单查询", md)
        self.assertIn("注意分页", md)
        self.assertIn("是否模糊搜索?", md)
        self.assertIn("规则1", md)


if __name__ == '__main__':
    unittest.main()