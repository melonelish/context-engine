from context_engine.errors import ContextEngineError, InputSizeError


def test_error_to_dict_includes_hint() -> None:
    error = ContextEngineError(error_code="invalid_input", message="Bad input", hint="Fix the payload")

    assert error.to_dict() == {
        "error_code": "invalid_input",
        "message": "Bad input",
        "hint": "Fix the payload",
    }


def test_error_to_dict_includes_details() -> None:
    error = InputSizeError(
        error_code="input_too_large",
        message="Too large",
        hint="Trim the input",
        details={"max_chars": 10, "actual_chars": 12},
    )

    assert error.to_dict()["details"]["max_chars"] == 10