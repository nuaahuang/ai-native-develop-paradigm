"""基于大语言模型的代码解析器"""

import json
import os


def parse_with_llm(code: str, model_type: str = "auto") -> dict:
    """
    使用大语言模型解析代码
    
    Args:
        code: 要解析的代码
        model_type: 模型类型（auto/claude/gpt）
    
    Returns:
        解析结果字典，包含 method, path, api_name, params, query_params, response 等字段
    """
    # 优先尝试使用模型解析
    try:
        return _parse_with_model(code)
    except Exception as e:
        print(f"LLM 解析失败，使用默认解析: {e}")
        return _parse_fallback(code)


def _parse_with_model(code: str) -> dict:
    """调用大语言模型解析代码"""
    prompt = f"""
请解析以下接口代码，提取接口信息。

代码：
{code}

请按照以下 JSON 格式输出结果：
{{
  "method": "HTTP方法（GET/POST/PUT/DELETE/PATCH）",
  "path": "接口路径",
  "api_name": "接口名称（中文）",
  "params": [
    {{
      "name": "参数名",
      "type": "类型",
      "required": true/false,
      "description": "说明"
    }}
  ],
  "query_params": [
    {{
      "name": "参数名",
      "type": "类型",
      "required": true/false,
      "description": "说明"
    }}
  ],
  "response": {{
    "code": 200,
    "message": "success",
    "data": {{
      "字段名": "示例值"
    }}
  }}
}}

注意：
1. params 是路径参数（URL 中的 {param}）
2. query_params 是查询参数（URL 中的 ?key=value）
3. 请根据代码逻辑推断接口名称和字段说明
4. 如果代码中有返回类型定义，请根据类型生成示例数据
"""
    
    # 调用模型（这里用模拟结果，实际使用时替换为真实的模型调用）
    result = _call_model(prompt)
    
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return _parse_fallback(code)


def _call_model(prompt: str) -> str:
    """调用大语言模型（模拟实现）"""
    # 在实际使用中，这里应该调用真实的模型 API
    # 如 OpenAI API、Claude API 等
    
    # 模拟返回结果（基于常见的接口代码模式）
    import re
    
    # 提取 HTTP 方法和路径
    method = "GET"
    path = ""
    
    # 尝试匹配各种模式
    patterns = [
        r'@(GetMapping|PostMapping|PutMapping|DeleteMapping)\s*\(\s*["\']([^"\']+)["\']',
        r'@app\.(get|post|put|delete)\s*\(\s*["\']([^"\']+)["\']',
        r'(GET|POST|PUT|DELETE|PATCH)\s+(/[\w/-]+(?:/\{[\w]+\})*)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, prompt)
        if match:
            method = match.group(1).replace('Mapping', '').upper() if 'Mapping' in match.group(1) else match.group(1).upper()
            path = match.group(2