---
name: api-doc
description: 版本迭代过程中，快速生成供前后端交流用的 Markdown 接口文档。支持从选中代码自动提取接口定义，增量更新。专注人工阅读交流，不生成机器消费的 OpenAPI。本工具只生成文档和测试示例代码，不实际发送网络请求。
author: deganghuang
version: 2.2.0
---

# api-doc

## 命令

/api-doc --output="./docs/api.md" [options]

## 使用场景

- 当需要生成或更新接口文档时触发
- 用户在编辑器中选中接口代码后触发
- 需要导出 OpenAPI 格式集成到其他工具时触发

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| --output | 是 | 输出文档路径，如 ./docs/api.md |
| --api-name | 否 | 接口名称，不指定则自动推断 |
| --export-openapi | 否 | 导出 OpenAPI 3.0 文件路径，支持 .json/.yaml |

## 工作流程

1. **解析代码**：识别代码类型（Java Spring / Python FastAPI / Express / Go Gin），提取 HTTP 方法、接口路径、参数和响应结构
2. **分配序号**：**必须**为每个接口分配唯一序号，根据文档中已有接口数量自动递增
3. **去重判断**：读取目标 MD 文档，根据接口路径判断是否已存在，存在则更新序号保持不变，不存在则分配新序号
4. **生成文档**：创建或更新 Markdown 格式的接口文档，**强制包含序号**，更新目录索引

## 支持的代码类型

| 语言/框架 | 示例代码 |
|-----------|----------|
| Java Spring | `@GetMapping("/api/report/{id}")` |
| Python FastAPI | `@app.get("/api/report/{id}")` |
| Python Django REST Framework | `@api_view(['GET'])` |
| Python Flask | `@app.route("/api/report/<id>")` |
| Express | `app.get("/api/report/:id")` |
| Go Gin | `r.GET("/api/report/:id")` |
| 纯文本 URL | `GET /api/report/{id}` |

## 输出解释

### 输出文档结构

```markdown
# 接口文档

## 目录
1. [1-查询阶段报告详情](#1-接口查询阶段报告详情)
2. [2-创建订单](#2-接口创建订单)

---

## 1-接口：查询阶段报告详情

### 基本信息

| 项目 | 值 |
|------|-----|
| **接口序号** | 1 |
| **接口名称** | 查询阶段报告详情 |
| **接口路径** | `GET /api/report/{id}` |

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | String | 是 | 报告ID |

### 响应结构

```json
{
  "code": 200,
  "message": "success",
  "data": {...}
}
```

---

## 2-接口：创建订单

### 基本信息

| 项目 | 值 |
|------|-----|
| **接口序号** | 2 |
| **接口名称** | 创建订单 |
| **接口路径** | `POST /api/order` |
```

## 示例

### 示例 1：基本用法（单个接口）

```
/api-doc --output="./docs/api.md"
```

### 示例 2：指定接口名称

```
/api-doc --output="./docs/api.md" --api-name="查询阶段报告详情"
```

### 示例 3：导出 OpenAPI

```
/api-doc --output="./docs/api.md" --export-openapi=./docs/openapi.json
```

### 示例 4：导出 OpenAPI YAML 格式

```
/api-doc --output="./docs/api.md" --export-openapi=./docs/openapi.yaml
```

## 注意事项

1. **强制序号**：每个接口**必须**包含唯一序号，序号从 1 开始递增，不可重复或跳过
2. **序号保持**：更新已存在的接口时，序号保持不变
3. 确保选中的代码包含完整的接口定义
4. 相同路径的接口会自动更新，不会重复添加
5. 生成的文档格式统一，便于拷贝和迁移