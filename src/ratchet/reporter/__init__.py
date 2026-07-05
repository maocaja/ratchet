"""C8 reporte antes/despues + ApprovalService (gate humano P2).

`build_report` ensambla el `Report` reproducible (BR-74); `map_decision` mapea el veredicto del
gate + la aprobación humana US-16 a la decisión de resultado; `ApprovalService` gestiona los DOS
gates humanos distintos (US-13 confirmar parche, US-16 aprobar deploy — BR-61).
"""

from __future__ import annotations

from datetime import datetime

from ratchet.domain import (
    ApprovalDecision,
    ApprovalKind,
    ApprovalRequest,
    EvalStatus,
    GateDecision,
    Report,
    ReportDecision,
    RunRecord,
    RunState,
)


class ApprovalRequestNotFoundError(RuntimeError):
    """No hay un ApprovalRequest registrado con ese request_id."""


def _find_approval(run: RunRecord, kind: ApprovalKind) -> ApprovalRequest | None:
    return next((a for a in run.approvals if a.kind is kind), None)


def map_decision(run: RunRecord) -> ReportDecision:
    """Estado/veredicto + aprobación humana US-16 ⇒ decisión de resultado (≠ GateVerdict), BL-9."""
    # Estados terminales que NO son post-gate se reportan como su propia decisión (no "inconclusa").
    if run.state is RunState.SIN_CAMBIO:
        return ReportDecision.SIN_CAMBIO  # el monitor no disparó
    if run.state is RunState.DETENIDA_HUMANO:
        return ReportDecision.DETENIDA  # paro humano deliberado (US-13 reject, BR-62)
    if (
        run.state is RunState.INCONCLUSA
        or run.verdict is None
        or (run.after is not None and run.after.status is not EvalStatus.OK)
    ):
        return ReportDecision.INCONCLUSA  # P1: fallo de RAG/entorno o sin veredicto
    if run.verdict.decision is GateDecision.REVERT:
        return ReportDecision.REVERT
    # verdict == approve: el deploy lo decide el humano (US-16).
    deploy = _find_approval(run, ApprovalKind.APPROVE_DEPLOY)
    if deploy is None or deploy.decision is ApprovalDecision.PENDING:
        return ReportDecision.PENDING  # esperando aprobación = waiting seguro
    if deploy.decision is ApprovalDecision.APPROVE:
        return ReportDecision.DEPLOY
    return ReportDecision.REVERT  # deploy rechazado ⇒ revertir a lo seguro


def build_report(run: RunRecord) -> Report:
    """Reporte antes/después reproducible desde datos versionados (BR-74)."""
    state_ref = None
    if run.after is not None:
        state_ref = run.after.state_ref
    elif run.before is not None:
        state_ref = run.before.state_ref
    recall_before = run.before.recall_span if run.before is not None else None
    recall_after = run.after.recall_span if run.after is not None else None
    # delta del reporte = RECUPERACIÓN (after − before), la historia antes/después; el delta del
    # gate (after vs baseline) vive en ci_delta/verdict, distinto eje.
    recovery = (
        recall_after - recall_before
        if recall_before is not None and recall_after is not None
        else (run.verdict.delta if run.verdict is not None else None)
    )
    return Report(
        run_id=run.run_id,
        recall_before=recall_before,
        recall_after=recall_after,
        delta=recovery,
        ci_delta=run.verdict.ci_delta if run.verdict is not None else None,
        change=run.patch.rationale if run.patch is not None else None,
        writeup_id=run.writeup_id,
        decision=map_decision(run),
        reproducible_from=state_ref,
    )


# Mapeo determinista (gate humano, decisión) → RunState resultante (máquina de estados, Parte C).
_GATE_STATE: dict[tuple[ApprovalKind, ApprovalDecision], RunState] = {
    (ApprovalKind.CONFIRM_PATCH, ApprovalDecision.PENDING): RunState.ESPERANDO_CONFIRMACION,
    (ApprovalKind.CONFIRM_PATCH, ApprovalDecision.APPROVE): RunState.APLICANDO_PARCHE_REINDEX,
    (ApprovalKind.CONFIRM_PATCH, ApprovalDecision.REJECT): RunState.DETENIDA_HUMANO,  # BR-62
    (ApprovalKind.APPROVE_DEPLOY, ApprovalDecision.PENDING): RunState.ESPERANDO_APROBACION,
    (ApprovalKind.APPROVE_DEPLOY, ApprovalDecision.APPROVE): RunState.PROMOVIDA,
    (ApprovalKind.APPROVE_DEPLOY, ApprovalDecision.REJECT): RunState.RECHAZADA,
}


def gate_state(kind: ApprovalKind, decision: ApprovalDecision) -> RunState:
    """Estado del run tras un gate humano. `reject` en US-13 ⇒ `DETENIDA_HUMANO` (BR-62)."""
    return _GATE_STATE[(kind, decision)]


class ApprovalService:
    """Gestiona los dos gates humanos distintos (BR-61); `pending` es waiting seguro."""

    def __init__(self) -> None:
        self._requests: dict[str, ApprovalRequest] = {}

    def request_approval(
        self, request_id: str, kind: ApprovalKind, proposal_ref: str
    ) -> ApprovalRequest:
        if request_id in self._requests:  # no sobrescribir silenciosamente el historial
            raise ValueError(f"approval '{request_id}' ya solicitado")
        request = ApprovalRequest(request_id=request_id, kind=kind, proposal_ref=proposal_ref)
        self._requests[request_id] = request  # decision=pending por default
        return request

    def record_approval(
        self,
        request_id: str,
        decision: ApprovalDecision,
        decided_by: str,
        decided_at: datetime,
    ) -> ApprovalRequest:
        request = self._requests.get(request_id)
        if request is None:
            raise ApprovalRequestNotFoundError(f"approval '{request_id}' no registrado")
        recorded = request.model_copy(
            update={"decision": decision, "decided_by": decided_by, "decided_at": decided_at}
        )
        self._requests[request_id] = recorded
        return recorded

    def get(self, request_id: str) -> ApprovalRequest | None:
        return self._requests.get(request_id)


__all__ = [
    "ApprovalRequestNotFoundError",
    "ApprovalService",
    "build_report",
    "gate_state",
    "map_decision",
]
