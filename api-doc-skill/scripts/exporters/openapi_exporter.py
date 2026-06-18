import json
import yaml
from typing import List, Optional, Dict, Any
from datetime import datetime
from scripts.models.api_info import ApiInfo
from scripts.models.parameter import Parameter, ParameterLocation
from scripts.models.response import ResponseInfo


class OpenApiExporter:
    """OpenAPI 3.0 导出器"""

    def __init__(self, title: str = "API 文档", version: str = "1.0.0"):
        self.title = title
        self.version = version

    def _location_to_openapi(self, location: ParameterLocation) -> str:
        """转换参数位置到 OpenAPI 格式"""
        mapping = {
            ParameterLocation.PATH: "path",
            ParameterLocation.QUERY: "query",
            ParameterLocation.BODY: "body",
            ParameterLocation.FORM: "formData",
            ParameterLocation.HEADER: "header",
        }
        return mapping.get(location, "query")

    def _type_to_openapi(self, type_: str) -> Dict[str, Any]:
        """转换类型到 OpenAPI 格式"""
        type_lower = type_.lower()

        if type_lower in ['string', 'str', 'text']:
            return {"type": "string"}
        elif type_lower in ['int', 'integer', 'long']:
            return {"type": "integer"}
        elif type_lower in ['float', 'double', 'number']:
            return {"type": "number"}
        elif type_lower in ['bool', 'boolean']:
            return {"type": "boolean"}
        elif type_lower in ['dict', 'object', 'model']:
            return {"type": "object"}
        elif type_lower in ['list', 'array', 'slice']:
            return {"type": "array", "items": {"type": "string"}}
        else:
            # 默认当作引用类型
            return {"$ref": f"#/components/schemas/{type_}"}

    def export(self, apis: List[ApiInfo], format: str = "json") -> str:
        """导出 OpenAPI 文档"""
        openapi: Dict[str, Any] = {
            "openapi": "3.0.0",
            "info": {
                "title": self.title,
                "version": self.version,
                "description": "自动生成的 API 文档",
            },
            "servers": [
                {
                    "url": "/"
                }
            ],
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": {}
            }
        }

        # 处理每个接口
        for api in apis:
            path = api.full_path
            method = api.http_method.lower()

            if path not in openapi["paths"]:
                openapi["paths"][path] = {}

            openapi["paths"][path][method] = self._build_operation(api)

        # 输出
        if format == "yaml":
            return yaml.dump(openapi, allow_unicode=True, default_flow_style=False)
        else:
            return json.dumps(openapi, indent=2, ensure_ascii=False)

    def _build_operation(self, api: ApiInfo) -> Dict[str, Any]:
        """构建 operation 对象"""
        operation: Dict[str, Any] = {
            "summary": api.name,
            "description": api.description or f"{api.name} 接口",
            "parameters": [],
            "responses": {},
        }

        # 处理参数
        path_params = []
        query_params = []
        body_param = None

        for param in api.parameters:
            if param.location == ParameterLocation.BODY:
                body_param = param
            else:
                openapi_param = {
                    "name": param.name,
                    "in": self._location_to_openapi(param.location),
                    "required": param.required,
                    "description": param.description or f"{param.name} 参数",
                    "schema": self._type_to_openapi(param.type_),
                }
                if param.location == ParameterLocation.PATH:
                    path_params.append(openapi_param)
                else:
                    query_params.append(openapi_param)

        operation["parameters"] = path_params + query_params

        # 请求体
        if body_param:
            operation["requestBody"] = {
                "description": body_param.description or "请求体",
                "required": body_param.required,
                "content": {
                    "application/json": {
                        "schema": self._type_to_openapi(body_param.type_)
                    }
                }
            }

        # 响应
        for resp in api.responses:
            status_key = str(resp.status_code)
            response_desc = resp.description or "响应"

            content = {}
            if resp.example_json:
                content["application/json"] = {
                    "example": json.loads(resp.example_json) if resp.example_json.strip() else {}
                }

            operation["responses"][status_key] = {
                "description": response_desc,
                "content": content,
            }

        # 默认 200 响应
        if not operation["responses"]:
            operation["responses"]["200"] = {
                "description": "成功",
                "content": {
                    "application/json": {
                        "example": {
                            "code": 200,
                            "message": "success",
                            "data": {}
                        }
                    }
                }
            }

        return operation

    def save(self, apis: List[ApiInfo], output_path: str, format: str = "json"):
        """保存到文件"""
        content = self.export(apis, format)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
