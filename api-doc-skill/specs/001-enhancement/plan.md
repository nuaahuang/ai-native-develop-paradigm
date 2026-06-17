# 实现计划：api-doc-skill 增强优化

## 架构设计

### 整体架构

保持原设计的插件化解析器架构，扩展为更清晰的分层：

```
api-doc-skill/
├── SKILL.md                          # Skill 定义
├── scripts/
│   ├── __init__.py
│   ├── skill_driver.py               # 主入口，处理命令参数
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── base_parser.py            # 基类，定义统一接口
│   │   ├── java_parser.py            # Java Spring
│   │   ├── fastapi_parser.py         # Python FastAPI
│   │   ├── flask_parser.py           # Python Flask（新增）
│   │   ├── django_parser.py          # Django REST Framework（新增）
│   │   ├── express_parser.py         # Express
│   │   ├── go_parser.py              # Go Gin
│   │   ├── graphql_parser.py         # GraphQL（新增）
│   │   ├── grpc_parser.py            # gRPC protobuf（新增）
│   │   └── plain_parser.py           # 纯文本
│   ├── models/
│   │   ├── __init__.py
│   │   ├── api_info.py               # API 信息数据模型
│   │   ├── parameter.py              # 参数定义
│   │   ├── response.py               # 响应定义
│   │   └── version_info.py           # 版本信息（新增）
│   ├── document/
│   │   ├── __init__.py
│   │   ├── markdown_parser.py        # 解析现有 Markdown 文档
│   │   ├── markdown_generator.py     # 生成 Markdown 文档
│   │   ├── version_manager.py        # 版本管理器（新增）
│   │   └── change_detector.py        # 变更检测（新增）
│   ├── exporters/
│   │   ├── __init__.py
│   │   ├── openapi_exporter.py       # OpenAPI 3.0 导出（新增）
│   │   └── swagger_exporter.py       # Swagger 2.0 导出（新增）
│   ├── batch/
│   │   ├── __init__.py
│   │   ├── scanner.py               # 项目目录扫描器（新增）
│   │   └── batch_processor.py        # 批量处理器（新增）
│   ├── images/
│   │   ├── __init__.py
│   │   ├── image_handler.py          # 图片处理（重构增强）
│   │   ├── validator.py              # 图片验证（新增）
│   │   ├── compressor.py             # 图片压缩（新增）
│   │   └── uploaders/
│   │       ├── __init__.py
│   │       ├── base_uploader.py
│   │       ├── qiniu_uploader.py
│   │       ├── oss_uploader.py
│   │       └── wecom_uploader.py
│   ├── examples/
│   │   ├── __init__.py
│   │   └── example_generator.py      # 测试示例生成（新增）
│   ├── validation/
│   │   ├── __init__.py
│   │   └── input_validator.py         # 输入验证（新增）
│   ├── config.py                     # 配置管理
│   └── utils.py                      # 工具函数
├── templates/
│   ├── markdown_interface.j2         # Markdown 接口模板
│   ├── markdown_document.j2          # Markdown 文档模板
│   └── version_comparison.j2         # 版本对比模板（新增）
└── specs/
    └── 001-enhancement/
        ├── spec.md                   # 需求规格（本文件）
        ├── plan.md                   # 实现计划
        └── tasks.md                  # 任务列表
```

## 核心模块设计

### 1. 数据模型增强

**文件：** `scripts/models/`

新增 `version_info.py`：

```python
@dataclass
class VersionInfo:
    version: str              # 版本号，如 "v1"
    created_at: datetime      # 创建时间
    updated_at: datetime      # 更新时间
    change_log: str           # 变更说明
    interfaces: List[str]     # 接口路径列表
```

增强 `api_info.py`：

```python
@dataclass
class ApiInfo:
    # 原有字段...
    version: Optional[str]         # 版本号
    change_history: List[Change]   # 变更历史
    examples: Dict[str, str]       # 测试示例（curl, python, javascript）
```

### 2. 新增解析器

#### Django REST Framework 解析器 (`django_parser.py`)

- 解析 `@api_view` 装饰器
- 解析 `@action` 装饰器
- 解析 `ViewSet` 类中的路由定义
- 解析序列化器作为请求/响应模型

#### Flask 解析器 (`flask_parser.py`)

- 解析 `@app.route` 装饰器
- 解析 `@blueprint.route` 装饰器
- 解析函数参数类型提示
- 解析方法文档字符串

#### GraphQL 解析器 (`graphql_parser.py`)

- 解析 `type Query` 定义
- 解析 `type Mutation` 定义
- 提取字段名、参数、类型
- 生成对应 HTTP 端点信息

#### gRPC 解析器 (`grpc_parser.py`)

- 解析 `.proto` 文件
- 提取 service 定义
- 提取 method 输入输出类型
- 映射为 HTTP 接口（适配 grpc-gateway）

### 3. 批量扫描模块

**文件：** `scripts/batch/scanner.py`

核心功能：

- 遍历指定目录，按扩展名过滤文件
- 默认排除规则：`node_modules/`, `venv/`, `.git/`, `__pycache__/`, `tests/` 等
- 可通过配置文件自定义排除规则
- 对每个文件，自动识别框架类型并调用对应解析器
- 收集所有解析出的接口信息

**新增命令参数：**
- `--scan-dir <path>` - 批量扫描模式
- `--exclude <pattern>` - 添加额外排除模式

### 4. 版本管理模块

**文件：** `scripts/document/version_manager.py`

核心功能：

- 按版本分组存储接口
- 生成版本分区的文档结构
- 记录每个接口的变更历史
- 对比不同版本找出差异（新增、删除、参数变更）
- 生成版本变更对比报告

**Markdown 文档结构增强：**

```markdown
# 接口文档

## 目录

### v1
1. [v1-获取用户信息](#v1-接口获取用户信息)
2. [v1-创建用户](#v1-接口创建用户)

### v2
1. [v2-获取用户信息](#v2-接口获取用户信息)
2. [v2-创建用户](#v2-接口创建用户)

---

## v1 版本

---

## v1-1-接口：获取用户信息
...
```

### 5. OpenAPI 导出模块

**文件：** `scripts/exporters/openapi_exporter.py`

映射关系：

- `ApiInfo` → `paths` 路径项
- `Parameter` → `parameters` + `requestBody`
- `ResponseInfo` → `responses`
- 版本信息 → `info.version`

支持输出：
- JSON 格式
- YAML 格式

**新增命令参数：**
- `--export-openapi <file>` - 导出 OpenAPI 到指定文件

### 6. 输入验证模块

**文件：** `scripts/validation/input_validator.py`

验证内容：

1. 代码非空检查
2. 是否识别出框架类型
3. 是否找到接口定义
4. 解析出的信息完整性检查

错误分类：

```python
class ValidationError:
    code: ErrorCode
    message: str
    suggestion: Optional[str]  # 修复建议
```

返回友好的错误信息，帮助用户定位问题。

### 7. 测试示例生成模块

**文件：** `scripts/examples/example_generator.py`

为每个接口生成：

1. **curl 示例** - 可直接复制执行的 curl 命令
2. **Python requests 示例** - Python 代码调用示例
3. **JavaScript fetch 示例** - 浏览器/Node.js 调用示例
4. **测试用例建议** - 列出常见的测试场景

### 8. 图片处理增强

重构 `scripts/images/image_handler.py`：

新增 `scripts/images/validator.py`：
- 验证图片文件是否存在
- 验证图片格式是否正确
- 验证图片完整性

新增 `scripts/images/compressor.py`：
- 可选择性压缩图片大小
- 保持可接受的画质

增强云上传：
- 每个云存储提供商独立实现
- 统一的 `BaseUploader` 接口
- 上传失败清晰错误提示

## 实现步骤

### 阶段一：基础设施增强

1. 创建数据模型（版本、变更历史）
2. 重构目录结构，新建模块目录
3. 创建配置管理模块
4. 输入验证框架

### 阶段二：新增解析器

5. Django REST Framework 解析器
6. Flask 解析器
7. GraphQL 解析器
8. gRPC protobuf 解析器
9. 改进现有解析器容错性

### 阶段三：批量生成功能

10. 目录扫描器
11. 批量处理器
12. 完整文档重生成逻辑

### 阶段四：版本管理

13. 版本管理器
14. 变更检测
15. 版本对比输出

### 阶段五：OpenAPI 导出

16. OpenAPI 3.0 导出
17. Swagger 2.0 导出

### 阶段六：示例与文档增强

18. 测试示例生成
19. 图片处理增强（验证、压缩）

## 依赖项

需要新增的 Python 依赖：

```
pyyaml                          - YAML 输出支持
python-graphql-core             - GraphQL 解析（可选）
protobuf                       - gRPC 解析
Pillow                         - 图片处理压缩
```

## 向后兼容性

- 现有的 Markdown 文档格式保持兼容
- 没有版本信息的接口默认归为 `v1`
- 无版本的文档可以通过一次完整重生成添加版本分组
- 原有命令参数保持有效

## 风险与应对

| 风险 | 应对 |
|------|------|
| 不同框架写法变化多样 | 优先支持通用常用写法，对特殊写法保留扩展性 |
| AST 解析复杂度高 | 先基于正则解析，对于复杂情况再考虑 AST 提升准确性 |
| 批量扫描性能问题 | 异步遍历文件，增量缓存已解析文件 |
| OpenAPI 规范复杂 | 先支持核心功能，扩展字段后续迭代 |
