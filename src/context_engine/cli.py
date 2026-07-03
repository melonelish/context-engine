from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer

from .pipeline import compress_request
from .schemas import BudgetConfig, BudgetPreset, CompressionRequest, ContextItem, SourceType


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"Input file must contain valid JSON: {exc}") from exc


def _request_from_logs(path: Path, budget: BudgetPreset) -> CompressionRequest:
    content = path.read_text(encoding="utf-8")
    return CompressionRequest(
        mode=SourceType.LOGS,
        items=[
            ContextItem(
                source_type=SourceType.LOGS,
                content=content,
                metadata={"path": str(path)},
                priority=10,
            )
        ],
        budget=BudgetConfig(preset=budget),
    )


def _request_from_rag(path: Path, budget: BudgetPreset) -> CompressionRequest:
    payload = _load_json(path)
    question = payload.get("question")
    chunks = payload.get("chunks")
    if not isinstance(question, str) or not question.strip():
        raise typer.BadParameter("RAG input JSON must include a non-empty 'question' field.")
    if not isinstance(chunks, list) or not chunks:
        raise typer.BadParameter("RAG input JSON must include a non-empty 'chunks' array.")

    items = []
    for index, chunk in enumerate(chunks):
        if not isinstance(chunk, dict) or not str(chunk.get("content", "")).strip():
            raise typer.BadParameter(f"RAG chunk at index {index} must be an object with non-empty 'content'.")
        metadata = {key: value for key, value in chunk.items() if key not in {"content", "priority"}}
        items.append(
            ContextItem(
                source_type=SourceType.RAG,
                content=str(chunk["content"]),
                metadata=metadata,
                priority=int(chunk.get("priority", 0)),
            )
        )

    return CompressionRequest(
        mode=SourceType.RAG,
        items=items,
        budget=BudgetConfig(preset=budget),
        metadata={"question": question.strip()},
    )


def _request_from_code(path: Path, budget: BudgetPreset) -> CompressionRequest:
    payload = _load_json(path)
    issue = payload.get("issue")
    files = payload.get("files")
    if not isinstance(issue, str) or not issue.strip():
        raise typer.BadParameter("Code input JSON must include a non-empty 'issue' field.")
    if not isinstance(files, list) or not files:
        raise typer.BadParameter("Code input JSON must include a non-empty 'files' array.")

    items = []
    for index, file_payload in enumerate(files):
        if not isinstance(file_payload, dict) or not str(file_payload.get("content", "")).strip():
            raise typer.BadParameter(f"Code file at index {index} must be an object with non-empty 'content'.")
        metadata = {key: value for key, value in file_payload.items() if key not in {"content", "priority"}}
        items.append(
            ContextItem(
                source_type=SourceType.CODE,
                content=str(file_payload["content"]),
                metadata=metadata,
                priority=int(file_payload.get("priority", 0)),
            )
        )

    return CompressionRequest(
        mode=SourceType.CODE,
        items=items,
        budget=BudgetConfig(preset=budget),
        metadata={
            "issue": issue.strip(),
            "test_output": str(payload.get("test_output", "")).strip(),
        },
    )


def _build_request(mode: SourceType, path: Path, budget: BudgetPreset) -> CompressionRequest:
    if mode is SourceType.LOGS:
        return _request_from_logs(path, budget)
    if mode is SourceType.RAG:
        return _request_from_rag(path, budget)
    if mode is SourceType.CODE:
        return _request_from_code(path, budget)
    raise typer.BadParameter(f"Unsupported mode: {mode.value}")


def main(
    mode: SourceType = typer.Option(SourceType.LOGS, help="Compression mode: logs, rag, or code."),
    input: Path = typer.Option(..., exists=True, dir_okay=False, readable=True, help="Path to the input file."),
    budget: BudgetPreset = typer.Option(BudgetPreset.MEDIUM, help="Output budget preset."),
    pretty: bool = typer.Option(True, help="Pretty-print JSON output."),
) -> None:
    request = _build_request(mode, input, budget)
    result = compress_request(request)
    payload = result.model_dump()
    typer.echo(json.dumps(payload, ensure_ascii=True, indent=2 if pretty else None))


if __name__ == "__main__":
    typer.run(main)