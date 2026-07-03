from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ContextEngineError(Exception):
    error_code: str
    message: str
    hint: str | None = None
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "error_code": self.error_code,
            "message": self.message,
        }
        if self.hint:
            payload["hint"] = self.hint
        if self.details:
            payload["details"] = self.details
        return payload


class InputValidationError(ContextEngineError):
    pass


class UnsupportedModeError(ContextEngineError):
    pass


class InputSizeError(ContextEngineError):
    pass


class FileAccessError(ContextEngineError):
    pass