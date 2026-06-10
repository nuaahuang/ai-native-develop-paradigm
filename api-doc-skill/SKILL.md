---
name: api-doc
description: 自动生成和更新 Markdown 格式的接口文档。支持从选中的代码中提取接口信息，自动判断接口是否已存在，支持上传 UI 截图。
author: deganghuang
version: 1.0.0
---

# api-doc

## 命令

/api-doc --output="./docs/api.md" [--api-name="接口名称"] [--image-format="base64"]

## 使用场景

- 当需要生成或更新接口文档时触发
- 用户在编辑器中选中接口代码后触发
- 用户上传 UI 截图并需要生成带图标的接口文档时触发

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| --output | 是 | 输出文档路径，如 ./docs/api.md |
| --api-name | 否 | 接口名称，不指定则自动推断 |
| --image-format | 否 | 图片格式：local（默认）/ base64 / url |
| --image-upload | 否 | 图片上传目标：wecom / qiniu / oss |
| --image-dir | 否 | 本地图片保存目录（默认：./images） |

## 工作流程

1. **解析代码**：识别代码类型（Java Spring / Python FastAPI / Express / Go Gin），提取 HTTP 方法、接口路径、参数和响应结构
2. **去重判断**：读取目标 MD 文档，根据接口路径判断是否已存在，存在则更新，不存在则新增
3. **处理图片**：保存上传的图片到文档目录下的 images 文件夹，生成图片引用路径
4. **生成文档**：创建或更新 Markdown 格式的接口文档，更新目录索引

## 支持的代码类型

| 语言/框架 | 示例代码 |
|-----------|----------|
| Java Spring | `@GetMapping("/api/report/{id}")` |
| Python FastAPI | `@app.get("/api/report/{id}")` |
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

### UI 截图

![截图](images/report.png)

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

### 企业微信迁移方案

使用 `--image-format="base64"` 参数可以将图片转为 Base64 编码内联到文档中，方便拷贝到企业微信文档。

## 示例

### 示例 1：基本用法

```
/api-doc --output="./docs/api.md"
```

### 示例 2：指定接口名称

```
/api-doc --output="./docs/api.md" --api-name="查询阶段报告详情"
```

### 示例 3：生成适合企业微信的文档（图片内联）

```
/api-doc --output="./docs/api.md" --image-format="base64"
```

## 注意事项

1. 确保选中的代码包含完整的接口定义
2. UI 截图会保存到文档目录下的 images 文件夹（使用 local 格式时）
3. 相同路径的接口会自动更新，不会重复添加
4. 生成的文档格式统一，便于拷贝和迁移