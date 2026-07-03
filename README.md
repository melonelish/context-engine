# Context Engine

Context Engine is a task-aware context compression engine for agents, RAG pipelines, and coding assistants.

It turns noisy logs, retrieval chunks, and code context into tighter, structured inputs that are easier for an LLM to use well.

## Release Status

Current release target: `v0.1.0`

This version is suitable for early external use, integration testing, and developer workflows. It is not yet a guaranteed fit for every real-world payload shape, but it is now documented, tested, and structured as a reusable package instead of a one-off demo.

## What It Does

- `logs`: extract likely root cause lines, traceback tails, and repeated-noise summaries
- `rag`: rank retrieved chunks against a user question and separate high-signal evidence from low-signal evidence
- `code`: rank hotspot files around an issue or failing test and emit minimal fix-oriented context
- `mcp`: expose the same compression flow through one `compress_context` tool

## Supported Now

- Python `3.11` to `3.13`
- plain text log input
- JSON-based `rag` input with `question` and `chunks`
- JSON-based `code` input with `issue`, optional `test_output`, and `files`
- CLI usage for all three modes
- MCP usage through one `compress_context` tool
- structured success and error envelopes
- schema version `1.0`

## Stability Guards

Current built-in safety limits:

- max inline text size: `200000` characters
- max structured list size: `64` items
- max input file size: `2000000` bytes

These guards exist to prevent common failure modes when strangers throw arbitrarily large payloads at the tool.

## Not Supported Yet

- binary inputs such as PDF, images, or office files
- embedding-aware reranking
- repository-scale dependency analysis
- guarantees for every real-world data shape
- long-term backward compatibility promises across future major versions

## Install

Recommended: use a fresh virtual environment.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .[dev,mcp]
```

## Quickstart

```powershell
python -m pytest -q
python -m context_engine.cli --mode logs --input examples/logs/sample.log --budget medium
python -m context_engine.cli --mode rag --input examples/rag/sample.json --budget medium
python -m context_engine.cli --mode code --input examples/code/sample.json --budget medium
```

## Output Contract

CLI and MCP return structured envelopes:

- success: `{ "ok": true, "result": ... }`
- failure: `{ "ok": false, "error": { "error_code": ..., "message": ..., "hint": ..., "details": ... } }`

That means bad inputs should fail clearly instead of dumping a raw traceback to end users.

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

Example failure response:

```json
{
  "ok": false,
  "error": {
    "error_code": "invalid_field",
    "message": "Field 'chunks' must be a non-empty list.",
    "hint": "Provide at least one item in 'chunks'."
  }
}
```

## Benchmarks

Benchmark cases and results live in [benchmark_cases.md](/D:/Context_Engine/benchmarks/benchmark_cases.md:1) and [benchmark_results.md](/D:/Context_Engine/benchmarks/benchmark_results.md:1).

Current behavior from the sample set:

- `logs`: better than raw input and simple truncation because it keeps the root cause while dropping repeated noise
- `rag`: better than plain chunk dumps because it ranks evidence around the question instead of preserving retrieval order
- `code`: better than plain summaries because it preserves the issue, failure signal, hotspot file, and supporting context in one block

## Development Checks

```powershell
python -m pytest -q
python benchmarks/generate_benchmarks.py
```

CI runs on every push and pull request through GitHub Actions.

## Current Limits

- the RAG ranker is still heuristic and not embedding-aware
- code ranking is still lexical and will need stronger structural signals
- the benchmark set is still small and should grow before a broader production rollout
- `fastmcp` should be installed in an isolated virtual environment to avoid dependency conflicts with unrelated global packages