"""Tests de la superficie (TASK-012): CLI Typer (3 verbos) + render HTML consola-SRE."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

import ratchet.api.cli as cli_mod
from ratchet.api.html import render_report_html
from ratchet.api.service import ReportService, RunExistsError
from ratchet.domain import Patch
from ratchet.reporter import build_report
from tests.factories import make_full_run_record


def test_cli_flujo_run_approve_report(tmp_path, monkeypatch):
    # NFR-U1-10: disparar → aprobar → leer reporte en 3 comandos, con estado entre procesos.
    monkeypatch.setattr(cli_mod, "_STATE", tmp_path / "state.json")
    runner = CliRunner()

    started = runner.invoke(cli_mod.app, ["run", "--run-id", "run-1"])
    assert started.exit_code == 0 and "esperando-confirmacion" in started.stdout

    c13 = runner.invoke(
        cli_mod.app, ["approve", "run-1", "--kind", "confirm-patch", "--decision", "approve"]
    )
    assert "esperando-aprobacion" in c13.stdout

    c16 = runner.invoke(
        cli_mod.app, ["approve", "run-1", "--kind", "approve-deploy", "--decision", "approve"]
    )
    assert "completada" in c16.stdout

    report = runner.invoke(cli_mod.app, ["report", "run-1"])
    assert report.exit_code == 0 and '"decision": "deploy"' in report.stdout


def test_cli_run_inexistente_falla(tmp_path, monkeypatch):
    monkeypatch.setattr(cli_mod, "_STATE", tmp_path / "state.json")
    result = CliRunner().invoke(cli_mod.app, ["report", "no-existe"])
    assert result.exit_code == 1


def test_render_html_self_contained_y_muestra_datos():
    run = make_full_run_record()
    html = render_report_html(build_report(run), run)

    assert html.lower().startswith("<!doctype html>")
    # Self-contained estructural: sin URLs, fuentes/imports remotos, scripts ni links externos.
    for forbidden in ("http://", "https://", "url(", "@import", "@font-face", "<script", "<link"):
        assert forbidden not in html.lower()
    assert "Ratchet" in html and "Recall" in html
    assert "fuente-vieja" in html and "probe-1" in html  # capa + evidencia G3 visibles
    assert "oklch" in html  # estilos modernos inline


def test_render_html_escapa_contenido_de_usuario():
    # Anti-XSS: un payload en un campo de usuario se neutraliza (escape), no se inyecta.
    run = make_full_run_record().model_copy(
        update={
            "patch": Patch(
                patch_id="p",
                doc_id="d",
                new_content="x",
                rationale="<script>alert('xss')</script>",
                patch_hash="h",
            )
        }
    )
    html = render_report_html(build_report(run), run)

    assert "<script>alert('xss')</script>" not in html  # payload crudo neutralizado
    assert "&lt;script&gt;" in html  # renderizado escapado


def test_start_run_duplicado_falla():
    service = ReportService()
    service.start("run-1")
    with pytest.raises(RunExistsError):  # §P-1: no sobrescribe decisiones humanas
        service.start("run-1")
