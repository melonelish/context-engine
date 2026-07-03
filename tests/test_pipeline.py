import json
from pathlib import Path

from context_engine.api import build_request_from_inputs
from context_engine.pipeline import compress_request
from context_engine.schemas import BudgetConfig, CompressionRequest, ContextItem, SourceType


FIXTURES = Path(__file__).parent / "fixtures"


def test_logs_pipeline_smoke() -> None:
    request = CompressionRequest(
        mode=SourceType.LOGS,
        items=[
            ContextItem(
                source_type=SourceType.LOGS,
                content="INFO start\nERROR parser failed\nTraceback (most recent call last):\nValueError: bad email\n",
            )
        ],
        budget=BudgetConfig(),
    )

    result = compress_request(request)

    assert result.mode is SourceType.LOGS
    assert "root cause" in result.summary.lower()
    assert "ValueError: bad email" in result.llm_ready_context


def test_logs_pipeline_handles_noisy_mixed_logs() -> None:
    content = (FIXTURES / "logs" / "mixed_runtime.log").read_text(encoding="utf-8")
    request = build_request_from_inputs(mode="logs", budget="medium", content=content)

    result = compress_request(request)

    assert "candidate profile missing normalized_email" in result.llm_ready_context
    assert "[NOISE REDUCED]" in result.llm_ready_context
    assert result.stats["repeated_noise_groups"] >= 1


def test_rag_pipeline_smoke() -> None:
    request = CompressionRequest(
        mode=SourceType.RAG,
        metadata={"question": "What caused the login timeout?"},
        items=[
            ContextItem(
                source_type=SourceType.RAG,
                content="Redis connection pool exhaustion caused login timeout during SSO spike.",
                metadata={"source": "incident.md", "score": 0.95},
                priority=8,
            ),
            ContextItem(
                source_type=SourceType.RAG,
                content="A dashboard query for monthly active users was updated.",
                metadata={"source": "analytics.md", "score": 0.1},
            ),
        ],
        budget=BudgetConfig(),
    )

    result = compress_request(request)

    assert result.mode is SourceType.RAG
    assert "useful chunks" in result.summary.lower()
    assert "incident.md" in result.llm_ready_context


def test_rag_pipeline_demotes_unrelated_chunks() -> None:
    payload = json.loads((FIXTURES / "rag" / "incident_mixed.json").read_text(encoding="utf-8"))
    request = build_request_from_inputs(mode="rag", budget="medium", payload=payload)

    result = compress_request(request)

    assert "incident-review.md" in result.llm_ready_context
    assert "mitigation.md" in result.llm_ready_context
    assert "analytics.md" in " ".join(result.dropped_noise)
    assert result.stats["low_signal_chunks"] >= 1


def test_code_pipeline_smoke() -> None:
    request = CompressionRequest(
        mode=SourceType.CODE,
        metadata={
            "issue": "Fix malformed email normalization.",
            "test_output": "ValueError: email field missing '@' separator",
        },
        items=[
            ContextItem(
                source_type=SourceType.CODE,
                content="def normalize_resume(payload):\n    raise ValueError(\"email field missing '@' separator\")\n",
                metadata={"path": "src/parsers.py", "symbol": "normalize_resume"},
                priority=10,
            ),
            ContextItem(
                source_type=SourceType.CODE,
                content="def helper():\n    return 42\n",
                metadata={"path": "src/helpers.py", "symbol": "helper"},
            ),
        ],
        budget=BudgetConfig(),
    )

    result = compress_request(request)

    assert result.mode is SourceType.CODE
    assert "hotspot" in result.summary.lower()
    assert "src/parsers.py::normalize_resume" in result.llm_ready_context


def test_code_pipeline_prioritizes_hotspot_and_supporting_files() -> None:
    payload = json.loads((FIXTURES / "code" / "resume_failure.json").read_text(encoding="utf-8"))
    request = build_request_from_inputs(mode="code", budget="medium", payload=payload)

    result = compress_request(request)

    assert "[LIKELY HOTSPOT FILES]" in result.llm_ready_context
    assert "src/parsers.py::normalize_resume" in result.llm_ready_context
    assert "tests/test_resume_pipeline.py::test_warns_on_bad_email" in result.llm_ready_context
    assert any("src/ui/theme.py" in item for item in result.dropped_noise)