"""Factories para objetos de dominio (testing.md: factories, no hardcode)."""

from __future__ import annotations

from datetime import UTC, datetime

from ratchet.domain import (
    ApprovalDecision,
    ApprovalKind,
    ApprovalRequest,
    Capa,
    Diagnosis,
    EvalResult,
    EvalStatus,
    FixLayer,
    GateDecision,
    GateVerdict,
    GoldenItem,
    GoldenSet,
    MonitorSignal,
    PerItemResult,
    RunRecord,
    RunState,
    Span,
    StateRef,
)


def make_span(
    doc_id: str = "niif16", start: int = 0, end: int = 10, text: str = "texto dorado"
) -> Span:
    return Span(doc_id=doc_id, start=start, end=end, text=text)


def make_golden_item(
    item_id: str = "it-1",
    question: str = "¿pregunta?",
    answer: str = "respuesta",
    critical: bool = False,
    slice: str | None = "niif16",
    span: Span | None = None,
) -> GoldenItem:
    return GoldenItem(
        item_id=item_id,
        question=question,
        answer=answer,
        gold_span=span or make_span(),
        critical=critical,
        slice=slice,
    )


def make_golden_set(version: str = "gs-v1", n: int = 3) -> GoldenSet:
    items = tuple(make_golden_item(item_id=f"it-{i}", critical=(i == 0)) for i in range(n))
    return GoldenSet(version=version, items=items)


def make_state_ref(
    golden_set_version: str = "gs-v1",
    config_hash: str = "cfg",
    corpus_hash: str = "corpus",
    patch_hash: str | None = None,
    k: int = 5,
    tau: float = 0.8,
) -> StateRef:
    return StateRef(
        golden_set_version=golden_set_version,
        config_hash=config_hash,
        corpus_hash=corpus_hash,
        patch_hash=patch_hash,
        k=k,
        tau=tau,
    )


def make_eval_result(
    recall: float = 0.7,
    per_item: tuple[PerItemResult, ...] | None = None,
    critical_recall: float = 1.0,
    ci: tuple[float, float] = (0.6, 0.8),
    status: EvalStatus = EvalStatus.OK,
) -> EvalResult:
    if per_item is None:
        per_item = (
            PerItemResult(item_id="it-0", hit=True, critical=True),
            PerItemResult(item_id="it-1", hit=True, critical=False),
            PerItemResult(item_id="it-2", hit=False, critical=False),
        )
    return EvalResult(
        golden_set_version="gs-v1",
        recall_span=recall,
        per_item=per_item,
        ci=ci,
        critical_recall=critical_recall,
        state_ref=make_state_ref(),
        status=status,
    )


def make_monitor_signal(
    triggered: bool = True,
    delta: float = 0.1,
    threshold: float = 0.05,
    current: EvalResult | None = None,
) -> MonitorSignal:
    return MonitorSignal(
        triggered=triggered,
        current=current or make_eval_result(),
        baseline_ref="bl-v1",
        delta=delta,
        threshold=threshold,
    )


def make_diagnosis(
    capa: Capa = Capa.FUENTE_VIEJA,
    fix_layer: FixLayer = FixLayer.DATOS,
    verified: bool = True,
) -> Diagnosis:
    return Diagnosis(capa=capa, evidencia=("probe-1",), fix_layer=fix_layer, verified=verified)


def make_gate_verdict(
    decision: GateDecision = GateDecision.APPROVE,
    delta: float = 0.18,
    ci_delta: tuple[float, float] = (0.11, 0.24),
    regressions_criticas: int = 0,
) -> GateVerdict:
    return GateVerdict(
        decision=decision, delta=delta, ci_delta=ci_delta, regressions_criticas=regressions_criticas
    )


def make_run_record(
    run_id: str = "run-1",
    state: RunState = RunState.NUEVA,
    seed: int = 42,
) -> RunRecord:
    return RunRecord(run_id=run_id, state=state, seed=seed)


def make_full_run_record(run_id: str = "run-full") -> RunRecord:
    """RunRecord completamente poblado (estructura anidada + datetime) para probar roundtrip."""
    return RunRecord(
        run_id=run_id,
        state=RunState.GATE,
        seed=42,
        before=make_eval_result(recall=0.6),
        after=make_eval_result(recall=0.8),
        signal=make_monitor_signal(),
        diagnosis=make_diagnosis(),
        verdict=make_gate_verdict(),
        approvals=(
            ApprovalRequest(
                request_id="ap-1",
                kind=ApprovalKind.CONFIRM_PATCH,
                proposal_ref="patch-1",
                decision=ApprovalDecision.APPROVE,
                decided_by="andres",
                decided_at=datetime(2026, 7, 5, 12, 0, 0, tzinfo=UTC),
            ),
        ),
    )
