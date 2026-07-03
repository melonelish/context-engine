from context_engine.pipeline import compress_request
from context_engine.schemas import BudgetConfig, CompressionRequest, ContextItem, SourceType


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
    assert "high-signal chunks" in result.summary.lower()
    assert "incident.md" in result.llm_ready_context


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