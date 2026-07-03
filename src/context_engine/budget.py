from __future__ import annotations

from .schemas import BudgetConfig, BudgetPreset, ContextItem


PRESET_OUTPUT_TOKENS: dict[BudgetPreset, int] = {
    BudgetPreset.SMALL: 220,
    BudgetPreset.MEDIUM: 420,
    BudgetPreset.LARGE: 800,
}

PRESET_INPUT_TOKENS: dict[BudgetPreset, int] = {
    BudgetPreset.SMALL: 1000,
    BudgetPreset.MEDIUM: 2200,
    BudgetPreset.LARGE: 4000,
}


def estimate_tokens(text: str) -> int:
    stripped = text.strip()
    if not stripped:
        return 0
    return max(1, (len(stripped) + 3) // 4)


def resolve_input_budget(budget: BudgetConfig) -> int:
    if budget.max_input_tokens is not None:
        return budget.max_input_tokens
    return PRESET_INPUT_TOKENS[budget.preset]


def resolve_output_budget(budget: BudgetConfig) -> int:
    if budget.max_output_tokens is not None:
        return budget.max_output_tokens
    return PRESET_OUTPUT_TOKENS[budget.preset]


def sort_and_trim_items(items: list[ContextItem], max_tokens: int) -> tuple[list[ContextItem], list[ContextItem]]:
    annotated = list(enumerate(items))
    ordered = sorted(
        annotated,
        key=lambda pair: (-pair[1].priority, pair[0]),
    )
    kept: list[tuple[int, ContextItem]] = []
    dropped: list[ContextItem] = []
    total = 0

    for index, item in ordered:
        size = item.token_estimate or estimate_tokens(item.content)
        if kept and total + size > max_tokens:
            dropped.append(item)
            continue
        total += size
        kept.append((index, item))

    kept.sort(key=lambda pair: pair[0])
    return [item for _, item in kept], dropped


def trim_text_to_budget(text: str, max_tokens: int) -> str:
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    clipped = text[:max_chars].rstrip()
    return clipped + "\n...[truncated to fit budget]"
