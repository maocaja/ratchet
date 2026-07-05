"""Integration de la superficie API (TASK-012): los 3 endpoints + reporte HTML self-contained."""

from __future__ import annotations

from fastapi.testclient import TestClient

from ratchet.api.app import create_app
from ratchet.api.service import ReportService


def _client() -> TestClient:
    return TestClient(create_app(ReportService()))  # servicio in-memory compartido por el test


def test_los_tres_endpoints_y_flujo_completo():
    client = _client()

    started = client.post("/runs", params={"run_id": "run-1"})
    assert started.status_code == 200
    assert started.json()["state"] == "esperando-confirmacion"  # pausa en US-13

    c13 = client.post("/approvals/run-1", params={"kind": "confirm-patch", "decision": "approve"})
    assert c13.status_code == 200 and c13.json()["state"] == "esperando-aprobacion"

    c16 = client.post("/approvals/run-1", params={"kind": "approve-deploy", "decision": "approve"})
    assert c16.json()["state"] == "completada"

    report = client.get("/runs/run-1/report")
    assert report.status_code == 200
    body = report.json()
    assert body["decision"] == "deploy"
    assert body["recall_after"] == 1.0
    assert body["recall_before"] < 1.0  # cayó y se recuperó


def test_reporte_html_es_self_contained():
    client = _client()
    client.post("/runs", params={"run_id": "r"})
    client.post("/approvals/r", params={"kind": "confirm-patch", "decision": "approve"})
    client.post("/approvals/r", params={"kind": "approve-deploy", "decision": "approve"})

    html = client.get("/runs/r/report", params={"format": "html"}).text

    assert "<!doctype html>" in html.lower()
    # Sin assets externos (abrible sin red): ni URLs, ni <script src>, ni <link>.
    assert "http://" not in html and "https://" not in html
    assert "<script" not in html.lower() and "<link" not in html.lower()


def test_run_duplicado_da_409():
    client = _client()
    client.post("/runs", params={"run_id": "dup"})
    assert client.post("/runs", params={"run_id": "dup"}).status_code == 409  # §P-1


def test_run_inexistente_da_404():
    client = _client()
    assert client.get("/runs/nope/report").status_code == 404
    assert (
        client.post(
            "/approvals/nope", params={"kind": "confirm-patch", "decision": "approve"}
        ).status_code
        == 404
    )
