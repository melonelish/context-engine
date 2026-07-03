# Release Assets

## GitHub Description

Task-aware context compression for logs, RAG chunks, and code context. CLI + MCP for agent and AI coding workflows.

## GitHub Topics

`llm` `rag` `mcp` `agents` `ai-coding` `context-compression` `python`

## Suggested Release Title

`v0.1.0 - Early external beta for task-aware context compression`

## Release Note

### What this release is

`Context Engine` is a task-aware context compression engine for agents, RAG pipelines, and coding assistants.

This `v0.1.0` release is the first public beta meant for external developer use, integration testing, and feedback collection.

### What it can do

- compress noisy logs into root-cause-oriented context
- rank RAG chunks around a user question and separate low-signal evidence
- rank hotspot code files around an issue or failing test
- expose the same flow through CLI and one MCP tool: `compress_context`

### What is included

- unified `logs`, `rag`, and `code` compression flows
- CLI entrypoint for all three modes
- MCP server entrypoint
- structured success and error envelopes
- regression tests for noisy logs, mixed retrieval results, and code-failure cases
- benchmark cases and generated benchmark results
- GitHub Actions CI

### Current boundaries

This is not yet a fully general context infrastructure layer for every real-world payload shape.

Known limitations:

- RAG ranking is still heuristic and not embedding-aware
- code ranking is still lexical and not dependency-graph-aware
- benchmark coverage is still intentionally small
- binary document inputs are not supported yet

### Recommended usage

Use this release if you want to:

- integrate a context compression layer into an agent workflow
- reduce noise before handing logs or retrieval chunks to an LLM
- test MCP-based integration paths
- evaluate the project and give feedback on real-world data

## GitHub README Hero Copy

### One-line positioning

Context Engine turns noisy logs, retrieval chunks, and code context into structured high-signal inputs that LLMs can use more reliably.

### Short intro block

Most agent systems do not fail because they lack data. They fail because they feed too much low-signal context into the model.

Context Engine is a task-aware compression layer for three common problem shapes:

- logs and tracebacks
- RAG retrieval results
- code + failure context

Instead of generic summarization, it keeps the parts a repair or reasoning agent actually needs: likely root cause lines, high-signal evidence chunks, hotspot files, and minimal fix context.

## CSDN First-Post Draft

# 我做了一个给 Agent / RAG / AI Coding 用的上下文压缩引擎：Context Engine

这几个月我越来越强烈地感受到一个问题：
很多 Agent 系统并不是模型不够强，而是喂给模型的上下文太脏、太长、太乱。

日志里有大量重复 heartbeat 和 poll 信息；
RAG 检索回来的 chunk 里经常混着相关和不相关内容；
代码修复场景里，模型看到的是一堆文件，而不是最小修复上下文。

所以我做了一个项目，叫 `Context Engine`。

它的目标不是再做一个聊天产品，而是做一个更底层的“上下文压缩层”：
把原始日志、检索结果、代码上下文压缩成更适合大模型处理的高信号输入。

当前版本已经支持三类场景：

- `logs`：提取 root cause、保留 traceback tail、归并重复噪声
- `rag`：围绕问题对检索 chunk 重新排序，分离低信号内容
- `code`：围绕 issue/test failure 排 hotspot file 和 supporting file

另外它已经提供：

- CLI 用法
- MCP server 接入
- 结构化错误返回
- regression tests
- benchmark 样例

我把它开源在这里：

`https://github.com/melonelish/context-engine`

如果你也在做：

- Agent 工作流
- RAG 系统
- AI Coding 工具
- MCP 集成

欢迎试一下，也欢迎直接拿真实脏数据来打它。

我现在最想收集的反馈有两类：

1. 哪些真实输入会把它搞崩或者压错重点
2. 对 `logs` / `rag` / `code` 三类场景，最值得继续加强的是哪一块

如果这个方向继续做下去，我后面会重点补：

- embedding/rerank 驱动的 RAG 排序
- 更强的 code hotspot 识别
- 更多真实 benchmark
- 更完整的文档和发布版本

## Short Social Post

I open-sourced `Context Engine`, a task-aware context compression layer for logs, RAG chunks, and code-failure context.

It supports CLI + MCP and focuses on turning noisy context into higher-signal LLM input instead of doing generic summarization.

Repo:
https://github.com/melonelish/context-engine