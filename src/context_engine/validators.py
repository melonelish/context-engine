from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import FileAccessError, InputSizeError, InputValidationError


MAX_TEXT_CHARS = 200_000
MAX_ITEMS = 64
MAX_FILE_BYTES = 2_000_000


def require_text(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputValidationError(
            error_code="invalid_field",
            message=f"Field '{field_name}' must be a non-empty string.",
            hint=f"Provide a non-empty text value for '{field_name}'.",
        )
    text = value.strip()
    if len(text) > MAX_TEXT_CHARS:
        raise InputSizeError(
            error_code="input_too_large",
            message=f"Field '{field_name}' exceeds the maximum supported size.",
            hint=f"Trim '{field_name}' to under {MAX_TEXT_CHARS} characters before retrying.",
            details={"field": field_name, "max_chars": MAX_TEXT_CHARS, "actual_chars": len(text)},
        )
    return text


def require_list(value: Any, *, field_name: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise InputValidationError(
            error_code="invalid_field",
            message=f"Field '{field_name}' must be a non-empty list.",
            hint=f"Provide at least one item in '{field_name}'.",
        )
    if len(value) > MAX_ITEMS:
        raise InputSizeError(
            error_code="too_many_items",
            message=f"Field '{field_name}' exceeds the maximum supported item count.",
            hint=f"Trim '{field_name}' to {MAX_ITEMS} items or fewer before retrying.",
            details={"field": field_name, "max_items": MAX_ITEMS, "actual_items": len(value)},
        )
    return value


def ensure_file_within_limit(path: Path) -> None:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise FileAccessError(
            error_code="file_access_error",
            message="Could not read the input file.",
            hint="Check that the file exists and is readable.",
            details={"path": str(path), "reason": str(exc)},
        ) from exc

    if size > MAX_FILE_BYTES:
        raise InputSizeError(
            error_code="file_too_large",
            message="Input file exceeds the maximum supported file size.",
            hint=f"Reduce the file to under {MAX_FILE_BYTES} bytes before retrying.",
            details={"path": str(path), "max_bytes": MAX_FILE_BYTES, "actual_bytes": size},
        )


def load_json_file(path: Path) -> dict[str, Any]:
    ensure_file_within_limit(path)
    try:
        import json

        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise InputValidationError(
            error_code="invalid_json",
            message="Input file must contain valid JSON.",
            hint="Check for trailing commas, missing quotes, or malformed brackets.",
            details={"path": str(path), "reason": str(exc)},
        ) from exc
    except OSError as exc:
        raise FileAccessError(
            error_code="file_access_error",
            message="Could not read the input file.",
            hint="Check that the file exists and is readable.",
            details={"path": str(path), "reason": str(exc)},
        ) from exc