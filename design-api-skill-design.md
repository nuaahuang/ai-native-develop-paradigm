# design-api Skill 详细设计方案

## 1. 概述

`design-api` Skill 负责**接口设计 + UI↔API 映射**，是 AI-Native 开发范式中的核心设计阶段（对应 Phase 2b）。该 Skill 可独立使用，特别适合快速生成接口文档的场景。

**核心使用场景**：写完接口后，上传 UI 截图和接口信息，Skill 自动生成带截图标注的接口文档（MD 格式），支持增量更新，方便拷贝迁移。

## 2. 功能定位

| 维度 | 说明 |
|------|------|
| **阶段定位** | Phase 2b：接口设计 + UI↔API 映射 |
| **核心职责** | 根据表结构和 UI Element Tree 设计接口，生成 OpenAPI 规范和字段映射文档 |
| **输入来源** | 表结构设计、UI Element Tree、Product Map（可选）、UI 截图（可选） |
| **输出产物** | OpenAPI 规范、UI↔API 映射表（MD/HTML）、Mock 数据、接口文档 |

## 3. 输入规范

### 3.1 输入参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `schema` | SQL/JSON | 是 | 数据库表结构（SQL DDL 或 JSON 格式） |
| `ui_elements` | JSON | 是 | UI Element Tree（页面→区块→字段结构） |
| `ui_screenshot` | Image/URL | 否 | UI 截图（带标注的设计图） |
| `product_map` | JSON/YAML | 否 | 现有 Product Map，用于增量设计 |
| `api_base_path` | String | 否 | API 基础路径（默认：`/api`） |
| `output_format` | String | 否 | 输出格式：markdown（推荐）/ html（默认：markdown） |
| `output_file` | String | 否 | 输出文件路径（支持增量更新） |
| `api_info` | JSON | 否 | 接口元信息（名称、描述、认证方式等） |

### 3.2 输入格式示例

#### 表结构输入（SQL DDL）
```sql
CREATE TABLE `stage_report` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '报告ID',
  `report_id` VARCHAR(64) NOT NULL COMMENT '报告编号',
  `stage_type` TINYINT NOT NULL DEFAULT 1 COMMENT '阶段类型：1-中间阶段 2-最终阶段',
  `day` INT NOT NULL COMMENT '天数',
  `stage` VARCHAR(64) NOT NULL COMMENT '阶段名称',
  `total_days` INT NOT NULL COMMENT '总天数',
  `adjustment_effect_title` VARCHAR(256) COMMENT '调整效果标题',
  `adjustment_effect_detail` TEXT COMMENT '调整效果详情',
  `achievements` TEXT COMMENT '阶段成果',
  `current_changes` TEXT COMMENT '当前变化',
  `next_stage_suggestion_title` VARCHAR(256) COMMENT '下一阶段建议标题',
  `next_stage_suggestion_detail` TEXT COMMENT '下一阶段建议详情',
  `next_stage_focus` TEXT COMMENT '下一阶段重点',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_report_id` (`report_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='阶段报告表';
```

#### UI Element Tree 输入（JSON）
```json
{
  "pages": [
    {
      "pageName": "阶段报告详情页",
      "blocks": [
        {
          "blockName": "阶段信息",
          "fields": [
            {"name": "stageType", "label": "阶段类型", "type": "enum", "options": ["中间阶段", "最终阶段"], "annotation": "1"},
            {"name": "day", "label": "天数", "type": "integer", "annotation": "2"},
            {"name": "stage", "label": "阶段名称", "type": "string", "annotation": "3"},
            {"name": "totalDays", "label": "总天数", "type": "integer", "annotation": "4"}
          ]
        },
        {
          "blockName": "调整效果",
          "fields": [
            {"name": "adjustmentEffect.title", "label": "标题", "type": "string", "annotation": "5"},
            {"name": "adjustmentEffect.detail", "label": "详情", "type": "text", "annotation": "6"}
          ]
        },
        {
          "blockName": "阶段成果",
          "fields": [
            {"name": "achievements", "label": "阶段成果", "type": "text", "annotation": "6"}
          ]
        },
        {
          "blockName": "当前变化",
          "fields": [
            {"name": "currentChanges", "label": "当前变化", "type": "text", "annotation": "7"}
          ]
        },
        {
          "blockName": "下一阶段建议",
          "fields": [
            {"name": "nextStageSuggestion.title", "label": "标题", "type": "string", "annotation": "8"},
            {"name": "nextStageSuggestion.detail", "label": "详情", "type": "text", "annotation": "8"},
            {"name": "nextStageFocus", "label": "重点", "type": "text", "annotation": "9"}
          ]
        }
      ]
    }
  ]
}
```

#### API 元信息输入（JSON）
```json
{
  "apiName": "查询阶段报告详情",
  "apiDescription": "根据报告ID查询阶段报告详情信息",
  "httpMethod": "GET",
  "path": "/ai-gxs/plan/stage-report/{reportId}",
  "authType": "Bearer",
  "version": "v1",
  "tags": ["计划管理", "阶段报告"]
}
```

## 4. 输出规范

### 4.1 输出产物清单

| 产物 | 格式 | 用途 |
|------|------|------|
| **OpenAPI 规范** | YAML | 标准 OpenAPI 3.1 格式接口文档 |
| **UI↔API 映射表** | Markdown（推荐） | 截图标注与字段的映射关系，方便拷贝迁移 |
| **接口文档** | Markdown | 完整的接口说明文档 |
| **Mock 数据** | JSON | 模拟响应数据 |
| **变更清单** | Markdown | 相对于现有文档的增量变更 |

### 4.2 输出格式示例

#### UI↔API 映射表输出（Markdown）
```markdown
# 接口文档：查询阶段报告详情

---

## 一、接口信息

| 项目 | 值 |
|------|-----|
| **接口名称** | 查询阶段报告详情 |
| **接口路径** | `GET /ai-gxs/plan/stage-report/{reportId}` |
| **认证方式** | Bearer Token |
| **版本** | v1 |
| **所属模块** | 计划管理 / 阶段报告 |

---

## 二、UI 截图与字段映射

![阶段报告详情页](stage-report-detail.png)

### 字段映射说明

| 标注号 | UI 位置 | 字段名 | 接口字段 | 类型 | 说明 |
|--------|----------|--------|----------|------|------|
| 1 | 阶段信息 → 阶段类型 | stageType | stageType | Integer | 阶段类型：1-中间阶段，2-最终阶段 |
| 2 | 阶段信息 → 天数 | day | day | Integer | 天数 |
| 3 | 阶段信息 → 阶段名称 | stage | stage | String | 阶段名称 |
| 4 | 阶段信息 → 总天数 | totalDays | totalDays | Integer | 总天数 |
| 5 | 调整效果 → 标题 | adjustmentEffect.title | adjustmentEffect.title | String | 调整效果标题 |
| 6 | 调整效果 → 详情 / 阶段成果 | adjustmentEffect.detail / achievements | adjustmentEffect.detail | String | 调整效果详情 |
| 6 | 调整效果 → 详情 / 阶段成果 | achievements | achievements | String | 阶段成果 |
| 7 | 当前变化 | currentChanges | currentChanges | String | 当前变化描述 |
| 8 | 下一阶段建议 → 标题/详情 | nextStageSuggestion.title/detail | nextStageSuggestion.title | String | 下一阶段建议标题 |
| 8 | 下一阶段建议 → 标题/详情 | nextStageSuggestion.title/detail | nextStageSuggestion.detail | String | 下一阶段建议详情 |
| 9 | 下一阶段建议 → 重点 | nextStageFocus | nextStageFocus | String | 下一阶段重点 |

---

## 三、请求参数

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| reportId | String | 是 | 报告编号 |

### 查询参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|

---

## 四、响应结构

### 成功响应（200 OK）

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
    "adjustmentEffect": {
      "title": "身体状态已进入稳定阶段",
      "detail": "经过28天的调整，身体各项指标已趋于稳定..."
    },
    "achievements": "完成了基础体能训练，体重下降5kg...",
    "currentChanges": "睡眠质量提升，精力充沛...",
    "nextStageSuggestion": {
      "title": "建议进入巩固期",
      "detail": "建议在接下来的阶段中保持现有训练强度..."
    },
    "nextStageFocus": "核心力量训练、饮食控制",
    "createdAt": "2024-01-28T10:30:00"
  }
}
```

### 字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| reportId | String | 报告编号 |
| stageType | Integer | 阶段类型：1-中间阶段，2-最终阶段 |
| stageTypeDesc | String | 阶段类型描述 |
| day | Integer | 当前天数 |
| stage | String | 阶段名称 |
| totalDays | Integer | 总天数 |
| adjustmentEffect | Object | 调整效果 |
| adjustmentEffect.title | String | 调整效果标题 |
| adjustmentEffect.detail | String | 调整效果详情 |
| achievements | String | 阶段成果 |
| currentChanges | String | 当前变化 |
| nextStageSuggestion | Object | 下一阶段建议 |
| nextStageSuggestion.title | String | 建议标题 |
| nextStageSuggestion.detail | String | 建议详情 |
| nextStageFocus | String | 下一阶段重点 |
| createdAt | String | 创建时间 |

---

## 五、错误响应

| HTTP 状态码 | 错误码 | 错误消息 | 说明 |
|-------------|--------|----------|------|
| 400 | 40001 | "reportId 不能为空" | 参数校验失败 |
| 401 | 40101 | "未授权，请登录" | 未携带 Token 或 Token 无效 |
| 404 | 40401 | "报告不存在" | 报告 ID 不存在 |
| 500 | 50001 | "系统内部错误" | 服务器异常 |

---

## 六、业务规则说明

1. **stageType 区分**：
   - 值为 1 表示中间阶段报告
   - 值为 2 表示最终阶段报告

2. **数据权限**：
   - 只能查询当前用户有权限查看的报告
   - 管理员可以查看所有报告

---

## 七、变更历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1 | 2024-01-28 | 初始版本 |

---

*Generated by design-api Skill*
```

#### OpenAPI 输出（YAML）
```yaml
openapi: 3.1.0
info:
  title: 阶段报告接口
  description: 阶段报告相关接口定义
  version: v1
servers:
  - url: /ai-gxs/plan
paths:
  /stage-report/{reportId}:
    get:
      summary: 查询阶段报告详情
      description: 根据报告ID查询阶段报告详情信息
      tags:
        - 计划管理
        - 阶段报告
      security:
        - BearerAuth: []
      parameters:
        - name: reportId
          in: path
          required: true
          description: 报告编号
          schema:
            type: string
      responses:
        '200':
          description: 成功响应
          content:
            application/json:
              schema:
                type: object
                properties:
                  code:
                    type: integer
                    example: 200
                  message:
                    type: string
                    example: success
                  data:
                    type: object
                    properties:
                      reportId:
                        type: string
                        description: 报告编号
                      stageType:
                        type: integer
                        description: 阶段类型
                      stageTypeDesc:
                        type: string
                        description: 阶段类型描述
                      day:
                        type: integer
                        description: 当前天数
                      stage:
                        type: string
                        description: 阶段名称
                      totalDays:
                        type: integer
                        description: 总天数
                      adjustmentEffect:
                        type: object
                        properties:
                          title:
                            type: string
                            description: 调整效果标题
                          detail:
                            type: string
                            description: 调整效果详情
                      achievements:
                        type: string
                        description: 阶段成果
                      currentChanges:
                        type: string
                        description: 当前变化
                      nextStageSuggestion:
                        type: object
                        properties:
                          title:
                            type: string
                            description: 建议标题
                          detail:
                            type: string
                            description: 建议详情
                      nextStageFocus:
                        type: string
                        description: 下一阶段重点
                      createdAt:
                        type: string
                        format: date-time
                        description: 创建时间
        '400':
          description: 请求参数错误
        '401':
          description: 未授权
        '404':
          description: 报告不存在
        '500':
          description: 系统内部错误
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
```

#### Mock 数据输出（JSON）
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
    "adjustmentEffect": {
      "title": "身体状态已进入稳定阶段",
      "detail": "经过28天的调整，身体各项指标已趋于稳定，体重下降5kg，体脂率下降3%。"
    },
    "achievements": "完成了基础体能训练计划，包括每日30分钟有氧运动和力量训练。饮食控制初见成效。",
    "currentChanges": "睡眠质量明显提升，平均睡眠时间达到7.5小时。精力充沛，工作效率提高。",
    "nextStageSuggestion": {
      "title": "建议进入巩固期",
      "detail": "建议在接下来的阶段中保持现有训练强度，重点关注核心力量训练和饮食精细化管理。"
    },
    "nextStageFocus": "核心力量训练、饮食控制精细化、定期身体检测",
    "createdAt": "2024-01-28T10:30:00"
  }
}
```

## 5. 核心处理流程

```
┌─────────────────────────────────────────────────────────────────┐
│                       design-api Skill                         │
├─────────────────────────────────────────────────────────────────┤
│  Step 1: 输入解析                                               │
│    ├── 解析表结构（SQL DDL 或 JSON）                              │
│    ├── 解析 UI Element Tree（提取字段定义和标注号）                 │
│    └── 解析 API 元信息（路径、方法、认证等）                        │
├─────────────────────────────────────────────────────────────────┤
│  Step 2: 接口设计                                               │
│    ├── 根据表结构生成接口字段                                    │
│    ├── 设计请求参数（路径参数、查询参数、请求体）                    │
│    ├── 设计响应结构（成功响应、错误响应）                          │
│    └── 生成 OpenAPI 规范                                        │
├─────────────────────────────────────────────────────────────────┤
│  Step 3: UI↔API 映射                                           │
│    ├── 建立 UI 标注与 API 字段的映射关系                          │
│    ├── 生成字段映射表（标注号、UI位置、字段名、类型、说明）          │
│    └── 生成映射可视化（截图 + 标注 + 字段说明）                    │
├─────────────────────────────────────────────────────────────────┤
│  Step 4: Mock 数据生成                                          │
│    ├── 根据字段类型生成合理的模拟数据                              │
│    ├── 支持自定义 Mock 规则                                      │
│    └── 生成 JSON 格式的 Mock 数据                                │
├─────────────────────────────────────────────────────────────────┤
│  Step 5: 增量更新处理（如果指定了输出文件）                         │
│    ├── 读取现有文档                                              │
│    ├── 识别变更部分（新增/修改/删除）                              │
│    ├── 合并更新内容                                              │
│    └── 保留变更历史                                              │
├─────────────────────────────────────────────────────────────────┤
│  Step 6: 业务规则检查点                                         │
│    ├── 识别涉及业务规则的接口（金额计算、权限校验等）                │
│    ├── 生成业务规则说明                                          │
│    └── 标记需要人工确认的业务规则                                  │
├─────────────────────────────────────────────────────────────────┤
│  Step 7: 输出                                                   │
│    ├── 接口文档（Markdown）                                       │
│    ├── OpenAPI 规范（YAML）                                       │
│    ├── Mock 数据（JSON）                                         │
│    └── 变更清单（Markdown）                                       │
└─────────────────────────────────────────────────────────────────┘
```

## 6. 核心算法与规则

### 6.1 接口设计规则

| 规则类型 | 规则描述 |
|----------|----------|
| **路径命名** | 使用短横线分隔，小写字母，如 `/ai-gxs/plan/stage-report/{id}` |
| **HTTP 方法** | GET（查询）、POST（创建）、PUT（更新）、DELETE（删除） |
| **参数分类** | 路径参数（必选）、查询参数（可选）、请求体（复杂对象） |
| **响应结构** | 统一格式：`{code, message, data}` |

### 6.2 UI↔API 映射规则

| 规则类型 | 规则描述 |
|----------|----------|
| **标注号匹配** | 根据 UI Element Tree 中的 `annotation` 字段匹配截图标注 |
| **字段命名** | API 字段使用小驼峰，如 `stageType` |
| **嵌套结构** | 支持多级嵌套字段，如 `adjustmentEffect.title` |
| **类型映射** | UI 类型 → API 类型：text→string，number→integer/decimal，select→enum |

### 6.3 Mock 数据生成规则

| 规则类型 | 规则描述 |
|----------|----------|
| **字符串字段** | 根据字段名生成合理内容（如 `title`→"标题内容"，`detail`→"详细描述..."） |
| **数字字段** | 根据字段含义生成合理范围的值（如 `day`→1-365） |
| **枚举字段** | 从选项列表中随机选取 |
| **日期字段** | 生成最近 30 天内的日期 |

### 6.4 业务规则检查点

| 触发条件 | 处理方式 |
|----------|----------|
| 涉及金额计算 | 生成业务规则说明，标记需确认 |
| 涉及权限校验 | 生成权限说明，标记需确认 |
| 涉及状态流转 | 生成状态机说明，标记需确认 |
| 涉及第三方交互 | 生成集成说明，标记需确认 |

## 7. 调用方式

### 7.1 命令行调用
```bash
# 基础调用 - 生成新文档
design-api \
  --schema="schema.sql" \
  --ui_elements="ui_elements.json" \
  --api_info='{"apiName":"查询阶段报告详情","httpMethod":"GET","path":"/ai-gxs/plan/stage-report/{reportId}"}' \
  --output="./output" \
  --output_format="markdown"

# 增量更新模式 - 更新现有文档
design-api \
  --schema="schema.sql" \
  --ui_elements="ui_elements.json" \
  --api_info='{"apiName":"查询阶段报告详情","httpMethod":"GET","path":"/ai-gxs/plan/stage-report/{reportId}"}' \
  --output_file="./docs/api-report.md" \
  --output_format="markdown"

# 带截图的调用
design-api \
  --schema="schema.sql" \
  --ui_elements="ui_elements.json" \
  --ui_screenshot="screenshot.png" \
  --api_info='{"apiName":"查询阶段报告详情","httpMethod":"GET","path":"/ai-gxs/plan/stage-report/{reportId}"}' \
  --output="./output"
```

### 7.2 API 调用
```json
POST /api/design-api
Content-Type: application/json

{
  "schema": "CREATE TABLE `stage_report` (...);",
  "ui_elements": {"pages": [...]},
  "ui_screenshot": "base64-encoded-image",
  "api_info": {
    "apiName": "查询阶段报告详情",
    "apiDescription": "根据报告ID查询阶段报告详情信息",
    "httpMethod": "GET",
    "path": "/ai-gxs/plan/stage-report/{reportId}",
    "authType": "Bearer",
    "version": "v1",
    "tags": ["计划管理", "阶段报告"]
  },
  "output_format": "markdown",
  "output_file": "./docs/api-report.md"
}
```

### 7.3 Skill 调用（Cursor/Trae）
```
/design-api --schema="schema.sql" --ui="ui_elements.json" --api-info='{"apiName":"查询阶段报告详情","path":"/api/report/{id}"}' --output="./docs/api.md"
```

## 8. 增量更新机制

### 8.1 更新策略

| 更新类型 | 处理方式 |
|----------|----------|
| **新增接口** | 在文档末尾追加新接口文档 |
| **修改接口** | 替换原有接口文档，保留变更历史 |
| **删除接口** | 标记为 deprecated，保留文档 |

### 8.2 更新流程
1. 读取现有文档
2. 根据接口路径识别是否已存在
3. 如果存在：
   - 对比字段变化
   - 生成变更说明
   - 更新内容，保留历史版本信息
4. 如果不存在：
   - 追加新接口文档

### 8.3 版本历史格式
```markdown
## 七、变更历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.1 | 2024-02-01 | 新增 nextStageFocus 字段 |
| v1 | 2024-01-28 | 初始版本 |
```

## 9. 错误处理

### 9.1 输入验证错误

| 错误类型 | 错误码 | 错误消息 |
|----------|--------|----------|
| 缺少必填参数 | 400 | "缺少必填参数：schema 或 ui_elements" |
| SQL 解析失败 | 400 | "表结构解析失败：{具体错误}" |
| JSON 解析失败 | 400 | "ui_elements JSON 解析失败：{具体错误}" |
| 无效的 HTTP 方法 | 400 | "无效的 HTTP 方法：{method}" |

### 9.2 业务逻辑错误

| 错误类型 | 错误码 | 错误消息 |
|----------|--------|----------|
| 字段映射不完整 | 400 | "UI 字段覆盖率 {rate}%，低于 95% 阈值" |
| 路径参数未定义 | 400 | "路径参数 {param} 未在表结构中定义" |

### 9.3 输出降级策略

当发生非致命错误时：
1. 生成部分结果（可能不完整）
2. 在输出中标记 WARNING
3. 提供人工审查建议

## 10. 扩展点

### 10.1 可扩展组件

| 扩展点 | 说明 | 扩展方式 |
|--------|------|----------|
| **数据库方言** | 支持不同数据库类型 | 新增 Dialect 实现 |
| **输出模板** | 自定义文档格式 | 新增 Template 实现 |
| **Mock 生成器** | 自定义 Mock 规则 | 新增 MockGenerator 实现 |
| **认证方式** | 支持不同认证类型 | 新增 AuthProvider 实现 |

### 10.2 插件机制

```
design-api/
├── core/           # 核心逻辑
├── dialects/       # 数据库方言插件
├── templates/      # 输出模板插件
│   ├── markdown/
│   └── html/
└── generators/     # 生成器插件
    └── mock/
```

## 11. 性能考虑

### 11.1 处理规模
- 支持最大：100 张表 + 500 个字段
- 处理时间：< 20 秒（常规场景）

### 11.2 缓存策略
- 缓存表结构解析结果
- 缓存模板渲染结果

## 12. 安全考虑

| 安全风险 | 应对策略 |
|----------|----------|
| SQL 注入 | 参数化处理，禁止拼接 SQL |
| 敏感信息泄露 | 输出前脱敏处理 |
| 资源耗尽 | 限制输入大小（最大 10MB） |
| 图片安全 | 限制图片大小和格式 |

---

## 附录：输出文件清单

| 文件 | 路径 | 说明 |
|------|------|------|
| 接口文档 | `output/api-document.md` | Markdown 格式的完整接口文档 |
| OpenAPI 规范 | `output/openapi.yaml` | YAML 格式的 OpenAPI 规范 |
| Mock 数据 | `output/mock-data.json` | JSON 格式的模拟数据 |
| 变更清单 | `output/changelog.md` | Markdown 格式的变更说明 |
| UI↔API 映射 | `output/ui-api-mapping.md` | 单独的字段映射表 |