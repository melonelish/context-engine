import asyncio

import pytest

pytest.importorskip("fastmcp")

from context_engine.mcp_server import compress_context, get_mcp_server


def test_mcp_server_registers_tool() -> None:
    server = get_mcp_server()
    tool = asyncio.run(server.get_tool("compress_context"))

    assert tool is not None
    assert tool.name == "compress_context"


def test_mcp_compress_context_logs() -> None:
    payload = compress_context(
        mode="logs",
        budget="small",
        content="INFO poll\nERROR parser failed\nTraceback (most recent call last):\nValueError: bad email\n",
    )

    assert payload["ok"] is True
    assert payload["result"]["mode"] == "logs"
    assert "[ROOT CAUSE]" in payload["result"]["llm_ready_context"]


def test_mcp_compress_context_returns_structured_error() -> None:
    payload = compress_context(mode="rag", budget="small", payload={"question": "why"})

    assert payload["ok"] is False
    assert payload["error"]["error_code"] == "invalid_field"