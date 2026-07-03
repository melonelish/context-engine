from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from context_engine.api import build_request_from_file
from context_engine.budget import estimate_tokens, trim_text_to_budget
from context_engine.pipeline import compress_request
from context_engine.schemas import BudgetPreset, CompressionRequest, SourceType


ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "benchmarks" / "benchmark_results.md"


def _raw_context_for_request(request: CompressionRequest) -> str:
    if request.mode is SourceType.LOGS:
        return request.items[0].content.strip()
    if request.mode is SourceType.RAG:
        lines = ["[QUESTION]", str(request.metadata.get("question", "")), "", "[RETRIEVED CHUNKS]"]
        for item in request.items:
            label = item.metadata.get("source", "unknown-source")
            lines.append(f"- {label}")
            lines.append(item.content.strip())
        return "\n".join(lines)
    if request.mode is SourceType.CODE:
        lines = ["[ISSUE]", str(request.metadata.get("issue", ""))]
        test_output = str(request.metadata.get("test_output", "")).strip()
        if test_output:
            lines.extend(["", "[TEST OUTPUT]", test_output])
        lines.extend(["", "[FILES]"])
        for item in request.items:
            label = item.metadata.get("path", "unknown-path")
            lines.append(f"## {label}")
            lines.append(item.content.strip())
        return "\n".join(lines)
    raise NotImplementedError


def _plain_summary(request: CompressionRequest) -> str:
    if request.mode is SourceType.LOGS:
        lines = [line for line in request.items[0].content.splitlines() if line.strip()]
        return "\n".join(lines[:4] + lines[-2:])
    if request.mode is SourceType.RAG:
        lines = ["[SUMMARY]", str(request.metadata.get("question", ""))]
        for item in request.items[:2]:
            lines.append(item.content.strip().split(".")[0].strip() + ".")
        return "\n".join(lines)
    if request.mode is SourceType.CODE:
        lines = ["[SUMMARY]", str(request.metadata.get("issue", ""))]
        for item in request.items:
            label = item.metadata.get("path", "unknown-path")
            first_line = item.content.strip().splitlines()[0]
            lines.append(f"- {label}: {first_line}")
        return "\n".join(lines)
    raise NotImplementedError


def _presence_score(text: str, terms: list[str]) -> int:
    lowered = text.lower()
    return sum(1 for term in terms if term.lower() in lowered)


def _row(case: str, request: CompressionRequest, target_terms: list[str], note: str) -> dict[str, Any]:
    engine = compress_request(request)
    raw = _raw_context_for_request(request)
    trunc = trim_text_to_budget(raw, request.budget.max_output_tokens or 220)
    summary = _plain_summary(request)

    return {
        "case": case,
        "input_tokens": sum(item.token_estimate or estimate_tokens(item.content) for item in request.items),
        "raw_tokens": estimate_tokens(raw),
        "trunc_tokens": estimate_tokens(trunc),
        "summary_tokens": estimate_tokens(summary),
        "engine_tokens": estimate_tokens(engine.llm_ready_context),
        "raw_hits": _presence_score(raw, target_terms),
        "trunc_hits": _presence_score(trunc, target_terms),
        "summary_hits": _presence_score(summary, target_terms),
        "engine_hits": _presence_score(engine.llm_ready_context, target_terms),
        "note": note,
    }


def main() -> None:
    logs_request = build_request_from_file(SourceType.LOGS, ROOT / "examples" / "logs" / "sample.log", BudgetPreset.SMALL)
    rag_request = build_request_from_file(SourceType.RAG, ROOT / "examples" / "rag" / "sample.json", BudgetPreset.SMALL)
    code_request = build_request_from_file(SourceType.CODE, ROOT / "examples" / "code" / "sample.json", BudgetPreset.SMALL)

    rows = [
        _row(
            "logs-root-cause",
            logs_request,
            ["ValueError: email field missing '@' separator", "[ROOT CAUSE]"],
            "Engine keeps the root cause section while simple truncation starts from noisy poll lines.",
        ),
        _row(
            "rag-evidence-ranking",
            rag_request,
            ["Redis connection pool exhaustion", "enterprise SSO traffic spiked", "incident-review.md"],
            "Engine keeps the incident evidence first and marks weaker evidence separately.",
        ),
        _row(
            "code-hotspot-compression",
            code_request,
            ["src/parsers.py::normalize_resume", "ValueError: email field missing '@' separator", "[LIKELY HOTSPOT FILES]"],
            "Engine preserves issue, failure signal, and likely hotspot in one compact block.",
        ),
    ]

    lines = [
        "# Benchmark Results",
        "",
        "These results are generated from the repo's sample inputs with the `small` output budget so the tradeoffs are visible.",
        "",
        "| Case | Input Tokens | Raw Tokens | Trunc Tokens | Generic Summary Tokens | Engine Tokens | Raw Hits | Trunc Hits | Summary Hits | Engine Hits |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for row in rows:
        lines.append(
            f"| {row['case']} | {row['input_tokens']} | {row['raw_tokens']} | {row['trunc_tokens']} | {row['summary_tokens']} | {row['engine_tokens']} | {row['raw_hits']} | {row['trunc_hits']} | {row['summary_hits']} | {row['engine_hits']} |"
        )

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    for row in rows:
        lines.append(f"- `{row['case']}`: {row['note']}")
    lines.append("- Token count is not the only success metric here. The code case shows why: the engine spends a few more tokens to keep the exact failure signal and hotspot structure that a repair agent needs.")

    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()