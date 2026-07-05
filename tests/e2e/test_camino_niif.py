"""e2e Camino NIIF (TASK-013): el Scenario completo, HERMÉTICO (sin ANTHROPIC_API_KEY, sin red).

baseline (corpus vigente) → NIIF 16 vieja (corpus degradado) → monitor detecta la caída →
investigador localiza fuente-vieja → parche de datos → (aprobaciones humanas) → gate recupera →
reporte antes/después. Todo con el SampleRag real (BM25) y el golden set real sembrado del repo.
"""

from __future__ import annotations

import os

from ratchet.api.service import ReportService
from ratchet.domain import (
    ApprovalDecision,
    ApprovalKind,
    Capa,
    Patch,
    ReportDecision,
    RunState,
)

_APPROVE = ApprovalDecision.APPROVE


def test_camino_niif_feliz_a_completada_sin_api_key(monkeypatch):
    # Hermético: el camino NIIF NO necesita la API key del LLM (propiedad de diseño).
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    service = ReportService()

    started = service.start("e2e-niif")
    assert (
        started.state is RunState.ESPERANDO_CONFIRMACION
    )  # monitor disparó, localizó, espera US-13
    assert started.diagnosis is not None and started.diagnosis.capa is Capa.FUENTE_VIEJA
    assert started.diagnosis.verified is True and started.diagnosis.fix_layer.value == "datos"

    service.approve(
        "e2e-niif", ApprovalKind.CONFIRM_PATCH, _APPROVE
    )  # aplica parche + reindex + gate
    run = service.approve("e2e-niif", ApprovalKind.APPROVE_DEPLOY, _APPROVE)
    report = service.report("e2e-niif")

    assert run.state is RunState.COMPLETADA
    assert report.decision is ReportDecision.DEPLOY
    assert report.recall_before < report.recall_after  # recall recuperado (0.86 → 1.00)
    assert report.recall_after == 1.0
    assert "ANTHROPIC_API_KEY" not in os.environ  # corrió sin secreto de red


def test_camino_niif_parche_que_empeora_lo_revierte(monkeypatch):
    # Regresión inyectada: un parche que NO recupera niif16 ⇒ el gate lo atrapa y revierte (🔒).
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    service = ReportService()
    monkeypatch.setattr(
        service,
        "_propose_patch",
        lambda dx, item: Patch(
            patch_id="parche-malo",
            doc_id=item.gold_span.doc_id,
            new_content="contenido roto que no contiene el span vigente",
            rationale="parche que no arregla",
            patch_hash="malo",
        ),
    )

    service.start("e2e-malo")
    run = service.approve("e2e-malo", ApprovalKind.CONFIRM_PATCH, _APPROVE)

    assert run.state is RunState.REVERTIDA  # el gate revirtió antes de llegar al deploy
    assert run.verdict is not None and run.verdict.regressions_criticas >= 1  # 🔒 clase crítica
    assert run.verdict.criterio == "reg_crit>0 (🔒)"  # revirtió POR el 🔒, no por el delta
