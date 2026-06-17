---
name: java-api-test
displayName: Java接口测试自动化工具
description: 通过扫描Java工程接口，动态生成Python自动化测试脚本，支持交互式授权、全量/增量测试，AI智能分析数据类型并构建前置依赖链
version: 1.2.0
author: Deric Huang
category: 测试工具
tags: ["接口测试", "自动化测试", "API测试", "Java"]
---

# java-api-test Skill

## 概述

基于AI驱动的Java接口测试自动化工具，采用**分层架构设计**：
- **核心框架**：稳定的测试执行引擎，无需频繁修改
- **接口定义**：独立的接口描述文件，便于增量更新
- **测试用例**：可动态生成的测试脚本，支持快速扩展

核心能力：
1. **接口扫描**：支持Java源码和Swagger文档扫描，提取字段类型定义和响应结构
2. **AI智能分析**：根据接口数据类型自动构建符合规范的请求体，识别接口间的依赖关系
3. **前置依赖链**：自动生成资源创建→查询→更新→删除的完整测试链路

## 架构设计

### 分层架构

```
┌─────────────────────────────────────────────────────┐
│                    分层架构                          │
├─────────────────────────────────────────────────────┤
│  references/core/     # 核心框架（固定不变）          │
│    ├── api_scanner.py     # 接口扫描器               │
│    ├── base_test.py       # 测试基类                 │
│    ├── http_client.py     # HTTP客户端               │
│    └── report_generator.py # 报告生成器             │
├─────────────────────────────────────────────────────┤
│  apis/                # 接口定义（动态生成）          │
│    └── [模块名]_api.py     # 接口文件（AI生成）      │
├─────────────────────────────────────────────────────┤
│  output/tests/        # 测试用例（动态生成）          │
│    └── test_[模块名].py    # 测试文件（AI生成）      │
└─────────────────────────────────────────────────────┘
```

### 文件类型标识规范

| 标识 | 含义 | 示例 |
|------|------|------|
| `# 固定` | 核心框架代码，稳定后无需修改 | `core/base_test.py` |
| `# 可修改` | 配置文件和模板，可按需调整 | `config.yaml` |
| `# 动态生成` | AI生成的代码，运行时创建 | `apis/user_api.py` |
| `# 参考用` | 示例代码，供AI参考学习 | `examples/mock_server.py` |

## 核心工作流程

**Skill作为AI交互入口，驱动整个测试流程**：

| 步骤 | 执行者 | 描述 |
|------|--------|------|
| 1 | 用户 | 触发Skill |
| 2 | AI | 理解意图并引导 |
| 3 | AI | 生成接口定义 |
| 4 | AI | 生成测试用例 |
| 5 | AI | 获取运行参数 |
| 6 | AI | 调用Python执行器 |
| 7 | Python | 执行测试脚本 |
| 8 | AI | 解析结果并总结 |

### AI智能分析能力

AI在生成测试用例时，会自动完成以下分析：

**1. 数据类型分析**（从scan结果中提取）
- 解析字段名、类型、格式（如email/password/date）
- 按类型生成符合规范的示例值（string/int/boolean等）
- 识别必填字段和可选字段

**2. 前置依赖分析**（接口关系推理）
- POST 201创建资源 → 自动标记为"资源提供者"
- 含路径参数 `{id}` 的接口 → 自动关联到创建测试
- 生成 skipTest 安全回退机制

**AI交互示例**：
```
用户："扫描UserController并生成测试"
AI：扫描到:
    POST /api/users (字段: username:string, email:email, password:password, age:int)
    GET  /api/users
    GET  /api/users/{id}
    PUT  /api/users/{id}  
    DELETE /api/users/{id}
    
    AI分析：POST创建用户是前置依赖，后续GET/PUT/DELETE需要用户ID
    是否生成带完整依赖链的测试用例？
```

### 交互触发词

| 触发场景 | 示例指令 |
|----------|----------|
| 扫描接口 | "扫描Java工程接口"、"分析Controller代码" |
| 生成测试 | "生成用户模块测试"、"创建订单接口测试" |
| 运行测试 | "运行所有测试"、"测试用户接口" |
| 增量测试 | "检测新增接口并测试"、"只测试新API" |
| 配置授权 | "设置Authorization header" |

## 支持的运行模式

| 模式 | 描述 | 适用场景 |
|------|------|----------|
| 全量运行 | 执行所有测试用例 | 回归测试、发布前验证 |
| 指定接口 | 按模块/名称正则匹配 | 开发调试、单模块验证 |
| 增量运行 | 仅测试新增/修改的接口 | CI流水线、日常开发 |

## Header配置机制

支持灵活的HTTP Header配置：

| 配置方式 | 说明 | 示例 |
|----------|------|------|
| 命令行参数 | `--header` 指定 | `--header Authorization "Bearer xxx"` |
| 交互式输入 | `--prompt-headers` | 按提示输入key-value对 |
| 环境变量 | `API_HEADERS`（JSON） | `API_HEADERS='{"Authorization":"Bearer xxx"}'` |

**优先级**：命令行参数 > 交互式输入 > 环境变量

## 接口扫描支持

### 扫描方式

| 扫描方式 | 描述 | 支持输入 | 提取信息 |
|----------|------|----------|----------|
| Java源码扫描 | 解析Controller注解 | Java源码目录或文件 | 方法+路径+模块 |
| Swagger文档扫描 | 解析Swagger/OpenAPI规范 | JSON/YAML文件或URL | 方法+路径+模块+**字段类型**+响应结构 |

### 变更检测能力

| 变更类型 | 描述 |
|----------|------|
| 新增 | 新增的接口 |
| 删除 | 删除的接口 |
| 修改 | 修改的接口 |
| 未变化 | 未变化的接口 |

## 目录结构

```
java-api-test-skill/
├── SKILL.md                 # 技能描述文档
├── examples/                # 演示示例项目
│   └── example1/            # 完整演示流程
└── references/              # 核心框架代码
    ├── core/                # 核心工具
    │   ├── api_scanner.py   # 接口扫描器
    │   ├── base_test.py     # 测试基类
    │   ├── http_client.py   # HTTP客户端
    │   ├── report_generator.py  # 报告生成器
    │   ├── run_tests.py     # 测试执行器
    │   └── skill_driver.py  # Skill驱动接口
    └── templates/           # 模板文件
        ├── config.yaml      # 配置模板
        ├── test_case.j2     # 测试用例模板
        └── apis/            # 接口定义模板
```

### Skill驱动接口

**skill_driver.py** 提供以下命令：

| 命令 | 说明 | 示例 |
|------|------|------|
| `scan` | 扫描接口 | `scan --type swagger --path /path/to/swagger.json` |
| `gen-api` | 生成接口定义 | `gen-api --module user --base-path /api/users` |
| `gen-test` | 生成测试用例 | `gen-test --module user --base-path /api/users --test-cases '[...]'` |
| `run` | 运行测试 | `run --include "user" --headers '{"Authorization":"Bearer xxx"}'` |
| `list` | 列出模块 | `list --type api` |

## 输入输出规范

### 接口定义格式

```python
# apis/[模块名]_api.py
from core.http_client import HttpClient

class [模块名]Api:
    BASE_PATH = "/api/[模块名]"
    
    @classmethod
    def get_[接口名](cls, client: HttpClient, params=None):
        return client.get(f"{cls.BASE_PATH}", params=params)
```

### 测试用例格式（AI生成-数据类型感知）

```python
# output/tests/test_[模块名].py
from core.base_test import BaseTest
from apis.[模块名]_api import [模块名]Api

class Test[模块名]Api(BaseTest):
    # AI自动分析出的类变量：用于前置依赖链
    _created_resource_id = None

    def test_create(self):
        """测试创建资源"""
        # AI根据接口字段类型自动生成的payload
        payload = {
            "username": "test_username",
            "email": "test@example.com",
            "password": "Password123!"
        }
        response = [模块名]Api.post_create(self.client, payload)
        self.assert_status_created(response)
        data = response.json()
        # 存储ID供后续测试依赖
        self.__class__._created_resource_id = data.get("id")

    def test_get_by_id(self):
        """测试获取单个资源 - 前置: create"""
        if not self.__class__._created_resource_id:
            self.skipTest("请先执行前置测试: create")
        response = [模块名]Api.get_by_id(self.client, self.__class__._created_resource_id)
        self.assert_status_ok(response)
```

### 测试报告输出

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "total_tests": 15,
  "passed": 14,
  "failed": 1,
  "skipped": 0,
  "report_path": "./output/reports/test_report_xxx.html"
}
```

## 调用方式

### 全量运行
```bash
python skill_driver.py run --all
```

### 指定接口运行
```bash
python skill_driver.py run --include "user|order"
```

### 增量运行
```bash
python skill_driver.py run --incremental
```

### 指定自定义Headers
```bash
python skill_driver.py run --all \
  --header Authorization "Bearer xxx" \
  --header X-Client-ID "my-client"
```

## 配置机制

### 配置优先级（从高到低）
1. 命令行参数
2. 环境变量（`API_BASE_URL`, `API_HEADERS`, `API_TIMEOUT`）
3. 工作目录配置（`api_test_config.yaml`）
4. Skill默认配置（`references/config.yaml`）

### 初始化项目（推荐）
```bash
cd /path/to/your/project
python /path/to/java-api-test-skill/references/core/skill_driver.py init
python /path/to/java-api-test-skill/references/core/skill_driver.py run --all
```

### 配置文件格式

```yaml
api:
  base_url: http://localhost:8080
  timeout: 30
  default_headers:
    Content-Type: application/json

test:
  output_dir: ./output/reports
  report_format: html
```

## 安全限制

为保障系统安全，本Skill实现了以下安全限制：

### 文件系统安全
- **路径边界检查**：仅允许扫描**当前工作目录**范围内的文件，禁止访问上级目录或系统敏感目录
- **敏感目录禁止**：禁止扫描包含 `.ssh`、`.git`、`/etc/`、`/root/`、`password`、`secret` 等敏感模式的路径
- **工作目录隔离**：所有扫描操作都被限制在用户触发Skill时所在的工作目录内

### 网络安全
- **禁止访问云元数据**：禁止访问 `metadata`、`169.254.` 等云平台敏感地址
- **HTTPS强制**：非本地服务必须使用HTTPS协议，禁止HTTP明文传输
- **禁止模式**：禁止访问 `aws`、`alibaba`、`tencent`、`kubernetes` 等敏感关键词域名
- **动态配置允许域名**：通过环境变量 `API_ALLOWED_DOMAINS=domain1,domain2` 配置额外允许的域名
- **用户确认**：执行网络请求前，AI会展示目标URL和Headers，需要用户确认后才执行

### 配置示例

```bash
# 允许企业内部域名
export API_ALLOWED_DOMAINS="company.com,intranet.example.com"
python skill_driver.py run --all
```

### 权限模型
- 本Skill只读取用户指定范围内的Java源码和Swagger文档
- 只向用户指定的API端点发送测试请求
- 所有文件操作和网络请求都由用户明确授权后执行

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.2.0 | 2024-06-17 | 安全加固：文件路径边界检查 + 网络域名白名单验证 |
| 1.1.0 | 2024-06-17 | 新增AI智能数据类型分析和前置依赖链生成 |
| 1.0.0 | 2024-01-15 | 初始版本，支持分层架构、交互式授权、增量测试 |