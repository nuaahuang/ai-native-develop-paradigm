# 任务列表：api-doc-skill 增强优化

## 阶段一：基础设施增强

| 优先级 | 任务 | 复杂度 | 状态 |
|--------|------|--------|------|
| P0 | 创建 `scripts/models/` 目录结构和数据模型 | M | ⬜️ |
| P0 | 新增 `api_info.py` - 增强数据模型（版本、变更历史、示例） | M | ⬜️ |
| P0 | 新增 `version_info.py` - 版本信息数据模型 | S | ⬜️ |
| P0 | 创建 `scripts/config.py` - 配置管理模块 | S | ⬜️ |
| P0 | 创建 `scripts/validation/input_validator.py` - 输入验证框架 | S | ⬜️ |

## 阶段二：新增解析器

| 优先级 | 任务 | 复杂度 | 状态 |
|--------|------|--------|------|
| P1 | 创建 `scripts/parsers/django_parser.py` - Django REST Framework 解析器 | M | ⬜️ |
| P1 | 创建 `scripts/parsers/flask_parser.py` - Flask 解析器 | M | ⬜️ |
| P2 | 创建 `scripts/parsers/graphql_parser.py` - GraphQL 解析器 | L | ⬜️ |
| P2 | 创建 `scripts/parsers/grpc_parser.py` - gRPC protobuf 解析器 | L | ⬜️ |
| P1 | 改进现有解析器 - 增强容错性，支持非标准写法 | M | ⬜️ |

## 阶段三：批量生成功能

| 优先级 | 任务 | 复杂度 | 状态 |
|--------|------|--------|------|
| P1 | 创建 `scripts/batch/scanner.py` - 项目目录扫描器 | M | ⬜️ |
| P1 | 创建 `scripts/batch/batch_processor.py` - 批量处理器 | M | ⬜️ |
| P1 | 重构 `markdown_generator.py` - 完整文档重生成逻辑 | M | ⬜️ |
| P1 | 在 `skill_driver.py` 中添加 `--scan-dir` 参数支持 | S | ⬜️ |

## 阶段四：版本管理

| 优先级 | 任务 | 复杂度 | 状态 |
|--------|------|--------|------|
| P1 | 创建 `scripts/document/version_manager.py` - 版本管理器 | M | ⬜️ |
| P2 | 创建 `scripts/document/change_detector.py` - 变更检测 | M | ⬜️ |
| P2 | 添加版本对比输出到 Markdown | M | ⬜️ |
| P1 | 在 `skill_driver.py` 中添加 `--version` 参数支持 | S | ⬜️ |

## 阶段五：OpenAPI 导出

| 优先级 | 任务 | 复杂度 | 状态 |
|--------|------|--------|------|
| P1 | 创建 `scripts/exporters/openapi_exporter.py` - OpenAPI 3.0 导出 | M | ⬜️ |
| P2 | 创建 `scripts/exporters/swagger_exporter.py` - Swagger 2.0 导出 | M | ⬜️ |
| P1 | 在 `skill_driver.py` 中添加 `--export-openapi` 参数支持 | S | ⬜️ |

## 阶段六：示例与文档增强

| 优先级 | 任务 | 复杂度 | 状态 |
|--------|------|--------|------|
| P1 | 创建 `scripts/examples/example_generator.py` - 测试示例生成 | M | ⬜️ |
| P1 | 生成 curl、Python requests、JavaScript fetch 示例 | M | ⬜️ |
| P1 | 添加测试用例建议生成 | S | ⬜️ |
| P1 | 重构 `scripts/images/` - 图片处理模块增强 | M | ⬜️ |
| P1 | 创建 `scripts/images/validator.py` - 图片验证 | S | ⬜️ |
| P2 | 创建 `scripts/images/compressor.py` - 图片压缩 | S | ⬜️ |
| P1 | 重构云上传架构，拆分为多个 Uploader 实现 | M | ⬜️ |

## 更新 SKILL 文档

| 优先级 | 任务 | 复杂度 | 状态 |
|--------|------|--------|------|
| P0 | 更新 SKILL.md - 添加新参数和功能说明 | S | ⬜️ |

---

## 复杂度说明

- S: 简单（< 100 行代码）
- M: 中等（100-300 行代码）
- L: 复杂（> 300 行代码）

## 优先顺序说明

**P0** - 必须完成，基础设施  
**P1** - 主要功能，按计划完成  
**P2** - 扩展功能，时间允许则完成
