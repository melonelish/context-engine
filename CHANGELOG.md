# Changelog

## 0.1.0 - 2026-07-03

Initial public MVP release.

### Added

- unified compression support for `logs`, `rag`, and `code`
- CLI entrypoint for all three modes
- MCP server with one `compress_context` tool
- structured success and error envelopes for CLI and MCP
- benchmark cases and generated benchmark results
- regression fixtures for noisier logs, mixed RAG retrieval, and code-failure scenarios
- GitHub Actions CI for install and test verification

### Changed

- tightened `rag` heuristics to demote clearly off-topic chunks
- improved `logs` noise collapsing and root-cause extraction for mixed noisy traces
- improved `code` hotspot and supporting-file ranking

### Known Limits

- RAG ranking is still heuristic and not embedding-aware
- code-context scoring is still lexical
- benchmark coverage is still small and should expand before broader production rollout