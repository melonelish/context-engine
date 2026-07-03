from __future__ import annotations

import re
from typing import Any

from ..budget import resolve_output_budget, trim_text_to_budget
from ..schemas import CompressionRequest, CompressionResult, ContextItem, SourceType


WORD_RE = re.compile(r"[A-Za-z0-9_]+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "for",
    "from",
    "how",
    "into",
    "its",
    "that",
    "the",
    "their",
    "this",
    "was",
    "what",
    "when",
    "where",
    "which",
    "why",
    "with",
    "users",
}
NEGATIVE_HINTS = {"dashboard", "monthly", "analytics", "deleted", "ui", "color", "theme", "button", "design"}
SUPPORTIVE_HINTS = {"mitigation", "incident", "rollback", "retry", "redis", "timeout", "pool", "queue", "sso"}


def _keywords(text: str) -> set[str]:
    return {
        token.lower()
        for token in WORD_RE.findall(text)
        if len(token) >= 3 and token.lower() not in STOPWORDS
    }


def _score_chunk(item: ContextItem, question_terms: set[str]) -> tuple[float, int, int]:
    chunk_terms = _keywords(item.content)
    overlap_terms = chunk_terms & question_terms
    overlap = len(overlap_terms)
    source_score = float(item.metadata.get("score", 0.0) or 0.0)
    priority_boost = item.priority * 0.2
    supportive_count = sum(1 for token in chunk_terms if token in SUPPORTIVE_HINTS)
    negative_count = sum(1 for token in chunk_terms if token in NEGATIVE_HINTS)
    supportive_bonus = supportive_count * 0.5
    negative_penalty = negative_count * 1.5
    total = (overlap * 2.4) + source_score + priority_boost + supportive_bonus - negative_penalty
    return total, overlap, negative_count


def _label_for_item(item: ContextItem) -> str:
    source = item.metadata.get("source") or item.metadata.get("path") or "unknown-source"
    score = item.metadata.get("score")
    if score is None:
        return str(source)
    return f"{source} (score={score})"


def compress_rag(
    request: CompressionRequest,
    items: list[ContextItem],
    pipeline_stats: dict[str, Any],
) -> CompressionResult:
    question = str(request.metadata.get("question", "")).strip() or "No question provided."
    question_terms = _keywords(question)

    ranked: list[tuple[float, int, int, ContextItem]] = []
    for item in items:
        score, overlap, negative_count = _score_chunk(item, question_terms)
        ranked.append((score, overlap, negative_count, item))

    ranked.sort(key=lambda row: (row[0], row[1], -row[2], row[3].priority), reverse=True)

    high_signal: list[tuple[float, int, int, ContextItem]] = []
    supportive_signal: list[tuple[float, int, int, ContextItem]] = []
    low_signal: list[tuple[float, int, int, ContextItem]] = []
    for index, row in enumerate(ranked):
        score, overlap, negative_count, item = row
        source_score = float(item.metadata.get("score", 0.0) or 0.0)
        if negative_count >= 2 and source_score < 0.7:
            low_signal.append(row)
        elif overlap >= 2 or score >= 4.0:
            high_signal.append(row)
        elif (overlap > 0 and negative_count == 0) or source_score >= 0.82 or (index == 0 and negative_count == 0):
            supportive_signal.append(row)
        else:
            low_signal.append(row)

    top_sources = [_label_for_item(item) for _, _, _, item in (high_signal + supportive_signal)[:3]]
    evidence_lines = []
    for bucket_name, bucket in (("HIGH", high_signal[:3]), ("SUPPORT", supportive_signal[:2])):
        for _, overlap, _, item in bucket:
            label = _label_for_item(item)
            evidence_lines.append(f"- {bucket_name} | {label} | overlap={overlap}")
            evidence_lines.append(item.content.strip())

    lower_signal_lines = []
    for _, overlap, _, item in low_signal[:3]:
        label = _label_for_item(item)
        lower_signal_lines.append(f"- {label} | overlap={overlap}")
        lower_signal_lines.append(item.content.strip())

    selected_count = len(high_signal) + len(supportive_signal)
    summary = (
        f"Selected {selected_count} useful chunks out of {len(items)} retrieved chunks "
        f"for question '{question}'."
    )
    key_facts = [
        f"Question: {question}",
        f"Retrieved chunks: {len(items)}",
        f"High-signal chunks: {len(high_signal)}",
        f"Supportive chunks: {len(supportive_signal)}",
        f"Top sources: {', '.join(top_sources) if top_sources else 'none'}",
    ]
    dropped_noise = [f"Low-signal chunk: {_label_for_item(item)}" for _, _, _, item in low_signal]

    sections = [
        "[QUESTION]",
        question,
        "",
        "[HIGH SIGNAL EVIDENCE]",
        *evidence_lines,
    ]
    if lower_signal_lines:
        sections.extend(["", "[LOWER SIGNAL EVIDENCE]", *lower_signal_lines])

    llm_ready_context = trim_text_to_budget("\n".join(sections), resolve_output_budget(request.budget))

    stats = dict(pipeline_stats)
    stats.update(
        {
            "question_terms": len(question_terms),
            "high_signal_chunks": len(high_signal),
            "supportive_chunks": len(supportive_signal),
            "low_signal_chunks": len(low_signal),
        }
    )

    return CompressionResult(
        mode=SourceType.RAG,
        summary=summary,
        key_facts=key_facts,
        dropped_noise=dropped_noise,
        llm_ready_context=llm_ready_context,
        normalized_items=items,
        stats=stats,
    )