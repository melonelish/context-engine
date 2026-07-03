from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import InputValidationError, UnsupportedModeError
from .pipeline import compress_request
from .schemas import BudgetConfig, BudgetPreset, CompressionRequest, ContextItem, SourceType
from .validators import ensure_file_within_limit, load_json_file, require_list, require_text


def budget_from_value(value: str | BudgetPreset) -> BudgetConfig:
    try:
        preset = value if isinstance(value, BudgetPreset) else BudgetPreset(str(value))
    except ValueError as exc:
        raise InputValidationError(
            error_code="invalid_budget",
            message=f"Unsupported budget preset: {value!r}.",
            hint="Use one of: small, medium, large.",
        ) from exc
    return BudgetConfig(preset=preset)


def build_logs_request_from_text(content: str, budget: str | BudgetPreset, source: str) -> CompressionRequest:
    return CompressionRequest(
        mode=SourceType.LOGS,
        items=[
            ContextItem(
                source_type=SourceType.LOGS,
                content=require_text(content, field_name="content"),
                metadata={"source": source},
                priority=10,
            )
        ],
        budget=budget_from_value(budget),
    )


def build_rag_request_from_payload(payload: dict[str, Any], budget: str | BudgetPreset) -> CompressionRequest:
    question = require_text(payload.get("question"), field_name="question")
    chunks = require_list(payload.get("chunks"), field_name="chunks")

    items = []
    for index, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            raise InputValidationError(
                error_code="invalid_chunk",
                message=f"Chunk at index {index} must be an object.",
                hint="Each chunk should be a JSON object with at least a 'content' field.",
            )
        metadata = {key: value for key, value in chunk.items() if key not in {"content", "priority"}}
        items.append(
            ContextItem(
                source_type=SourceType.RAG,
                content=require_text(chunk.get("content"), field_name=f"chunks[{index}].content"),
                metadata=metadata,
                priority=int(chunk.get("priority", 0)),
            )
        )

    return CompressionRequest(
        mode=SourceType.RAG,
        items=items,
        budget=budget_from_value(budget),
        metadata={"question": question},
    )


def build_code_request_from_payload(payload: dict[str, Any], budget: str | BudgetPreset) -> CompressionRequest:
    issue = require_text(payload.get("issue"), field_name="issue")
    files = require_list(payload.get("files"), field_name="files")

    items = []
    for index, file_payload in enumerate(files):
        if not isinstance(file_payload, dict):
            raise InputValidationError(
                error_code="invalid_file_item",
                message=f"File item at index {index} must be an object.",
                hint="Each file should be a JSON object with at least a 'content' field.",
            )
        metadata = {key: value for key, value in file_payload.items() if key not in {"content", "priority"}}
        items.append(
            ContextItem(
                source_type=SourceType.CODE,
                content=require_text(file_payload.get("content"), field_name=f"files[{index}].content"),
                metadata=metadata,
                priority=int(file_payload.get("priority", 0)),
            )
        )

    return CompressionRequest(
        mode=SourceType.CODE,
        items=items,
        budget=budget_from_value(budget),
        metadata={
            "issue": issue,
            "test_output": str(payload.get("test_output", "")).strip(),
        },
    )


def build_request_from_file(mode: SourceType, path: Path, budget: str | BudgetPreset) -> CompressionRequest:
    ensure_file_within_limit(path)
    if mode is SourceType.LOGS:
        return build_logs_request_from_text(path.read_text(encoding="utf-8"), budget, str(path))
    if mode is SourceType.RAG:
        return build_rag_request_from_payload(load_json_file(path), budget)
    if mode is SourceType.CODE:
        return build_code_request_from_payload(load_json_file(path), budget)
    raise UnsupportedModeError(
        error_code="unsupported_mode",
        message=f"Unsupported mode: {mode!r}.",
        hint="Use one of: logs, rag, code.",
    )


def build_request_from_inputs(
    *,
    mode: str | SourceType,
    budget: str | BudgetPreset,
    content: str | None = None,
    payload: dict[str, Any] | None = None,
    path: Path | None = None,
) -> CompressionRequest:
    try:
        source_type = mode if isinstance(mode, SourceType) else SourceType(str(mode))
    except ValueError as exc:
        raise UnsupportedModeError(
            error_code="unsupported_mode",
            message=f"Unsupported mode: {mode!r}.",
            hint="Use one of: logs, rag, code.",
        ) from exc

    if path is not None:
        return build_request_from_file(source_type, path, budget)
    if source_type is SourceType.LOGS:
        return build_logs_request_from_text(content or "", budget, "inline")
    if source_type is SourceType.RAG:
        return build_rag_request_from_payload(payload or {}, budget)
    if source_type is SourceType.CODE:
        return build_code_request_from_payload(payload or {}, budget)
    raise UnsupportedModeError(
        error_code="unsupported_mode",
        message=f"Unsupported mode: {mode!r}.",
        hint="Use one of: logs, rag, code.",
    )


def compress_from_inputs(
    *,
    mode: str | SourceType,
    budget: str | BudgetPreset,
    content: str | None = None,
    payload: dict[str, Any] | None = None,
    path: Path | None = None,
) -> dict[str, Any]:
    request = build_request_from_inputs(mode=mode, budget=budget, content=content, payload=payload, path=path)
    return compress_request(request).model_dump()