# Benchmark Cases

This benchmark set is intentionally small and uses the repo's sample inputs so results are reproducible during local development.

## Case 1: Logs Root Cause Recovery

- Input: `examples/logs/sample.log`
- Goal: retain the root cause line and traceback tail while dropping repeated noise
- Why it matters: raw logs often exceed budget before the real error becomes clear

## Case 2: RAG Evidence Ranking

- Input: `examples/rag/sample.json`
- Goal: rank evidence around the user question and demote unrelated retrieved chunks
- Why it matters: retrieval order is often not answer order

## Case 3: Code Hotspot Compression

- Input: `examples/code/sample.json`
- Goal: preserve issue statement, failure signal, likely hotspot file, and minimal fix context
- Why it matters: agents waste tokens when every file is treated equally

## Baselines

- Baseline A: raw context with no task-aware organization
- Baseline B: simple truncation to the same output budget
- Baseline C: generic summary with no mode-specific prioritization
- Context Engine: shared preprocessing plus mode-specific compression