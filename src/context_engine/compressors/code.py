from __future__ import annotations

import re
from typing import Any

from ..budget import resolve_output_budget, trim_text_to_budget
from ..schemas import CompressionRequest, CompressionResult, ContextItem, SourceType


WORD_RE = re.compile(r"[A-Za-z0-9_]+")
HOT_PATH_HINTS = ("test", "parser", "pipeline", "service", "validator")
LOW_SIGNAL_PATH_HINTS = ("ui", "theme", "style", "color")


def _keywords(text: str) -> set[str]:
    return {token.lower() for token in WORD_RE.findall(text) if len(token) >= 3}


def _score_item(item: ContextItem, issue_terms: set[str], failure_terms: set[str]) -> tuple[float, int]:
    content_terms = _keywords(item.content)
    path_text = str(item.metadata.get("path", ""))
    symbol_text = str(item.metadata.get("symbol", ""))
    meta_terms = _keywords(path_text + " " + symbol_text)
    overlap = len((content_terms | meta_terms) & issue_terms)
    failure_overlap = len((content_terms | meta_terms) & failure_terms)
    path_bonus = 1.2 if any(hint in path_text.lower() for hint in HOT_PATH_HINTS) else 0.0
    raise_bonus = 1.5 if "raise " in item.content or "throw " in item.content else 0.0
    assert_bonus = 1.0 if "assert " in item.content else 0.0
    low_signal_penalty = 1.6 if any(hint in path_text.lower() for hint in LOW_SIGNAL_PATH_HINTS) else 0.0
    total = (overlap * 2.5) + (failure_overlap * 1.7) + (item.priority * 0.2) + path_bonus + raise_bonus + assert_bonus - low_signal_penalty
    return total, overlap + failure_overlap


def _item_label(item: ContextItem) -> str:
    path = item.metadata.get("path") or "unknown-path"
    symbol = item.metadata.get("symbol")
    if symbol:
        return f"{path}::{symbol}"
    return str(path)


def compress_code(
    request: CompressionRequest,
    items: list[ContextItem],
    pipeline_stats: dict[str, Any],
) -> CompressionResult:
    issue = str(request.metadata.get("issue", "")).strip() or "No issue description provided."
    test_output = str(request.metadata.get("test_output", "")).strip()
    issue_terms = _keywords(issue)
    failure_terms = _keywords(test_output)

    ranked: list[tuple[float, int, ContextItem]] = []
    for item in items:
        score, overlap = _score_item(item, issue_terms, failure_terms)
        ranked.append((score, overlap, item))

    ranked.sort(key=lambda row: (row[0], row[1], row[2].priority), reverse=True)
    hot_items = ranked[: min(2, len(ranked))]
    supporting_items = ranked[min(2, len(ranked)) : min(3, len(ranked))]
    cold_items = ranked[min(3, len(ranked)) :]

    summary_target = _item_label(hot_items[0][2]) if hot_items else "no file context"
    summary = (
        f"Ranked {len(items)} code context items for issue '{issue}'. "
        f"Most likely hotspot is {summary_target}."
    )
    key_facts = [
        f"Issue: {issue}",
        f"Context files: {len(items)}",
        f"Likely hotspot: {summary_target}",
        f"Supporting files: {len(supporting_items)}",
    ]
    if test_output:
        key_facts.append(f"Failure signal captured: {test_output.splitlines()[0]}")

    dropped_noise = [f"Lower-priority context: {_item_label(item)}" for _, _, item in cold_items]

    context_lines = [
        "[ISSUE]",
        issue,
    ]
    if test_output:
        context_lines.extend(["", "[TEST OUTPUT]", test_output])

    context_lines.extend(["", "[LIKELY HOTSPOT FILES]"])
    for score, overlap, item in hot_items:
        context_lines.append(f"- {_item_label(item)} | score={score:.2f} | overlap={overlap}")

    if supporting_items:
        context_lines.extend(["", "[SUPPORTING FILES]"])
        for score, overlap, item in supporting_items:
            context_lines.append(f"- {_item_label(item)} | score={score:.2f} | overlap={overlap}")

    context_lines.extend(["", "[MINIMAL FIX CONTEXT]"])
    for _, _, item in hot_items + supporting_items:
        context_lines.append(f"## {_item_label(item)}")
        context_lines.append(item.content.strip())

    llm_ready_context = trim_text_to_budget("\n".join(context_lines), resolve_output_budget(request.budget))

    stats = dict(pipeline_stats)
    stats.update(
        {
            "hot_items": len(hot_items),
            "supporting_items": len(supporting_items),
            "cold_items": len(cold_items),
            "has_test_output": bool(test_output),
        }
    )

    return CompressionResult(
        mode=SourceType.CODE,
        summary=summary,
        key_facts=key_facts,
        dropped_noise=dropped_noise,
        llm_ready_context=llm_ready_context,
        normalized_items=items,
        stats=stats,
    )