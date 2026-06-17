---
name: java-api-test
displayName: Java接口测试自动化工具
description: 通过扫描Java工程接口，动态生成Python自动化测试脚本，支持交互式授权、全量/增量测试
version: 1.0.0
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

## 架构设计

### 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                    分层架构                                  │
├─────────────────────────────────────────────────────────────┤
│  references/core/     # 核心框架（固定不变）                  │
│    ├── api_scanner.py     # 接口扫描器                       │
│    ├── base_test.py       # 测试基类                         │
│    ├── http_client.py     # HTTP客户端                       │
│    └── report_generator.py # 报告生成器                     │
├─────────────────────────────────────────────────────────────┤
│  references/apis/     # 接口定义（动态生成）                  │
│    ├── [模块名]_api.py     # 接口文件（AI生成）              │
│    └── ...                                                  │
├─────────────────────────────────────────────────────────────┤
│  output/tests/        # 测试用例（动态生成）                  │
│    ├── test_[模块名].py    # 测试文件（AI生成）              │
│    └── ...                                                  │
└─────────────────────────────────────────────────────────────┘
```

### 文件类型标识规范

为了清晰区分文件用途，采用以下标识约定：

| 标识 | 含义 | 示例 |
|------|------|------|
| `# 固定` | 核心框架代码，稳定后无需修改 | `core/base_test.py` |
| `# 可修改` | 配置文件和模板，可按需调整 | `config.yaml`, `templates/test_case.j2` |
| `# 动态生成` | AI生成的代码，运行时创建 | `apis/user_api.py`, `tests/test_user.py` |
| `# 参考用` | 示例代码，供AI参考学习 | `examples/user_api.py` |

## 核心工作流程（Skill驱动）

**Skill作为AI交互入口，驱动整个测试流程**：

| 步骤 | 执行者 | 描述 | 输入输出 |
|------|--------|------|----------|
| 1 | 用户 | 触发Skill | 自然语言指令（如"帮我测试用户接口"） |
| 2 | AI | 理解意图并引导 | 询问所需信息（接口定义、运行模式等） |
| 3 | AI | 生成接口定义 | 写入 `apis/[模块名]_api.py` |
| 4 | AI | 生成测试用例 | 写入 `tests/test_[模块名].py` |
| 5 | AI | 获取运行参数 | 交互式收集Headers、环境配置 |
| 6 | AI | 调用Python执行器 | 执行 `run_tests.py` 并传递参数 |
| 7 | Python | 执行测试脚本 | 运行pytest测试用例 |
| 8 | AI | 解析结果并总结 | 生成报告、展示测试结果 |

### 交互触发词

用户可以通过以下方式触发Skill：

| 触发场景 | 示例指令 |
|----------|----------|
| 扫描接口 | "帮我扫描Java工程的接口"、"分析Controller代码" |
| 生成测试 | "生成用户模块的测试"、"创建订单接口测试" |
| 运行测试 | "运行所有测试"、"测试用户和订单接口" |
| 增量测试 | "检测新增接口并测试"、"只测试新添加的API" |
| 配置授权 | "设置Authorization header"、"配置认证信息" |

### AI对话示例

**场景1：新增接口测试**
```
用户："帮我添加一个商品接口的测试"
AI："请提供接口信息：
     - 模块名：product
     - HTTP方法：POST
     - 端点：/api/products
     - 请求体：{"name": "商品名", "price": 99.9}
     - 预期状态码：201
     是否正确？"
用户："正确"
AI："正在生成 apis/product_api.py 和 tests/test_product.py..."
AI："需要运行测试吗？"
用户："是"
AI："请配置HTTP Headers（按回车跳过）：
     Header: Authorization: Bearer xxx"
用户："Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
AI："正在执行测试...
     ✅ test_create_product - 通过 (0.3s)
     测试完成！"
```

**场景2：全量测试**
```
用户："运行所有测试"
AI："请配置HTTP Headers：
     Header: Authorization: Bearer xxx"
用户："Authorization: Bearer abc123"
AI："找到3个测试文件：test_user.py, test_order.py, test_product.py
     正在执行测试...
     ✅ test_get_users - 通过
     ✅ test_create_user - 通过
     ❌ test_get_order - 失败（状态码404）
     ✅ test_create_product - 通过
     
     📊 测试结果：3通过，1失败
     报告已生成：output/reports/test_report_xxx.html"
```

**场景3：增量测试**
```
用户："检测新增接口并测试"
AI："正在对比代码变更...
     发现1个新增接口文件：apis/payment_api.py
     是否生成测试并执行？"
用户："是"
AI："请输入Authorization token："
用户："xxx"
AI："正在生成测试并执行...
     ✅ test_create_payment - 通过
     ✅ test_get_payment - 通过"
```

## 支持的运行模式

| 模式 | 描述 | 适用场景 |
|------|------|----------|
| 全量运行 | 执行所有测试用例 | 回归测试、发布前验证 |
| 指定接口 | 按模块/名称正则匹配 | 开发调试、单模块验证 |
| 增量运行 | 仅测试新增/修改的接口 | CI流水线、日常开发 |

## Header配置机制

支持灵活的HTTP Header配置，适用于各种认证场景：

| 配置方式 | 说明 | 示例 |
|----------|------|------|
| **命令行参数** | 使用 `--header` 指定，可多次使用 | `--header Authorization "Bearer xxx"` |
| **交互式输入** | 使用 `--prompt-headers` 进入交互模式 | 按提示输入多个key-value对 |
| **环境变量** | `API_HEADERS`（JSON格式） | `API_HEADERS='{"Authorization":"Bearer xxx"}'` |
| **环境变量（单token）** | `API_AUTH_TOKEN`（自动转为Bearer） | `API_AUTH_TOKEN=xxx` |

**优先级**：命令行参数 > 交互式输入 > 环境变量

## 接口扫描支持

### 支持的扫描方式

| 扫描方式 | 描述 | 支持的输入 |
|----------|------|------------|
| **Java源码扫描** | 解析Controller类中的注解 | Java源码目录或单个文件 |
| **Swagger文档扫描** | 解析Swagger/OpenAPI规范 | JSON/YAML文件或URL |

### 扫描能力

**Java源码扫描**：
- 支持 `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping` 注解
- 支持 `@RequestMapping` 注解（自动识别method属性）
- 自动提取Controller类名作为模块名
- 自动识别类级别和方法级别的路径拼接

**Swagger文档扫描**：
- 支持 Swagger V2 (`swagger: "2.0"`)
- 支持 OpenAPI V3 (`openapi: "3.x.x"`)
- 支持本地文件和远程URL
- 支持JSON和YAML格式
- 自动按tags分组

### 变更检测能力

扫描时支持检测接口的变化类型：

| 变更类型 | 描述 | 检测方式 |
|----------|------|----------|
| **新增** | 新增的接口 | 对比历史快照，检测新增的method+endpoint组合 |
| **删除** | 删除的接口 | 对比历史快照，检测消失的method+endpoint组合 |
| **修改** | 修改的接口 | 通过哈希值对比接口定义内容 |
| **未变化** | 未变化的接口 | 哈希值一致的接口 |

**变更检测流程**：
1. 扫描当前接口定义
2. 加载历史快照（最近一次保存的快照）
3. 对比接口变化
4. 可选：保存当前扫描结果为新快照

### AI对话示例（扫描接口）

```
用户："帮我扫描Java工程的接口"
AI："请提供Java源码目录路径："
用户："/path/to/java/project/src/main/java"
AI："正在扫描...
     发现3个Controller文件：
     - UserController.java → user模块（5个接口）
     - OrderController.java → order模块（4个接口）
     - ProductController.java → product模块（3个接口）
     共12个接口，是否需要生成测试脚本？"
用户："是，生成user和order模块的测试"
AI："正在生成测试脚本..."
```

```
用户："从Swagger文档生成测试"
AI："请提供Swagger文档路径或URL："
用户："http://localhost:8080/api/swagger.json"
AI："正在解析Swagger文档...
     发现5个模块，共20个接口
     是否需要全部生成测试？"
用户："只生成payment模块"
AI："正在生成 apis/payment_api.py 和 tests/test_payment.py..."
```

**场景3：检测接口变更**
```
用户："检测接口变更"
AI："请提供扫描路径："
用户："/path/to/java/source"
AI："正在扫描并检测变更...
     
     📊 变更摘要：
     ├── 总接口数：15
     ├── 新增接口：2
     ├── 删除接口：1
     ├── 修改接口：3
     └── 未变化：9
     
     ✅ 新增：
     - POST /api/payments
     - GET /api/payments/{id}
     
     ❌ 删除：
     - DELETE /api/users/{id}
     
     🔄 修改：
     - PUT /api/users/{id}（请求体变更）
     
     是否需要为新增接口生成测试？"
用户："是"
AI："正在生成测试脚本..."
```

## 目录结构

```
java-api-test-skill/
├── SKILL.md                 # 技能描述文档（固定）
├── examples/                # 演示示例项目（参考用）
│   └── example1/            # 完整演示流程（参考用）
│       ├── mock_server.py
│       ├── run_example.py
│       └── output/          # 演示输出（参考用）
└── references/              # 核心框架代码（固定不变）
    └── core/                # 核心工具（固定不变）
        ├── api_scanner.py   # 接口扫描器（固定）
        ├── base_test.py     # 测试基类（固定）
        ├── http_client.py   # HTTP客户端（固定）
        ├── report_generator.py  # 报告生成器（固定）
        ├── run_tests.py     # 测试执行器（固定）
        └── skill_driver.py  # Skill驱动接口（固定）
    └── templates/           # 模板文件（可修改）
        ├── config.yaml      # 配置模板（可修改）
        ├── test_case.j2     # 测试用例Jinja2模板
        └── apis/            # 接口定义参考模板
            ├── user_api.py  # 用户模块接口模板
            └── order_api.py # 订单模块接口模板
```

> **注意**：`apis/`（接口定义目录）和 `output/tests/`（测试用例目录）会在AI生成时自动创建。

### 文件类型说明

| 文件类型 | 标识 | 说明 | 更新频率 |
|----------|------|------|----------|
| **固定代码** | `# 固定` | 核心框架，稳定后无需修改 | 极少 |
| **模板文件** | `# 可修改` | Jinja2模板和参考模板，定义生成格式 | 按需调整 |
| **动态生成** | `# 动态生成` | AI生成的接口定义和测试用例 | 运行时生成 |
| **演示示例** | `# 参考用` | 完整演示项目，展示使用流程 | 参考用 |

### Skill驱动接口

**skill_driver.py** 是AI与Python脚本之间的桥梁，提供以下命令：

| 命令 | 说明 | 示例 |
|------|------|------|
| `scan` | 扫描接口 | `python skill_driver.py scan --type java --path /path/to/java/source` |
| `gen-api` | 生成接口定义文件 | `python skill_driver.py gen-api --module user --base-path /api/users --endpoints '[{"method":"GET","name":"list"}]'` |
| `gen-test` | 生成测试用例文件 | `python skill_driver.py gen-test --module user --test-cases '[{"name":"get_users","method":"GET"}]'` |
| `run` | 运行测试 | `python skill_driver.py run --include "user" --headers '{"Authorization":"Bearer xxx"}'` |
| `list` | 列出模块 | `python skill_driver.py list --type api` |

**scan命令参数**：
- `--type`：扫描类型（`java` 或 `swagger`）
- `--path`：扫描路径（目录、文件或URL）
- `--group`：是否按模块分组（默认True）

**AI调用流程**：
1. AI解析用户自然语言指令
2. AI调用 `skill_driver.py scan` 扫描接口
3. AI调用 `skill_driver.py gen-api` 生成接口定义
4. AI调用 `skill_driver.py gen-test` 生成测试用例
5. AI调用 `skill_driver.py run` 执行测试
6. AI解析返回结果并展示给用户

## 输入规范

### 接口定义格式（apis/目录下的文件）

```python
# apis/[模块名]_api.py - # 动态生成
from core.http_client import HttpClient

class [模块名]Api:
    BASE_PATH = "/api/[模块名]"
    
    @classmethod
    def get_[接口名](cls, client: HttpClient, params=None):
        return client.get(f"{cls.BASE_PATH}", params=params)
    
    @classmethod
    def create_[接口名](cls, client: HttpClient, data):
        return client.post(f"{cls.BASE_PATH}", json=data)
```

**示例参考**：`references/templates/apis/user_api.py`（# 模板）

### 测试用例格式（output/tests/目录下的文件）

```python
# output/tests/test_[模块名].py - # 动态生成
from core.base_test import BaseTest
from apis.[模块名]_api import [模块名]Api

class Test[模块名]Api(BaseTest):
    
    def test_get_[接口名](self):
        """测试获取[接口描述]"""
        response = [模块名]Api.get_[接口名](self.client)
        self.assert_status_ok(response)
    
    def test_create_[接口名](self):
        """测试创建[接口描述]"""
        payload = {...}
        response = [模块名]Api.create_[接口名](self.client, payload)
        self.assert_status_created(response)
```

## 输出规范

### 测试报告

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "total_tests": 15,
  "passed": 14,
  "failed": 1,
  "skipped": 0,
  "results": [
    {"test_name": "test_get_users", "status": "passed", "duration": 0.5},
    {"test_name": "test_create_user", "status": "failed", "error": "AssertionError"}
  ],
  "report_path": "./output/reports/test_report_20240115_1030.html"
}
```

## 调用方式

### 全量运行
```bash
python run_tests.py --all
```

### 指定接口运行
```bash
python run_tests.py --include "user"
python run_tests.py --include "user|order"
```

### 增量运行
```bash
python run_tests.py --incremental
```

### 指定自定义Headers
```bash
# 指定单个header
python run_tests.py --all --header Authorization "Bearer xxx"

# 指定多个headers
python run_tests.py --all \
  --header Authorization "Bearer xxx" \
  --header X-Client-ID "my-client" \
  --header X-Tenant-ID "tenant-001"

# 交互式输入headers
python run_tests.py --all --prompt-headers
```

## 配置机制

### 配置优先级（从高到低）

1. **命令行参数**：通过 `--base-url`, `--header` 等参数传入
2. **环境变量**：`API_BASE_URL`, `API_HEADERS`, `API_TIMEOUT`
3. **工作目录配置**：在项目目录创建 `api_test_config.yaml`
4. **Skill默认配置**：`references/config.yaml`

### 使用方式

#### 方式1：初始化项目（推荐）

```bash
# 进入你的项目目录
cd /path/to/your/java/project

# 使用Skill初始化项目（自动生成配置文件和目录结构）
python /path/to/java-api-test-skill/references/core/skill_driver.py init

# 修改配置文件
vim api_test_config.yaml

# 使用Skill运行测试
python /path/to/java-api-test-skill/references/core/skill_driver.py run --all
```

**初始化后生成的文件结构**：

```
your-project/
├── api_test_config.yaml  # 配置文件（请修改为你的环境）
├── apis/                # 接口定义目录（AI生成）
│   └── __init__.py
└── output/
    ├── tests/           # 测试用例目录（AI生成）
    └── reports/         # 测试报告目录（运行时生成）
```

#### 方式2：使用环境变量

```bash
export API_BASE_URL=http://your-api-server:8080
export API_HEADERS='{"Authorization":"Bearer xxx"}'

python /path/to/java-api-test-skill/references/core/skill_driver.py run --all
```

#### 方式3：使用命令行参数

```bash
python /path/to/java-api-test-skill/references/core/skill_driver.py run \
  --all \
  --base-url http://your-api-server:8080 \
  --header Authorization "Bearer xxx"
```

### 配置文件格式 (api_test_config.yaml)

```yaml
api:
  base_url: http://localhost:8080
  timeout: 30
  default_headers:
    Content-Type: application/json
    Accept: application/json

test:
  output_dir: ./output/reports
  report_format: html

incremental:
  enabled: true
  git_path: ./
  base_branch: main
```

## 扩展机制

### 新增接口模块
1. 在 `apis/` 目录下创建新文件：`[模块名]_api.py`
2. 在 `tests/` 目录下创建对应测试文件：`test_[模块名].py`
3. 运行测试时自动识别并执行

### 自定义断言
在 `core/base_test.py` 中添加自定义断言方法，所有测试类自动继承

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2024-01-15 | 初始版本，支持分层架构、交互式授权、增量测试 |
