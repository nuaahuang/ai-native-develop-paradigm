import argparse
import os
import json
from typing import List, Dict, Any


class WorkItem:
    def __init__(self, name: str, type: str = "后端", level: str = "page", backend_hours: float = 0.0, frontend_hours: float = 0.0, description: str = "", children: List = None, backend_estimation: Dict = None, frontend_estimation: Dict = None):
        self.name = name
        self.type = type
        self.level = level
        self.backend_hours = backend_hours
        self.frontend_hours = frontend_hours
        self.description = description
        self.children = children if children else []
        self.backend_estimation = backend_estimation
        self.frontend_estimation = frontend_estimation


class RequirementItem:
    def __init__(self, name: str, description: str, func_type: str = "新增"):
        self.name = name
        self.description = description
        self.func_type = func_type
        self.priority = "P2"
        self.dependencies: List[str] = []
        self.risk = ""
        self.milestone = ""
        self.work_items: List[WorkItem] = []
        self.notes = ""
        self.explanation = ""
        self.clarifications: List[str] = []

    @classmethod
    def from_dict(cls, data: Dict):
        req = cls(data["name"], data.get("description", ""), data.get("func_type", "新增"))
        req.priority = data.get("priority", "P2")
        req.dependencies = data.get("dependencies", [])
        req.risk = data.get("risk", "")
        req.milestone = data.get("milestone", "")
        req.notes = data.get("notes", "")
        req.explanation = data.get("explanation", "")
        req.clarifications = data.get("clarifications", [])
        for work_item_data in data.get("work_items", []):
            children = []
            for child_data in work_item_data.get("children", []):
                children.append(WorkItem(
                    child_data["name"],
                    child_data.get("type", "接口开发"),
                    child_data.get("level", "interface"),
                    child_data.get("backend_hours", child_data.get("hours", 0.0)),
                    child_data.get("frontend_hours", 0.0),
                    child_data.get("description", ""),
                    None,
                    child_data.get("backend_estimation"),
                    child_data.get("frontend_estimation")
                ))
            req.work_items.append(WorkItem(
                work_item_data["name"],
                work_item_data.get("type", "后端"),
                work_item_data.get("level", "page"),
                work_item_data.get("backend_hours", work_item_data.get("hours", 0.0)),
                work_item_data.get("frontend_hours", 0.0),
                work_item_data.get("description", ""),
                children,
                work_item_data.get("backend_estimation"),
                work_item_data.get("frontend_estimation")
            ))
        return req


class CSVGenerator:
    @staticmethod
    def generate_work_plan(requirements: List[RequirementItem]) -> str:
        lines = ["需求项,工作项,优先级,预计后端工时（小时）,预计前端工时（小时）,复杂度,估算公式,复用情况,调整原因,说明"]
        total_backend_hours = 0.0
        total_frontend_hours = 0.0
        
        for req_item in requirements:
            for work_item in req_item.work_items:
                if work_item.level != "page":
                    continue
                
                name = req_item.name.replace('"', '""')
                work_name = work_item.name.replace('"', '""')
                priority = req_item.priority
                desc = work_item.description.replace('"', '""')
                if req_item.explanation:
                    full_desc = f"{desc}【说明】{req_item.explanation}" if desc else f"【说明】{req_item.explanation}"
                    full_desc = full_desc.replace('"', '""')
                else:
                    full_desc = desc
                
                backend_hours = work_item.backend_hours
                frontend_hours = work_item.frontend_hours
                estimations = [c.backend_estimation for c in work_item.children if c.backend_estimation] + [c.frontend_estimation for c in work_item.children if c.frontend_estimation]
                complexity = " / ".join(dict.fromkeys(e["complexity_level"] for e in estimations)).replace('"', '""')
                formulas = "；".join(f'{e["base_hours"]}×{e["complexity_coefficient"]}+{e["adjustment_hours"]}={e["calculated_hours"]}' for e in estimations).replace('"', '""')
                reuse = " / ".join(dict.fromkeys(e["reuse_status"] for e in estimations)).replace('"', '""')
                reasons = "；".join(dict.fromkeys(e["adjustment_reason"] for e in estimations)).replace('"', '""')
                
                lines.append(f'"{name}","{work_name}","{priority}",{backend_hours},{frontend_hours},"{complexity}","{formulas}","{reuse}","{reasons}","{full_desc}"')
                total_backend_hours += backend_hours
                total_frontend_hours += frontend_hours
        
        lines.append(f'"总计","-","-",{total_backend_hours},{total_frontend_hours},"-","-","-","-","-"')
        return '\n'.join(lines)


class EstimationValidator:
    COEFFICIENTS = {"简单": 1.0, "普通": 1.5, "中等": 2.0, "复杂": 2.5, "极高": 3.0}

    @classmethod
    def validate_estimation(cls, estimation: Dict, hours: float, path: str, errors: List[str]):
        required = ["base_type", "base_hours", "complexity_level", "complexity_coefficient", "adjustment_hours", "calculated_hours", "reuse_status", "adjustment_reason"]
        missing = [key for key in required if key not in estimation]
        if missing:
            errors.append(f'{path}缺少估算字段：{",".join(missing)}')
            return
        expected_coefficient = cls.COEFFICIENTS.get(estimation["complexity_level"])
        if expected_coefficient != estimation["complexity_coefficient"]:
            errors.append(f'{path}复杂度系数不匹配')
        adjustment = float(estimation["adjustment_hours"])
        calculated = float(estimation["base_hours"]) * float(estimation["complexity_coefficient"]) + adjustment
        if adjustment < -2.0 or adjustment > 2.0:
            errors.append(f'{path}调整工时超出-2.0至2.0范围')
        if adjustment != 0 and not estimation["adjustment_reason"].strip():
            errors.append(f'{path}非零调整缺少原因')
        if abs(calculated - float(estimation["calculated_hours"])) > 0.01 or abs(calculated - hours) > 0.01:
            errors.append(f'{path}工时计算公式不成立')
        if hours != 0 and not 1.0 <= hours <= 24.0:
            errors.append(f'{path}非零工时不在1.0至24.0范围内')

    @classmethod
    def validate(cls, requirements: List[RequirementItem]):
        errors = []
        for requirement in requirements:
            for work_item in requirement.work_items:
                if work_item.level != "page":
                    continue
                if not work_item.children:
                    errors.append(f'{requirement.name}/{work_item.name}缺少子项')
                    continue
                backend_total = 0.0
                frontend_total = 0.0
                for child in work_item.children:
                    path = f'{requirement.name}/{work_item.name}/{child.name}'
                    if child.backend_hours:
                        if not child.backend_estimation:
                            errors.append(f'{path}缺少backend_estimation')
                        else:
                            cls.validate_estimation(child.backend_estimation, child.backend_hours, path + '/后端', errors)
                    if child.frontend_hours:
                        if not child.frontend_estimation:
                            errors.append(f'{path}缺少frontend_estimation')
                        else:
                            cls.validate_estimation(child.frontend_estimation, child.frontend_hours, path + '/前端', errors)
                    backend_total += child.backend_hours
                    frontend_total += child.frontend_hours
                if abs(backend_total - work_item.backend_hours) > 0.01:
                    errors.append(f'{requirement.name}/{work_item.name}后端父子工时不一致')
                if abs(frontend_total - work_item.frontend_hours) > 0.01:
                    errors.append(f'{requirement.name}/{work_item.name}前端父子工时不一致')
        return errors


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

    errors = EstimationValidator.validate(requirements)
    if errors:
        print("工时验收失败：")
        for error in errors:
            print(f'- {error}')
        return 1
    
    os.makedirs(args.output, exist_ok=True)
    
    work_plan_csv = CSVGenerator.generate_work_plan(requirements)
    work_plan_path = os.path.join(args.output, 'work-plan.csv')
    
    with open(work_plan_path, 'w', encoding='utf-8-sig') as f:
        f.write(work_plan_csv)
    
    print(f'工作计划预估表已生成：{work_plan_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
