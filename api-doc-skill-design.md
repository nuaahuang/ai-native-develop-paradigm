# api-doc Skill 设计方案（简化版）

## 1. 概述

`api-doc` Skill 是一个简化版的接口文档生成工具，专注于**快速生成和增量更新 Markdown 格式的接口文档**。

**核心使用场景**：在 IDE 中选中接口代码，上传 UI 截图，Skill 自动生成/更新 MD 文档。

## 2. 功能定位

| 维度 | 说明 |
|------|------|
| **核心职责** | 解析接口代码，生成/更新 MD 格式接口文档 |
| **输入** | 接口代码（选中）、UI 截图（上传）、目标文档路径 |
| **输出** | 更新后的 MD 文档 |
| **核心特性** | 自动去重、增量更新、图片嵌入、格式统一 |

## 3. 输入规范

### 3.1 输入参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `code` | String | 是 | 选中的接口代码（支持多种语言） |
| `ui_image` | Image/URL | 否 | UI 截图（聊天窗口上传） |
| `output_file` | String | 是 | 目标 MD 文档路径 |
| `api_name` | String | 否 | 接口名称（自动解析，可手动指定） |

### 3.2 支持的代码类型

| 语言/框架 | 支持程度 | 解析能力 |
|-----------|----------|----------|
| Java Spring Boot | ✅ 完全支持 | 解析 @GetMapping/@PostMapping、参数、返回值 |
| Python FastAPI | ✅ 完全支持 | 解析 @app.get/@app.post、Pydantic 模型 |
| Node.js Express | ✅ 支持 | 解析路由定义、请求响应 |
| TypeScript | ✅ 支持 | 解析类型定义、接口声明 |
| Go Gin | ✅ 支持 | 解析路由、结构体 |
| 纯文本 URL | ✅ 支持 | 解析 URL、HTTP 方法 |

### 3.3 输入示例

#### 示例 1：Java Spring Boot
```java
@GetMapping("/ai-gxs/plan/stage-report/{reportId}")
public ResponseEntity<ApiResponse<StageReportDTO>> getStageReport(
    @PathVariable String reportId,
    @RequestParam(required = false) String status
) {
    // 查询阶段报告
    StageReportDTO report = reportService.getById(reportId);
    return ResponseEntity.ok(ApiResponse.success(report));
}
```

#### 示例 2：Python FastAPI
```python
@app.get("/ai-gxs/plan/stage-report/{reportId}")
def get_stage_report(
    reportId: str,
    status: Optional[str] = None
) -> ApiResponse[StageReportDTO]:
    """查询阶段报告详情"""
    report = report_service.get_by_id(reportId)
    return ApiResponse.success(report)
```

#### 示例 3：纯文本 URL
```
GET /ai-gxs/plan/stage-report/{reportId}
```

## 4. 输出规范

### 4.1 输出格式（Markdown）

每个接口文档记录格式如下：

```markdown
---

## 接口：查询阶段报告详情

### 基本信息

| 项目 | 值 |
|------|-----|
| **接口路径** | `GET /ai-gxs/plan/stage-report/{reportId}` |
| **所属文件** | `controller/ReportController.java` |
| **最后更新** | 2024-01-28 10:30:00 |

### UI 截图

![阶段报告详情页](stage-report-detail.png)

### 请求参数

#### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| reportId | String | 是 | 报告编号 |

#### 查询参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| status | String | 否 | 报告状态过滤 |

### 响应结构

#### 成功响应（200 OK）

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "reportId": "RPT-20240101-001",
    "stageType": 1,
    "stage": "阶段一",
    "day": 28,
    "totalDays": 90
  }
}
```

#### 字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | Integer | 响应码 |
| message | String | 响应消息 |
| data | Object | 数据体 |
| data.reportId | String | 报告编号 |
| data.stageType | Integer | 阶段类型 |
| data.stage | String | 阶段名称 |
| data.day | Integer | 当前天数 |
| data.totalDays | Integer | 总天数 |

### 错误响应

| HTTP 状态码 | 说明 |
|-------------|------|
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 404 | 报告不存在 |
```

### 4.2 文档结构

```markdown
# 接口文档

> 自动生成，请勿手动修改

---

## 目录

1. [查询阶段报告详情](#接口查询阶段报告详情)
2. [创建阶段报告](#接口创建阶段报告)
3. [更新阶段报告](#接口更新阶段报告)

---

<!-- 接口文档记录 -->
```

## 5. 核心处理流程

```
┌─────────────────────────────────────────────────────────────────┐
│                        api-doc Skill                          │
├─────────────────────────────────────────────────────────────────┤
│  Step 1: 代码解析                                             │
│    ├── 识别代码类型（Java/Python/JS/Go/纯文本）                  │
│    ├── 解析 HTTP 方法和路径                                    │
│    ├── 解析请求参数（路径/查询/请求体）                          │
│    └── 解析响应结构和字段                                      │
├─────────────────────────────────────────────────────────────────┤
│  Step 2: 去重判断                                             │
│    ├── 读取目标 MD 文档                                        │
│    ├── 根据接口路径判断是否已存在                                │
│    ├── 如果存在：标记为需要更新                                  │
│    └── 如果不存在：标记为新增                                    │
├─────────────────────────────────────────────────────────────────┤
│  Step 3: 图片处理（如有）                                       │
│    ├── 保存上传的图片到指定目录                                  │
│    ├── 生成图片引用路径                                        │
│    └── 优化图片大小（如有必要）                                  │
├─────────────────────────────────────────────────────────────────┤
│  Step 4: 文档生成/更新                                         │
│    ├── 生成接口文档片段                                        │
│    ├── 更新目录（如有新增）                                      │
│    ├── 替换或追加文档内容                                        │
│    └── 更新最后修改时间                                        │
├─────────────────────────────────────────────────────────────────┤
│  Step 5: 输出                                                 │
│    └── 保存更新后的 MD 文档                                     │
└─────────────────────────────────────────────────────────────────┘
```

## 6. 核心算法与规则

### 6.1 代码解析规则

| 代码类型 | 解析方法 | 提取内容 |
|----------|----------|----------|
| Java Spring | 正则匹配注解 | @GetMapping/@PostMapping、@PathVariable、@RequestParam |
| Python FastAPI | 正则匹配装饰器 | @app.get/@app.post、函数参数、返回类型注解 |
| Express | 正则匹配路由 | app.get/app.post、req.params、req.query |
| TypeScript | 解析类型定义 | interface、type、函数签名 |
| Go Gin | 正则匹配路由 | r.GET/r.POST、结构体字段 |
| 纯文本 URL | 正则提取 | HTTP 方法、路径、参数 |

### 6.2 去重判断规则

| 判断依据 | 说明 |
|----------|------|
| **接口路径** | 作为唯一标识，如 `/ai-gxs/plan/stage-report/{reportId}` |
| **匹配方式** | 完全匹配路径（忽略参数名差异） |
| **更新策略** | 相同路径 → 更新，不同路径 → 新增 |

### 6.3 图片处理规则

| 规则 | 说明 |
|------|------|
| **保存位置** | 与 MD 文档同目录下的 `images/` 文件夹 |
| **命名规则** | 接口路径转义 + 时间戳，如 `stage-report_20240128103000.png` |
| **引用方式** | 相对路径引用，如 `![描述](images/stage-report_20240128103000.png)` |
| **格式支持** | PNG、JPG、GIF、WebP |

## 7. 调用方式

### 7.1 Skill 调用（Trae/Cursor）

```
# 基础调用：选中代码后调用
/api-doc --output="./docs/api.md"

# 指定接口名称
/api-doc --output="./docs/api.md" --api-name="查询阶段报告详情"

# 更新已存在的接口文档（选中代码后调用）
/api-doc --output="./docs/api.md" --update
```

### 7.2 完整流程示例

1. **在 IDE 中选中接口代码**
   ```java
   @GetMapping("/ai-gxs/plan/stage-report/{reportId}")
   public ResponseEntity<ApiResponse<StageReportDTO>> getStageReport(
       @PathVariable String reportId) { ... }
   ```

2. **在聊天窗口上传 UI 截图**

3. **调用 Skill**
   ```
   /api-doc --output="./docs/api.md"
   ```

4. **Skill 自动完成**
   - 解析代码，提取接口信息
   - 判断是否已存在（根据路径）
   - 生成/更新文档
   - 保存图片并引用

## 8. 文档格式规范

### 8.1 标题层级

```markdown
# 接口文档（一级标题，固定）
## 目录（二级标题，自动生成）
## 接口：XXX（二级标题，接口名称）
### 基本信息（三级标题）
### UI 截图（三级标题，如有）
### 请求参数（三级标题）
#### 路径参数（四级标题）
#### 查询参数（四级标题）
#### 请求体（四级标题，如有）
### 响应结构（三级标题）
#### 成功响应（四级标题）
#### 字段说明（四级标题）
### 错误响应（三级标题）
```

### 8.2 表格格式

| 类型 | 列定义 |
|------|--------|
| 基本信息 | 项目、值 |
| 请求参数 | 参数名、类型、必填、说明 |
| 响应字段 | 字段名、类型、说明 |
| 错误响应 | HTTP 状态码、说明 |

### 8.3 代码块格式

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

## 9. 增量更新机制

### 9.1 更新策略

| 场景 | 处理方式 |
|------|----------|
| **接口不存在** | 在文档末尾追加新接口文档 |
| **接口已存在** | 替换原有接口文档，保留位置 |
| **更新目录** | 自动同步目录项 |
| **保留历史** | 覆盖更新（如需历史版本，使用版本控制） |

### 9.2 更新流程

1. 读取目标 MD 文档
2. 根据接口路径查找是否已存在
3. 如果存在：
   - 定位到该接口文档位置
   - 替换内容（保留标题，更新其他部分）
   - 更新最后修改时间
4. 如果不存在：
   - 在文档末尾追加新接口文档
   - 更新目录

## 10. 错误处理

### 10.1 输入验证错误

| 错误类型 | 错误消息 |
|----------|----------|
| 缺少代码 | "请先选中接口代码" |
| 缺少输出文件路径 | "请指定输出文件路径，如 --output=\"./docs/api.md\"" |
| 无法解析代码 | "无法解析选中的代码，请检查代码格式" |

### 10.2 文件操作错误

| 错误类型 | 错误消息 |
|----------|----------|
| 文件不存在 | "目标文件不存在，将创建新文件" |
| 无法写入 | "无法写入文件，请检查文件权限" |
| 图片保存失败 | "图片保存失败，将跳过图片插入" |

### 10.3 降级策略

当发生非致命错误时：
- 跳过失败部分（如图片）
- 继续生成其他内容
- 在输出中标记 WARNING

## 11. 扩展性

### 11.1 支持的代码类型扩展

通过插件机制支持更多语言：
```
api-doc/
├── parsers/
│   ├── java.py       # Java 解析器
│   ├── python.py     # Python 解析器
│   ├── typescript.py # TypeScript 解析器
│   └── go.py         # Go 解析器
└── templates/
    └── markdown/     # MD 输出模板
```

### 11.2 输出格式扩展

支持输出不同格式：
- Markdown（默认）
- HTML
- Confluence 格式

---

## 附录：输出示例

完整的接口文档输出示例：

```markdown
# 接口文档

> 自动生成，请勿手动修改

---

## 目录

1. [查询阶段报告详情](#接口查询阶段报告详情)

---

## 接口：查询阶段报告详情

### 基本信息

| 项目 | 值 |
|------|-----|
| **接口路径** | `GET /ai-gxs/plan/stage-report/{reportId}` |
| **所属文件** | `controller/ReportController.java` |
| **最后更新** | 2024-01-28 10:30:00 |

### UI 截图

![阶段报告详情页](images/stage-report_20240128103000.png)

### 请求参数

#### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| reportId | String | 是 | 报告编号 |

### 响应结构

#### 成功响应（200 OK）

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "reportId": "RPT-20240101-001",
    "stageType": 1,
    "stageTypeDesc": "中间阶段",
    "day": 28,
    "stage": "阶段一",
    "totalDays": 90,
    "achievements": "完成基础体能训练",
    "currentChanges": "睡眠质量提升",
    "createdAt": "2024-01-28T10:30:00"
  }
}
```

#### 字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | Integer | 响应码，200 表示成功 |
| message | String | 响应消息 |
| data | Object | 响应数据体 |
| data.reportId | String | 报告编号 |
| data.stageType | Integer | 阶段类型：1-中间阶段，2-最终阶段 |
| data.stageTypeDesc | String | 阶段类型描述 |
| data.day | Integer | 当前天数 |
| data.stage | String | 阶段名称 |
| data.totalDays | Integer | 总天数 |
| data.achievements | String | 阶段成果 |
| data.currentChanges | String | 当前变化 |
| data.createdAt | String | 创建时间 |

### 错误响应

| HTTP 状态码 | 说明 |
|-------------|------|
| 400 | 请求参数错误，如 reportId 为空 |
| 401 | 未授权，请携带 Token |
| 404 | 报告不存在 |
| 500 | 系统内部错误 |
```