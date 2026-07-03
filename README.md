# Context Engine

Context Engine is a task-aware context compression engine for agents, RAG pipelines, and coding assistants.

It turns noisy logs, retrieval chunks, and code context into tighter, structured inputs that are easier for an LLM to use well.

## What It Supports

- `logs`: keep root cause lines, traceback tails, and repeated-noise summaries
- `rag`: rank retrieved chunks against a user question and surface high-signal evidence
- `code`: rank likely hotspot files around an issue or failing test and emit minimal fix context
- `mcp`: expose the same compression flow through one `compress_context` tool

## Quickstart

```powershell
python -m pip install -e .[dev,mcp]
python -m pytest -q
python -m context_engine.cli --mode logs --input examples/logs/sample.log --budget medium
python -m context_engine.cli --mode rag --input examples/rag/sample.json --budget medium
python -m context_engine.cli --mode code --input examples/code/sample.json --budget medium
```

## CLI Usage

```powershell
python -m context_engine.cli --mode logs --input examples/logs/sample.log --budget small
python -m context_engine.cli --mode rag --input examples/rag/sample.json --budget medium
python -m context_engine.cli --mode code --input examples/code/sample.json --budget large
```

## MCP Usage

Run the MCP server over stdio:

```powershell
python -m context_engine.mcp_server
```

The server exposes one tool:

- `compress_context`: accepts `mode`, `budget`, and either raw log `content` or structured `payload` for `rag` and `code`

Example tool inputs:

```json
{
  "mode": "logs",
  "budget": "small",
  "content": "ERROR parser failed\nTraceback (most recent call last):\nValueError: bad email"
}
```

```json
{
  "mode": "rag",
  "budget": "medium",
  "payload": {
    "question": "What caused the login timeout?",
    "chunks": [
      {"content": "Redis pool exhaustion caused the timeout.", "source": "incident.md", "score": 0.96}
    ]
  }
}
```

## Before / After

Raw logs force an LLM to wade through polling noise, repeated fetch lines, and a full traceback. Context Engine extracts the likely root cause, keeps only the important error lines, and records repeated noise separately.

Raw RAG results often mix relevant incident evidence with unrelated chunks. Context Engine reorders chunks around the question and marks lower-signal evidence so the answer path is easier to follow.

Raw code context often arrives as a pile of files. Context Engine promotes the most likely hotspot, preserves the failure signal, and emits a compact fix-oriented block.

## Benchmarks

Benchmark cases and results live in [benchmarks/benchmark_cases.md](D:/Context_Engine/benchmarks/benchmark_cases.md) and [benchmarks/benchmark_results.md](D:/Context_Engine/benchmarks/benchmark_results.md).

Current headline from the sample set:

- `logs`: better than raw input and simple truncation because it keeps the root cause while dropping repeated noise
- `rag`: better than plain chunk dumps because it ranks evidence around the question instead of preserving retrieval order
- `code`: better than plain summaries because it preserves the issue, failure signal, hotspot file, and minimal fix context in one block

## Project Layout

```text
src/context_engine/
  schemas.py
  budget.py
  pipeline.py
  compressors/
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
  generate_benchmarks.py
tests/
  test_budget.py
  test_schemas.py
  test_pipeline.py
```

## Remaining Weak Spots

- the RAG ranker is still heuristic and not embedding-aware
- code ranking is lexical, so larger repos will need stronger symbol and dependency signals
- the benchmark set is intentionally small and should expand before public launch