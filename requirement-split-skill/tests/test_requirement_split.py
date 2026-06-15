import unittest
import os
import json
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from requirement_split import RequirementItem, WorkItem, CSVGenerator


class TestRequirementSplit(unittest.TestCase):
    
    def test_requirement_item_from_dict(self):
        data = {
            "name": "订单创建",
            "description": "用户可以创建新订单",
            "func_type": "新增",
            "work_items": [
                {"name": "表结构设计", "type": "后端", "backend_hours": 1.0, "frontend_hours": 0.0, "description": "设计数据表"}
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
        self.assertEqual(req.work_items[0].type, "后端")
        self.assertEqual(req.work_items[0].backend_hours, 1.0)
        self.assertEqual(req.work_items[0].frontend_hours, 0.0)
        self.assertEqual(req.notes, "注意点")
        self.assertEqual(req.explanation, "说明")
        self.assertEqual(req.clarifications, ["问题1"])

    def test_work_item(self):
        work_item = WorkItem("接口开发", "后端", 1.0, 0.0, "开发接口")
        self.assertEqual(work_item.name, "接口开发")
        self.assertEqual(work_item.type, "后端")
        self.assertEqual(work_item.backend_hours, 1.0)
        self.assertEqual(work_item.frontend_hours, 0.0)
        self.assertEqual(work_item.description, "开发接口")

    def test_generate_work_plan(self):
        req1 = RequirementItem("订单创建", "描述1", "新增")
        req1.work_items.append(WorkItem("表结构设计", "后端", 1.0, 0.0, "设计"))
        req1.work_items.append(WorkItem("接口开发", "后端", 0.5, 0.0, "开发"))
        
        csv = CSVGenerator.generate_work_plan([req1])
        
        self.assertIn("订单创建", csv)
        self.assertIn("表结构设计", csv)
        self.assertIn("1.0", csv)
        self.assertIn("总计", csv)

    def test_generate_work_plan_with_frontend(self):
        req1 = RequirementItem("订单创建", "描述1", "新增")
        req1.work_items.append(WorkItem("订单表单页面", "前端", 0.0, 3.0, "前端页面"))
        req1.work_items.append(WorkItem("创建订单接口", "后端", 1.0, 0.0, "后端接口"))
        
        csv = CSVGenerator.generate_work_plan([req1])
        
        self.assertIn("前端", csv)
        self.assertIn("后端", csv)
        self.assertIn("3.0", csv)
        self.assertIn("1.0", csv)


if __name__ == '__main__':
    unittest.main()