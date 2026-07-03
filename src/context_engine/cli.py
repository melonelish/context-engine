from __future__ import annotations

import json
from pathlib import Path

import typer

from .api import compress_from_inputs
from .errors import ContextEngineError
from .schemas import BudgetPreset, SourceType


app = typer.Typer(add_completion=False, help="Compress logs, rag chunks, or code context into structured output.")


@app.callback(invoke_without_command=True)
def main(
    mode: SourceType = typer.Option(SourceType.LOGS, help="Compression mode: logs, rag, or code."),
    input: Path = typer.Option(..., exists=True, dir_okay=False, readable=True, help="Path to the input file."),
    budget: BudgetPreset = typer.Option(BudgetPreset.MEDIUM, help="Output budget preset."),
    pretty: bool = typer.Option(True, help="Pretty-print JSON output."),
) -> None:
    try:
        payload = compress_from_inputs(mode=mode, path=input, budget=budget)
    except ContextEngineError as exc:
        typer.echo(json.dumps({"ok": False, "error": exc.to_dict()}, ensure_ascii=True, indent=2 if pretty else None))
        raise typer.Exit(code=2)

    typer.echo(json.dumps({"ok": True, "result": payload}, ensure_ascii=True, indent=2 if pretty else None))


if __name__ == "__main__":
    app()