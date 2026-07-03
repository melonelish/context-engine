from context_engine.schemas import CompressionRequest, ContextItem, SourceType


def test_request_accepts_request_metadata() -> None:
    request = CompressionRequest(
        mode=SourceType.RAG,
        metadata={"question": "Why did login fail?"},
        items=[ContextItem(source_type=SourceType.RAG, content="Redis pool exhausted")],
    )

    assert request.metadata["question"] == "Why did login fail?"
    assert request.items[0].source_type is SourceType.RAG