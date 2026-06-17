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

| 扫描方式 | 描述 | 支持输入 |
|----------|------|----------|
| Java源码扫描 | 解析Controller注解 | Java源码目录或文件 |
| Swagger文档扫描 | 解析Swagger/OpenAPI规范 | JSON/YAML文件或URL |

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
| `scan` | 扫描接口 | `scan --type java --path /path/to/java` |
| `gen-api` | 生成接口定义 | `gen-api --module user --base-path /api/users` |
| `gen-test` | 生成测试用例 | `gen-test --module user --test-cases '[{"name":"get_users"}]'` |
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

### 测试用例格式

```python
# output/tests/test_[模块名].py
from core.base_test import BaseTest
from apis.[模块名]_api import [模块名]Api

class Test[模块名]Api(BaseTest):
    def test_get_[接口名](self):
        response = [模块名]Api.get_[接口名](self.client)
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

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2024-01-15 | 初始版本，支持分层架构、交互式授权、增量测试 |