from pathlib import Path

from typer.testing import CliRunner

from context_engine.cli import app


runner = CliRunner()


def test_cli_returns_structured_error_for_bad_rag_input(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.json"
    bad_file.write_text('{"question": "why"}', encoding="utf-8")

    result = runner.invoke(app, ["--mode", "rag", "--input", str(bad_file), "--budget", "medium"])

    assert result.exit_code == 2
    assert '"ok": false' in result.stdout.lower()
    assert '"error_code": "invalid_field"' in result.stdout.lower()