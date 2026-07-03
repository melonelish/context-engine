from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .budget import estimate_tokens, resolve_input_budget, resolve_output_budget, sort_and_trim_items
from .compressors.code import compress_code
from .compressors.logs import compress_logs
from .compressors.rag import compress_rag
from .schemas import CompressionRequest, CompressionResult, ContextItem, SourceType


def normalize_items(raw_items: Iterable[ContextItem | dict[str, Any] | str], mode: SourceType) -> list[ContextItem]:
    normalized: list[ContextItem] = []

    for raw in raw_items:
        if isinstance(raw, ContextItem):
            item = raw
        elif isinstance(raw, dict):
            payload = dict(raw)
            payload.setdefault("source_type", mode)
            item = ContextItem(**payload)
        elif isinstance(raw, str):
            item = ContextItem(source_type=mode, content=raw)
        else:
            raise TypeError(f"Unsupported context item: {type(raw)!r}")

        item.token_estimate = estimate_tokens(item.content)
        normalized.append(item)

    return normalized


def deduplicate_items(items: list[ContextItem]) -> tuple[list[ContextItem], int]:
    seen: set[str] = set()
    deduped: list[ContextItem] = []
    duplicates = 0

    for item in items:
        key = " ".join(item.content.split())
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        deduped.append(item)

    return deduped, duplicates


def prepare_request(request: CompressionRequest) -> tuple[list[ContextItem], dict[str, Any]]:
    normalized = normalize_items(request.items, request.mode)
    deduped, duplicate_items = deduplicate_items(normalized)
    kept_items, dropped_items = sort_and_trim_items(deduped, resolve_input_budget(request.budget))

    stats = {
        "input_items": len(request.items),
        "normalized_items": len(normalized),
        "duplicate_items_removed": duplicate_items,
        "budget_dropped_items": len(dropped_items),
        "estimated_input_tokens": sum(item.token_estimate or 0 for item in kept_items),
        "requested_output_tokens": resolve_output_budget(request.budget),
    }
    return kept_items, stats


def compress_request(request: CompressionRequest) -> CompressionResult:
    prepared_items, stats = prepare_request(request)

    if request.mode is SourceType.LOGS:
        return compress_logs(request=request, items=prepared_items, pipeline_stats=stats)
    if request.mode is SourceType.RAG:
        return compress_rag(request=request, items=prepared_items, pipeline_stats=stats)
    if request.mode is SourceType.CODE:
        return compress_code(request=request, items=prepared_items, pipeline_stats=stats)

    raise NotImplementedError(f"Mode {request.mode.value!r} is not implemented yet.")