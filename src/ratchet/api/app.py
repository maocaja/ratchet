"""FastAPI: los 3 verbos del demo (run / approve / report) — C10, espejo del CLI.

Nota de alcance (U1 hermético, NFR-U1-8 sin authn): el servicio es in-process, single-operador;
el estado mutable no lleva lock — correcto para el demo, se endurece (cola/BD) en el escalado.
"""

from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from ratchet.api.html import render_report_html
from ratchet.api.service import ReportService, RunExistsError, RunNotFoundError
from ratchet.domain import ApprovalDecision, ApprovalKind, RunRecord


def _view(run: RunRecord) -> dict:
    """Vista del run que muestra QUÉ se va a confirmar (diagnóstico + parche) — NFR-U1-10."""
    view: dict = {"run_id": run.run_id, "state": run.state.value}
    if run.diagnosis is not None:
        view["diagnosis"] = {
            "capa": run.diagnosis.capa.value,
            "fix_layer": run.diagnosis.fix_layer.value,
            "evidencia": list(run.diagnosis.evidencia),
        }
    if run.patch is not None:
        view["proposed_change"] = run.patch.rationale
    return view


def create_app(service: ReportService | None = None) -> FastAPI:
    svc = service if service is not None else ReportService()
    app = FastAPI(title="Ratchet · knowledge on-call")

    @app.post("/runs")
    def create_run(run_id: str = "run-1") -> dict:
        try:
            return _view(svc.start(run_id))
        except RunExistsError as exc:
            raise HTTPException(status_code=409, detail=f"run {run_id} ya existe") from exc

    @app.post("/approvals/{run_id}")
    def approve(run_id: str, kind: ApprovalKind, decision: ApprovalDecision) -> dict:
        try:
            return _view(svc.approve(run_id, kind, decision))
        except RunNotFoundError as exc:
            raise HTTPException(status_code=404, detail=f"run {run_id} no encontrado") from exc

    @app.get("/runs/{run_id}/report")
    def get_report(
        run_id: str, fmt: Literal["json", "html"] = Query(default="json", alias="format")
    ):
        try:
            run = svc.get_run(run_id)
        except RunNotFoundError as exc:
            raise HTTPException(status_code=404, detail=f"run {run_id} no encontrado") from exc
        report = svc.report(run_id)
        if fmt == "html":
            return HTMLResponse(render_report_html(report, run))
        return report.model_dump(mode="json")

    return app


app = create_app()  # para `uvicorn ratchet.api.app:app`
