from __future__ import annotations

from collections import Counter
from typing import Any

from ..budget import resolve_output_budget, trim_text_to_budget
from ..schemas import CompressionRequest, CompressionResult, ContextItem, SourceType


ERROR_MARKERS = (
    "error",
    "exception",
    "traceback",
    "failed",
    "fatal",
    "panic",
    "caused by",
)


def _find_traceback_tail(lines: list[str]) -> list[str]:
    last_traceback = -1
    for index, line in enumerate(lines):
        if "traceback" in line.lower():
            last_traceback = index

    if last_traceback == -1:
        return []

    return lines[last_traceback:]


def _find_error_lines(lines: list[str]) -> list[str]:
    result: list[str] = []
    for line in lines:
        lowered = line.lower()
        if any(marker in lowered for marker in ERROR_MARKERS):
            result.append(line)
    return result


def _find_root_cause(error_lines: list[str]) -> str:
    for line in reversed(error_lines):
        lowered = line.lower()
        if "caused by" in lowered:
            return line
        if "exception" in lowered or "error" in lowered:
            return line
    return error_lines[-1] if error_lines else "No explicit error line found."


def compress_logs(
    request: CompressionRequest,
    items: list[ContextItem],
    pipeline_stats: dict[str, Any],
) -> CompressionResult:
    joined = "\n".join(item.content for item in items)
    raw_lines = [line.rstrip() for line in joined.splitlines() if line.strip()]
    counts = Counter(raw_lines)

    repeated_lines = [line for line, count in counts.items() if count > 1]
    noise_descriptions = [f"{counts[line]}x {line}" for line in repeated_lines[:8]]
    error_lines = _find_error_lines(raw_lines)
    traceback_tail = _find_traceback_tail(raw_lines)
    root_cause = _find_root_cause(error_lines)

    key_facts = [
        f"Input lines: {len(raw_lines)}",
        f"Unique lines: {len(counts)}",
        f"Repeated noise groups: {len(repeated_lines)}",
        f"Likely root cause: {root_cause}",
    ]

    summary = (
        f"Detected {len(error_lines)} error-oriented lines across {len(raw_lines)} log lines. "
        f"Likely root cause is '{root_cause}'."
    )

    context_sections = [
        "[ROOT CAUSE]",
        root_cause,
        "",
        "[KEY ERROR LINES]",
        *error_lines[-8:],
    ]

    if traceback_tail:
        context_sections.extend(["", "[TRACEBACK TAIL]", *traceback_tail[-12:]])

    if repeated_lines:
        context_sections.extend(["", "[NOISE REDUCED]", *noise_descriptions])

    llm_ready_context = trim_text_to_budget(
        "\n".join(context_sections),
        resolve_output_budget(request.budget),
    )

    stats = dict(pipeline_stats)
    stats.update(
        {
            "raw_line_count": len(raw_lines),
            "error_line_count": len(error_lines),
            "repeated_line_groups": len(repeated_lines),
            "traceback_tail_lines": len(traceback_tail),
        }
    )

    return CompressionResult(
        mode=SourceType.LOGS,
        summary=summary,
        key_facts=key_facts,
        dropped_noise=noise_descriptions,
        llm_ready_context=llm_ready_context,
        normalized_items=items,
        stats=stats,
    )
