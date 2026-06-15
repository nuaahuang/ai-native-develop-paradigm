import argparse
import os
import json
from typing import List, Dict, Any


class WorkItem:
    def __init__(self, name: str, hours: float = 0.5, description: str = ""):
        self.name = name
        self.hours = hours
        self.description = description


class RequirementItem:
    def __init__(self, name: str, description: str, func_type: str = "新增"):
        self.name = name
        self.description = description
        self.func_type = func_type
        self.work_items: List[WorkItem] = []
        self.notes = ""
        self.explanation = ""
        self.clarifications: List[str] = []

    @classmethod
    def from_dict(cls, data: Dict):
        req = cls(data["name"], data.get("description", ""), data.get("func_type", "新增"))
        req.notes = data.get("notes", "")
        req.explanation = data.get("explanation", "")
        req.clarifications = data.get("clarifications", [])
        for work_item_data in data.get("work_items", []):
            req.work_items.append(WorkItem(
                work_item_data["name"],
                work_item_data.get("hours", 0.5),
                work_item_data.get("description", "")
            ))
        return req


class CSVGenerator:
    @staticmethod
    def generate_work_plan(requirements: List[RequirementItem]) -> str:
        lines = ["需求项,工作项,预计后端工时（小时）,说明"]
        total_hours = 0.0
        
        for req_item in requirements:
            for work_item in req_item.work_items:
                name = req_item.name.replace('"', '""')
                work_name = work_item.name.replace('"', '""')
                desc = work_item.description.replace('"', '""')
                if req_item.explanation:
                    full_desc = f"{desc}【说明】{req_item.explanation}" if desc else f"【说明】{req_item.explanation}"
                    full_desc = full_desc.replace('"', '""')
                else:
                    full_desc = desc
                lines.append(f'"{name}","{work_name}",{work_item.hours},"{full_desc}"')
                total_hours += work_item.hours
        
        lines.append(f'"总计","-",{total_hours},"-"')
        return '\n'.join(lines)


def load_json_from_file(file_path: str) -> Dict:
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_json_from_string(json_str: str) -> Dict:
    return json.loads(json_str)


def main():
    parser = argparse.ArgumentParser(description='需求拆分结果处理工具 - 生成工作计划预估表（CSV格式）')
    parser.add_argument('--input', required=True, help='大模型输出的JSON文件路径或JSON字符串')
    parser.add_argument('--output', default='./output', help='输出目录路径')
    parser.add_argument('--is-string', action='store_true', help='输入是否为JSON字符串（默认是文件路径）')
    
    args = parser.parse_args()
    
    try:
        if args.is_string:
            data = load_json_from_string(args.input)
        else:
            if not os.path.exists(args.input):
                print(f'错误：输入文件不存在：{args.input}')
                return
            data = load_json_from_file(args.input)
    except json.JSONDecodeError as e:
        print(f'错误：JSON格式解析失败：{str(e)}')
        return
    
    requirements = []
    for req_data in data.get("requirements", []):
        req_item = RequirementItem.from_dict(req_data)
        requirements.append(req_item)
    
    os.makedirs(args.output, exist_ok=True)
    
    work_plan_csv = CSVGenerator.generate_work_plan(requirements)
    work_plan_path = os.path.join(args.output, 'work-plan.csv')
    
    with open(work_plan_path, 'w', encoding='utf-8-sig') as f:
        f.write(work_plan_csv)
    
    print(f'工作计划预估表已生成：{work_plan_path}')


if __name__ == '__main__':
    main()
