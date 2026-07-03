import pytest

from context_engine.api import build_request_from_inputs, compress_from_inputs
from context_engine.errors import InputSizeError, InputValidationError, UnsupportedModeError
from context_engine.schemas import SCHEMA_VERSION, SourceType


def test_build_request_from_inputs_for_rag() -> None:
    request = build_request_from_inputs(
        mode=SourceType.RAG,
        budget="medium",
        payload={
            "question": "What caused the timeout?",
            "chunks": [{"content": "Redis pool exhaustion", "source": "incident.md", "score": 0.91}],
        },
    )

    assert request.mode is SourceType.RAG
    assert request.metadata["question"] == "What caused the timeout?"
    assert request.items[0].metadata["source"] == "incident.md"
    assert request.schema_version == SCHEMA_VERSION


def test_build_request_from_inputs_rejects_bad_mode() -> None:
    with pytest.raises(UnsupportedModeError):
        build_request_from_inputs(mode="video", budget="medium", content="x")


def test_compress_from_inputs_rejects_empty_logs() -> None:
    with pytest.raises(InputValidationError):
        compress_from_inputs(mode="logs", budget="small", content="   ")


def test_compress_from_inputs_rejects_oversized_text() -> None:
    with pytest.raises(InputSizeError):
        compress_from_inputs(mode="logs", budget="small", content="x" * 200001)


def test_build_request_rejects_too_many_chunks() -> None:
    chunks = [{"content": "signal"} for _ in range(65)]
    with pytest.raises(InputSizeError):
        build_request_from_inputs(mode="rag", budget="small", payload={"question": "why", "chunks": chunks})