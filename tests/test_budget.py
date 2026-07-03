from context_engine.budget import trim_text_to_budget


def test_trim_text_to_budget_adds_marker_when_needed() -> None:
    text = "a" * 100
    trimmed = trim_text_to_budget(text, max_tokens=10)

    assert trimmed.endswith("...[truncated to fit budget]")
    assert len(trimmed) < len(text) + 30