# Context Engine 三天计划书

## 项目目标

在 3 天内完成 `Context Engine` 的 MVP，形态为 `Python SDK + CLI + MCP Server`，聚焦 Agent、RAG、AI Coding 三类场景中的上下文压缩。

第一版只证明一件事：

`Context Engine 比简单截断或普通总结，更适合把脏、长、乱的上下文压缩成可直接喂给大模型的高信号输入。`

## MVP 范围

本次只做最小可验证闭环。

纳入范围：

- 统一的上下文输入 Schema
- 三类压缩场景：
  - 日志 / traceback
  - RAG 检索片段
  - 代码上下文
- 预算感知的压缩输出
- 结构化 JSON 结果
- 本地 CLI 演示入口
- 一个最小 MCP 工具入口
- 3 组 before / after 示例
- 与简单基线的对比结果

不纳入范围：

- Web UI
- VS Code 插件
- 多轮记忆压缩
- 自动修复代码
- 模型训练或微调流程
- 生产级鉴权、监控、持久化

## 三天后交付物

3 天结束时，项目应具备：

- 可安装的 Python 包结构
- 可运行的 SDK API
- 可运行的 CLI
- 可运行的 MCP Server
- 3 个示例场景及压缩结果
- 一份简短 benchmark 结果表
- 一版可发布的 README 草稿

## 技术栈建议

- Python 3.11+
- `pydantic`：数据结构
- `typer`：CLI
- `tiktoken` 或同类 tokenizer：预算控制
- `fastmcp`：MCP server
- `pytest`：基础测试
- `uv`：环境和包管理

## 目录建议

```text
Context_Engine/
  src/context_engine/
    __init__.py
    schemas.py
    budget.py
    pipeline.py
    compressors/
      __init__.py
      logs.py
      rag.py
      code.py
    cli.py
    mcp_server.py
  examples/
    logs/
    rag/
    code/
  benchmarks/
    benchmark_cases.md
    benchmark_results.md
  tests/
    test_budget.py
    test_schemas.py
    test_pipeline.py
  README.md
  pyproject.toml
```

## 第一天：先跑通骨架和第一条链路

### 目标

把项目骨架搭起来，并确保至少一个场景可以端到端跑通。

### 任务

1. 初始化项目
- 创建 `pyproject.toml`
- 创建 `src/` 包结构
- 加入基础依赖
- 写最小 README 骨架

2. 定义内部数据模型
- `ContextItem`
- `CompressionRequest`
- `CompressionResult`
- 字段至少包含 `source_type`、`content`、`metadata`、`priority`、`budget`

3. 实现共享 pipeline
- 原始输入标准化为 `ContextItem`
- 去重明显重复内容
- 估算 token 大小
- 做简单预算裁剪
- 返回统一结构

4. 先做第一个压缩器：`logs`
- 识别重复日志行
- 保留 traceback 尾部和 error 行
- 提取疑似根因行
- 输出 `summary`、`key_facts`、`dropped_noise`、`llm_ready_context`

5. 准备第一个 demo
- 一个真实日志样本
- 一个预期压缩输出

### 当天完成标准

- `python -m context_engine.cli` 能处理一个日志样本
- 输出为结构化 JSON 或 Markdown
- 效果肉眼明显优于直接丢原始日志

### 建议时间分配

- 2 小时：项目初始化
- 2 小时：schema 和 pipeline
- 2.5 小时：日志压缩器
- 1 小时：示例和手工验证

## 第二天：补齐 MVP 表面能力

### 目标

从单场景扩展到完整 MVP：日志、RAG、代码上下文，加上可用的 CLI。

### 任务

1. 实现 `rag` 压缩器
- 输入：用户问题 + 检索 chunk
- 去掉重复证据
- 标记高相关与低相关片段
- 生成可直接回答问题的压缩证据块

2. 实现 `code` 压缩器
- 输入：报错信息 + 文件片段 + 可选测试输出
- 保留文件路径、符号名和可能影响范围
- 生成最小修复上下文

3. 完善预算控制
- 支持 `small`、`medium`、`large`
- 输出长度尽量贴近预算

4. 完成 CLI
- 支持 `--mode logs|rag|code`
- 支持 `--input`
- 支持 `--budget`
- 支持 JSON 输出

5. 整理示例集
- `examples/logs`
- `examples/rag`
- `examples/code`

6. 增加最小测试
- schema 校验
- budget 裁剪
- pipeline smoke test

### 当天完成标准

- 三种模式都能本地运行
- 每种模式都有一个可展示样例
- CLI 稳定到可以直接做 README 示例和截图

### 建议时间分配

- 2.5 小时：RAG 压缩器
- 2.5 小时：代码压缩器
- 1.5 小时：CLI
- 1 小时：测试
- 0.5 小时：示例清理

## 第三天：MCP、Benchmark、包装发布

### 目标

把 MVP 变成一个可评估、可展示、可对外发布的项目雏形。

### 任务

1. 增加 MCP Server
- 暴露一个工具：`compress_context`
- 支持 mode 和 budget 参数
- 返回统一结构结果

2. 做基础对比
- 基线 A：原文直接输入
- 基线 B：简单截断
- 基线 C：普通摘要
- 与 `Context Engine` 对比

3. 写 benchmark 说明
- 至少 3 个 case
- 记录输入大小、输出大小、定性差异
- 明确在哪些地方赢，哪些地方还弱

4. 完善 README
- 一句话定位
- 支持场景
- quickstart
- CLI 示例
- MCP 示例
- before / after 示例
- benchmark 表格

5. 收尾工程包装
- 确认本地安装可用
- 确认示例命令有效
- 确认 import 稳定

6. 最终验证
- 跑测试
- 手工跑 3 个示例流
- 检查 README 里的命令是否都能执行

### 当天完成标准

- 包可以本地安装
- MCP server 能跑起来
- README 已经达到可公开发布的水平
- benchmark 足以证明它不只是普通 summarization

### 建议时间分配

- 2 小时：MCP server
- 2 小时：benchmark 和结果整理
- 2 小时：README 与打包收尾
- 1 小时：最终验证和修问题

## 明确交付清单

三天结束后，至少产出这些文件：

- `src/context_engine/schemas.py`
- `src/context_engine/pipeline.py`
- `src/context_engine/compressors/logs.py`
- `src/context_engine/compressors/rag.py`
- `src/context_engine/compressors/code.py`
- `src/context_engine/cli.py`
- `src/context_engine/mcp_server.py`
- `examples/logs/sample.log`
- `examples/rag/sample.json`
- `examples/code/sample.json`
- `benchmarks/benchmark_results.md`
- `README.md`

## 时间不够时的优先级

如果三天内时间吃紧，优先顺序固定为：

1. SDK 核心
2. logs + rag 压缩器
3. CLI
4. MCP server
5. code 压缩器打磨
6. 测试与 README 美化

不要为了包装感，牺牲前两个核心能力。

## 风险和应对

### 风险 1：看起来像普通摘要

应对：
- 强制结构化输出
- 保留任务感知字段
- 用 logs、RAG、code 三类 before / after 举证

### 风险 2：范围失控

应对：
- 不做 UI
- 不增加第四种模式
- 用共享 pipeline + 薄场景层实现

### 风险 3：MCP 集成拖时间

应对：
- 第三天只暴露一个工具
- 直接复用 SDK pipeline，不另建复杂抽象

### 风险 4：benchmark 太弱

应对：
- 小而真实，不求大全
- 只跟简单基线比，不跟所有框架混战
- 样本尽量用真实脏数据，不用过度理想化样本

## 完成定义

这轮 3 天冲刺完成的标准是：

- 用户能本地安装并运行
- 工具能处理三类真实上下文
- 输出是结构化且预算感知的
- 有 MCP 入口
- 至少有 3 组有说服力的 demo
- README 在 1 分钟内能讲清项目价值

## 第四天以后建议

如果这 3 天做顺了，下一轮重点应该放在：

- 提升 rerank 和去重质量
- 增加 OpenAI / Ollama / Qwen provider adapter
- 扩展 benchmark 样本集
- 发布 PyPI 包
- 写第一篇 CSDN 首发文章

## 对外发布文案草稿

建议你对外这样描述：

`Context Engine 是一个面向 agents、RAG 和 coding assistants 的任务感知上下文压缩引擎。它把噪声日志、检索片段和代码上下文压缩成更紧凑、更适合大模型处理的高信号输入。`

这句话足够聚焦，也给后续扩展留了空间。
