"""CLI Typer: `ratchet run | approve | report` — espejo de la API (C10).

`trigger → aprobar → leer reporte` en 3 comandos (NFR-U1-10). El estado (decisiones) se
persiste en `~/.ratchet/state.json` para que los comandos funcionen entre procesos.
"""

from __future__ import annotations

from pathlib import Path

import typer

from ratchet.api.html import render_report_html
from ratchet.api.service import ReportService, RunNotFoundError
from ratchet.domain import ApprovalDecision, ApprovalKind

app = typer.Typer(help="Ratchet · el SRE de guardia del conocimiento de un RAG.")

_STATE = Path.home() / ".ratchet" / "state.json"


def _service() -> ReportService:
    _STATE.parent.mkdir(parents=True, exist_ok=True)
    return ReportService(state_path=_STATE)


@app.command()
def run(run_id: str = "run-1") -> None:
    """Dispara una corrida del loop (se pausa en el primer gate humano)."""
    record = _service().start(run_id)
    typer.echo(f"{record.run_id}: {record.state.value}")


@app.command()
def approve(
    run_id: str,
    kind: str = typer.Option(
        "confirm-patch", help="confirm-patch (US-13) | approve-deploy (US-16)"
    ),
    decision: str = typer.Option("approve", help="approve | reject | pending"),
) -> None:
    """Registra una decisión humana y reanuda el loop."""
    try:
        record = _service().approve(run_id, ApprovalKind(kind), ApprovalDecision(decision))
    except RunNotFoundError:
        typer.secho(f"run {run_id} no encontrado", fg="red", err=True)
        raise typer.Exit(1) from None
    typer.echo(f"{record.run_id}: {record.state.value}")


@app.command()
def report(
    run_id: str,
    html: bool = typer.Option(False, help="Emitir el reporte HTML self-contained."),
    out: str = typer.Option("", help="Escribir el HTML a un archivo en vez de stdout."),
) -> None:
    """Muestra el reporte antes/después (JSON, o HTML consola-SRE con --html)."""
    service = _service()
    try:
        record = service.get_run(run_id)
    except RunNotFoundError:
        typer.secho(f"run {run_id} no encontrado", fg="red", err=True)
        raise typer.Exit(1) from None
    projected = service.report(run_id)
    if not html:
        typer.echo(projected.model_dump_json(indent=2))
        return
    content = render_report_html(projected, record)
    if out:
        Path(out).write_text(content, encoding="utf-8")
        typer.echo(f"HTML → {out}")
    else:
        typer.echo(content)


if __name__ == "__main__":
    app()
