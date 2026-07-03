from __future__ import annotations

from typing import Any

from .pipeline import compress_request
from .schemas import BudgetConfig, BudgetPreset, CompressionRequest, ContextItem, SourceType

try:
    from fastmcp import FastMCP
except ImportError:
    FastMCP = None  # type: ignore[assignment]


def _budget_from_value(value: str | BudgetPreset) -> BudgetConfig:
    preset = value if isinstance(value, BudgetPreset) else BudgetPreset(str(value))
    return BudgetConfig(preset=preset)


def _request_from_logs(content: str, budget: str | BudgetPreset) -> CompressionRequest:
    if not content.strip():
        raise ValueError("Logs mode requires non-empty 'content'.")
    return CompressionRequest(
        mode=SourceType.LOGS,
        items=[
            ContextItem(
                source_type=SourceType.LOGS,
                content=content,
                metadata={"source": "mcp"},
                priority=10,
            )
        ],
        budget=_budget_from_value(budget),
    )


def _request_from_rag(payload: dict[str, Any], budget: str | BudgetPreset) -> CompressionRequest:
    question = payload.get("question")
    chunks = payload.get("chunks")
    if not isinstance(question, str) or not question.strip():
        raise ValueError("RAG mode requires a non-empty payload.question string.")
    if not isinstance(chunks, list) or not chunks:
        raise ValueError("RAG mode requires a non-empty payload.chunks list.")

    items = []
    for index, chunk in enumerate(chunks):
        if not isinstance(chunk, dict) or not str(chunk.get("content", "")).strip():
            raise ValueError(f"RAG chunk at index {index} must include non-empty content.")
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
        budget=_budget_from_value(budget),
        metadata={"question": question.strip()},
    )


def _request_from_code(payload: dict[str, Any], budget: str | BudgetPreset) -> CompressionRequest:
    issue = payload.get("issue")
    files = payload.get("files")
    if not isinstance(issue, str) or not issue.strip():
        raise ValueError("Code mode requires a non-empty payload.issue string.")
    if not isinstance(files, list) or not files:
        raise ValueError("Code mode requires a non-empty payload.files list.")

    items = []
    for index, file_payload in enumerate(files):
        if not isinstance(file_payload, dict) or not str(file_payload.get("content", "")).strip():
            raise ValueError(f"Code file at index {index} must include non-empty content.")
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
        budget=_budget_from_value(budget),
        metadata={
            "issue": issue.strip(),
            "test_output": str(payload.get("test_output", "")).strip(),
        },
    )


def compress_context(
    mode: str,
    budget: str = "medium",
    content: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_type = SourceType(str(mode))

    if source_type is SourceType.LOGS:
        request = _request_from_logs(content or "", budget)
    elif source_type is SourceType.RAG:
        request = _request_from_rag(payload or {}, budget)
    elif source_type is SourceType.CODE:
        request = _request_from_code(payload or {}, budget)
    else:
        raise ValueError(f"Unsupported mode: {mode}")

    return compress_request(request).model_dump()


if FastMCP is not None:
    mcp = FastMCP(
        name="Context Engine",
        instructions="Compress logs, retrieval chunks, and code context into structured LLM-ready signal.",
    )
    mcp.tool(name="compress_context", description="Compress logs, rag chunks, or code context into structured output.")(compress_context)
else:
    mcp = None


def get_mcp_server() -> Any:
    if mcp is None:
        raise RuntimeError("fastmcp is not installed. Install with `python -m pip install -e .[mcp]`.")
    return mcp


if __name__ == "__main__":
    get_mcp_server().run(transport="stdio")