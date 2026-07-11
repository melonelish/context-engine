from __future__ import annotations

from typing import Any

from .api import compress_from_inputs
from .errors import ContextEngineError

try:
    from fastmcp import FastMCP
except ImportError:
    FastMCP = None  # type: ignore[assignment]


def compress_context(
    mode: str,
    budget: str = "medium",
    content: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        result = compress_from_inputs(mode=mode, budget=budget, content=content, payload=payload)
        return {"ok": True, "result": result}
    except ContextEngineError as exc:
        return {"ok": False, "error": exc.to_dict()}


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


def main() -> None:
    get_mcp_server().run(transport="stdio")


if __name__ == "__main__":
    main()
