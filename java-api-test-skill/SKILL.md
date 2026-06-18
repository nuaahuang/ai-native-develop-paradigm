---
name: java-api-test
displayName: Java接口测试脚本生成工具
description: 通过扫描Java工程接口，AI自动分析依赖关系编排数据流测试链，上游接口响应数据自动传递给下游接口。动态生成Python自动化测试脚本和测试用例代码。采用分层架构设计，核心框架稳定不变，接口定义和测试用例可动态生成。适用于Java后端项目的接口自动化测试脚本生成。
version: 2.0.0
author: Deric Huang
category: 测试工具
tags: ["接口测试", "自动化测试", "API测试", "Java", "测试生成"]
---

# java-api-test Skill

## 概述

基于AI驱动的Java接口测试自动化工具，采用**分层架构设计**：
- **核心框架**：`scripts/`，稳定不变，包含扫描器、HTTP客户端、测试执行器、报告生成器
- **接口定义**：`apis/`，动态生成，每个模块一个文件，便于增量更新
- **测试用例**：`output/tests/`，动态生成，AI根据依赖关系自动编排测试链

核心能力：
1. **接口扫描**：Java源码扫描(`src/`)和Swagger文档扫描(`swagger/`)，提取字段类型定义和响应结构
2. **AI智能分析**：根据接口数据类型自动构建符合规范的请求体，识别接口间依赖关系
3. **前置依赖链**：**自动编排数据流测试链**，上游接口响应数据自动传递给下游接口

**核心亮点**：AI自动分析接口依赖关系，生成完整数据流测试链 → `POST 创建资源 → GET 查询详情 → PUT 更新 → DELETE 删除`，上游接口的响应数据自动传递给下游接口，测试脚本更贴近真实调用场景

## 核心架构

### 分层结构（本地项目运行时）

```
{your-project}/
├── output/
│   ├── apis/               # 动态生成：接口定义文件 (# 动态生成)
│   │   └── user_api.py
│   ├── tests/              # 动态生成：测试用例文件 (# 动态生成)
│   │   └── test_user.py
│   ├── scripts/            # 动态生成：测试执行脚本 (# 动态生成)
│   │   └── report_generator.py
│   ├── run_tests.py        # 动态生成：完整测试执行器
│   └── run_api_tests.py    # 动态生成：简化测试运行器
└── api_test_config.yaml     # 配置文件 (# 可修改)

java-api-test-skill/
├── SKILL.md              # 技能说明
├── scripts/             # 可执行脚本
│   ├── __init__.py
│   ├── api_scanner.py     # 接口扫描器（含安全检查）
│   ├── base_test.py       # 测试基类（断言工具）
│   ├── http_client.py     # HTTP客户端（含域名安全验证）
│   └── skill_driver.py  # Skill驱动入口（命令路由）
└── references/           # 参考文档和模板
    └── templates/
        ├── config.yaml      # 配置模板
        └── test_case.j2     # 测试用例模板
```

### 文件类型说明

| 标识 | 位置 | 说明 |
|------|------|------|
| **固定** | `scripts/` | 核心可执行脚本，稳定后无需修改 |
| **可修改** | `{your-project}/api_test_config.yaml` | 用户配置文件，可按需调整 |
| **动态生成** | `{your-project}/output/apis/` `{your-project}/output/tests/` | AI生成的接口定义和测试用例 |
| **可生成** | `{your-project}/output/run_tests.py` `{your-project}/output/run_api_tests.py` | 测试执行脚本（用户可自行执行） |
| **模板** | `references/templates/` | 代码生成模板 |

## 核心工作流程（AI Skill驱动）

| 步骤 | AI角色 | Python执行 |
|------|---------|----------|
| 1 | 用户触发Skill | - |
| 2 | AI理解意图，引导用户输入扫描路径 | - |
| 3 | AI调用 `skill_driver.py scan` | 扫描接口，提取字段类型+响应结构 |
| 4 | AI智能分析：识别数据类型+依赖关系 | - |
| 5 | AI展示分析结果，确认测试范围 | 用户确认 |
| 6 | AI调用 `skill_driver.py gen-api` | 生成 `apis/{module}_api.py` |
| 7 | AI调用 `skill_driver.py gen-test` | 生成 `output/tests/test_{module}.py`（带依赖链） |
| 8 | AI调用 `skill_driver.py gen-exec` | 生成测试执行脚本（用户可自行执行） |
| 9 | AI总结结果，展示生成的文件和使用方式 | - |

## AI智能分析能力

**1. 数据类型感知**（从扫描结果提取）
- 根据 `type`/`format` 生成符合规范的示例值
  - `string` → `"test_field"`
  - `string + email` → `"test@example.com"`
  - `string + password` → `"Password123!"`
  - `integer` → 随机整数
  - `boolean` → `true`

**2. 依赖链自动编排**（数据流传递）
- 对每个接口提取输入需求：路径参数/查询参数/请求体中的 `xxx_id`
- 对每个接口提取输出供给：响应字段列表（POST 201自动添加 `id`）
- 交叉匹配：**输入需求 ← 上游输出供给**，只向前匹配防循环
- 生成 skipTest 安全回退：前置未执行则自动跳过



## 安全限制

### 文件系统安全
- **路径边界检查**：必须在当前工作目录范围内，禁止访问上级目录或系统敏感目录
- **目录白名单**：仅允许扫描 `src/`、`src/main/`、`swagger/`、`api/`、`controller/`、`controllers/` 等源码和文档目录
- **文件扩展名限制**：单个文件仅允许 `.java`、`.json`、`.yml`、`.yaml`、`.swagger`
- **敏感目录禁止**：禁止扫描包含 `.ssh`、`.git`、`/etc/`、`/root/`、`password`、`secret` 等敏感模式的路径
- **工作目录隔离**：所有扫描操作都被限制在用户触发Skill时所在的工作目录内

### 权限模型
- 本Skill只读取用户指定范围内的Java源码和Swagger文档
- 所有文件操作都由用户明确授权后执行

## 驱动命令（scripts/skill_driver.py）

| 命令 | 参数 | 说明 |
|------|------|------|
| `init` | - | 初始化项目，生成配置文件和目录 |
| `scan` | `--type java/swagger` `--path PATH` | 扫描接口，输出JSON |
| `gen-api` | `--module NAME` `--base-path PATH` `--endpoints JSON` | 生成接口定义文件 |
| `gen-test` | `--module NAME` `--base-path PATH` `--test-cases JSON` | 生成测试用例文件（含依赖链） |
| `gen-exec` | - | 生成测试执行脚本到用户目录（用户可自行执行） |
| `list` | `--type api/test` | 列出已生成的模块 |

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 2.0.0 | 2024-06-18 | 策略调整：移除自动执行功能，仅保留测试脚本和用例生成能力 |
| 1.3.0 | 2024-06-17 | 安全加固：扫描路径白名单机制，限制只能扫描 src/swagger/api/controller 目录 |
| 1.2.0 | 2024-06-17 | 安全加固：文件路径边界检查 + 网络域名白名单验证 |
| 1.1.0 | 2024-06-17 | 新增AI智能数据类型分析和前置依赖链生成 |
| 1.0.0 | 2024-01-15 | 初始版本，支持分层架构、交互式授权、增量测试 |
