"""Tests del reporter + ApprovalService (TASK-010): BR-61/62/74, mapeo veredicto→reporte."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ratchet.domain import (
    ApprovalDecision,
    ApprovalKind,
    ApprovalRequest,
    EvalStatus,
    GateDecision,
    Patch,
    ReportDecision,
    RunRecord,
    RunState,
)
from ratchet.reporter import (
    ApprovalRequestNotFoundError,
    ApprovalService,
    build_report,
    gate_state,
    map_decision,
)
from tests.factories import (
    make_eval_result,
    make_full_run_record,
    make_gate_verdict,
    make_run_record,
)


def _deploy_approval(decision: ApprovalDecision) -> ApprovalRequest:
    return ApprovalRequest(
        request_id="dep",
        kind=ApprovalKind.APPROVE_DEPLOY,
        proposal_ref="run-full",
        decision=decision,
        decided_by="carolina",
        decided_at=datetime(2026, 7, 5, tzinfo=UTC),
    )


def test_build_report_recomputable_desde_datos_versionados():
    # BR-74: reconstruir el run desde su proyección versionada (persistencia) da el MISMO reporte.
    run = make_full_run_record()
    reconstruido = RunRecord.model_validate(run.model_dump(mode="json"))

    report = build_report(run)

    assert build_report(reconstruido) == report
    assert report.recall_before == run.before.recall_span
    assert report.recall_after == run.after.recall_span
    assert report.delta == run.after.recall_span - run.before.recall_span  # recuperación
    assert report.reproducible_from == run.after.state_ref


def test_build_report_change_desde_patch_y_state_ref_before_si_no_hay_after():
    run = make_full_run_record().model_copy(
        update={
            "patch": Patch(
                patch_id="p1",
                doc_id="niif16",
                new_content="vigente",
                rationale="fuente vieja",
                patch_hash="h",
            ),
            "after": None,
        }
    )

    report = build_report(run)

    assert report.change == "fuente vieja"  # el resumen del cambio viene del patch
    assert report.recall_after is None
    assert report.reproducible_from == run.before.state_ref  # cae a before si no hay after


def test_map_decision_approve_con_after_inconclusa_es_inconclusa():
    # Caso que la tarea señaló: verdict=approve pero after inconclusa ⇒ inconclusa (P1).
    run = make_full_run_record().model_copy(
        update={"after": make_eval_result(status=EvalStatus.INCONCLUSA)}
    )
    assert map_decision(run) is ReportDecision.INCONCLUSA


def test_map_decision_estado_sin_cambio_y_detenida():
    sin_cambio = make_full_run_record().model_copy(update={"state": RunState.SIN_CAMBIO})
    detenida = make_full_run_record().model_copy(update={"state": RunState.DETENIDA_HUMANO})

    assert map_decision(sin_cambio) is ReportDecision.SIN_CAMBIO
    assert map_decision(detenida) is ReportDecision.DETENIDA  # BR-62, no "inconclusa"


def test_map_decision_approve_sin_deploy_es_pending():
    # verdict approve pero sin aprobación humana US-16 ⇒ pending (waiting seguro).
    assert map_decision(make_full_run_record()) is ReportDecision.PENDING


def test_map_decision_approve_con_deploy_aprobado_es_deploy():
    run = make_full_run_record().model_copy(
        update={"approvals": (_deploy_approval(ApprovalDecision.APPROVE),)}
    )
    assert map_decision(run) is ReportDecision.DEPLOY


def test_map_decision_deploy_rechazado_es_revert():
    run = make_full_run_record().model_copy(
        update={"approvals": (_deploy_approval(ApprovalDecision.REJECT),)}
    )
    assert map_decision(run) is ReportDecision.REVERT


def test_map_decision_verdict_revert_es_revert():
    run = make_full_run_record().model_copy(
        update={"verdict": make_gate_verdict(decision=GateDecision.REVERT, ci_delta=(-0.2, -0.1))}
    )
    assert map_decision(run) is ReportDecision.REVERT


def test_map_decision_sin_verdict_es_inconclusa():
    assert map_decision(make_run_record()) is ReportDecision.INCONCLUSA


def test_approval_service_dos_gates_independientes():
    # BR-61: dos gates distintos, con estados independientes.
    service = ApprovalService()
    service.request_approval("us13", ApprovalKind.CONFIRM_PATCH, "patch-1")
    service.request_approval("us16", ApprovalKind.APPROVE_DEPLOY, "run-1")

    service.record_approval(
        "us13", ApprovalDecision.APPROVE, "andres", datetime(2026, 7, 5, tzinfo=UTC)
    )

    assert service.get("us13").decision is ApprovalDecision.APPROVE
    assert service.get("us16").decision is ApprovalDecision.PENDING  # el otro no se afecta


def test_approval_service_errores_y_defaults():
    service = ApprovalService()
    assert service.get("no-existe") is None  # get de id ausente

    with pytest.raises(ApprovalRequestNotFoundError):
        service.record_approval(
            "no-existe", ApprovalDecision.APPROVE, "x", datetime(2026, 7, 5, tzinfo=UTC)
        )

    service.request_approval("us13", ApprovalKind.CONFIRM_PATCH, "patch-1")
    with pytest.raises(ValueError, match="ya solicitado"):
        service.request_approval("us13", ApprovalKind.CONFIRM_PATCH, "patch-1")  # duplicado


def test_gate_state_reject_us13_detiene_humano():
    # BR-62: rechazar el confirm-patch (US-13) ⇒ no se aplica ⇒ DETENIDA_HUMANO.
    assert (
        gate_state(ApprovalKind.CONFIRM_PATCH, ApprovalDecision.REJECT) is RunState.DETENIDA_HUMANO
    )


@pytest.mark.parametrize(
    ("kind", "decision", "expected"),
    [
        (ApprovalKind.CONFIRM_PATCH, ApprovalDecision.PENDING, RunState.ESPERANDO_CONFIRMACION),
        (ApprovalKind.CONFIRM_PATCH, ApprovalDecision.APPROVE, RunState.APLICANDO_PARCHE_REINDEX),
        (ApprovalKind.CONFIRM_PATCH, ApprovalDecision.REJECT, RunState.DETENIDA_HUMANO),
        (ApprovalKind.APPROVE_DEPLOY, ApprovalDecision.PENDING, RunState.ESPERANDO_APROBACION),
        (ApprovalKind.APPROVE_DEPLOY, ApprovalDecision.APPROVE, RunState.PROMOVIDA),
        (ApprovalKind.APPROVE_DEPLOY, ApprovalDecision.REJECT, RunState.RECHAZADA),
    ],
)
def test_gate_state_mapeo_completo(kind, decision, expected):
    assert gate_state(kind, decision) is expected
