from __future__ import annotations

import re
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
    "valueerror",
    "runtimeerror",
    "typeerror",
    "timeout",
    "timed out",
    "无法",
    "失败",
    "异常",
    "报错",
)
POLL_PATTERNS = (
    r"status=empty",
    r"heartbeat",
    r"poll queue=",
    r"retrying in \d+",
)
NOISE_REGEXES = [re.compile(pattern, re.IGNORECASE) for pattern in POLL_PATTERNS]


def _normalize_line(line: str) -> str:
    compact = re.sub(r"\d+", "<num>", line)
    compact = re.sub(r"\s+", " ", compact.strip())
    return compact


def _is_noise_line(line: str) -> bool:
    return any(regex.search(line) for regex in NOISE_REGEXES)


def _find_traceback_tail(lines: list[str]) -> list[str]:
    last_traceback = -1
    for index, line in enumerate(lines):
        lowered = line.lower()
        if "traceback" in lowered or "stack trace" in lowered:
            last_traceback = index

    if last_traceback == -1:
        return []

    tail = lines[last_traceback : last_traceback + 18]
    return [line for line in tail if line.strip()]


def _find_error_lines(lines: list[str]) -> list[str]:
    result: list[str] = []
    for line in lines:
        lowered = line.lower()
        if any(marker in lowered for marker in ERROR_MARKERS):
            result.append(line)
    return result


def _score_root_cause(line: str) -> tuple[int, int]:
    lowered = line.lower()
    score = 0
    if "caused by" in lowered:
        score += 6
    if "valueerror" in lowered or "runtimeerror" in lowered or "typeerror" in lowered:
        score += 5
    if "timeout" in lowered or "timed out" in lowered:
        score += 4
    if any(token in lowered for token in ("无法", "失败", "异常", "报错")):
        score += 4
    if "error" in lowered or "exception" in lowered:
        score += 3
    return score, len(line)


def _find_root_cause(error_lines: list[str], traceback_tail: list[str]) -> str:
    candidates = error_lines + traceback_tail
    if not candidates:
        return "No explicit error line found."
    ranked = sorted(candidates, key=_score_root_cause, reverse=True)
    return ranked[0]


def compress_logs(
    request: CompressionRequest,
    items: list[ContextItem],
    pipeline_stats: dict[str, Any],
) -> CompressionResult:
    joined = "\n".join(item.content for item in items)
    raw_lines = [line.rstrip() for line in joined.splitlines() if line.strip()]
    normalized_counts = Counter(_normalize_line(line) for line in raw_lines)

    repeated_groups = [key for key, count in normalized_counts.items() if count > 1]
    repeated_noise = [key for key in repeated_groups if _is_noise_line(key)]
    noise_descriptions = [f"{normalized_counts[key]}x {key}" for key in repeated_noise[:8]]
    error_lines = _find_error_lines(raw_lines)
    traceback_tail = _find_traceback_tail(raw_lines)
    root_cause = _find_root_cause(error_lines, traceback_tail)

    signal_lines = []
    for line in error_lines[-10:]:
        if line not in signal_lines:
            signal_lines.append(line)
    for line in traceback_tail[-10:]:
        if line not in signal_lines:
            signal_lines.append(line)

    key_facts = [
        f"Input lines: {len(raw_lines)}",
        f"Repeated line groups: {len(repeated_groups)}",
        f"Repeated noise groups: {len(repeated_noise)}",
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
        *signal_lines,
    ]

    if traceback_tail:
        context_sections.extend(["", "[TRACEBACK TAIL]", *traceback_tail[-12:]])

    if noise_descriptions:
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
            "repeated_line_groups": len(repeated_groups),
            "repeated_noise_groups": len(repeated_noise),
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