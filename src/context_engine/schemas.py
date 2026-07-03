from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SourceType(str, Enum):
    LOGS = "logs"
    RAG = "rag"
    CODE = "code"


class BudgetPreset(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class BudgetConfig(BaseModel):
    preset: BudgetPreset = BudgetPreset.MEDIUM
    max_input_tokens: int | None = None
    max_output_tokens: int | None = None


class ContextItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    source_type: SourceType
    content: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    priority: int = 0
    token_estimate: int | None = None


class CompressionRequest(BaseModel):
    mode: SourceType
    items: list[ContextItem] = Field(min_length=1)
    budget: BudgetConfig = Field(default_factory=BudgetConfig)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompressionResult(BaseModel):
    mode: SourceType
    summary: str
    key_facts: list[str] = Field(default_factory=list)
    dropped_noise: list[str] = Field(default_factory=list)
    llm_ready_context: str
    normalized_items: list[ContextItem] = Field(default_factory=list)
    stats: dict[str, Any] = Field(default_factory=dict)