"""Tests de tipos de dominio (TASK-002): happy, error y edge + PBT.

Cubre las validaciones básicas; la lógica de negocio se testea en sus módulos.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from ratchet.domain import (
    TERMINAL_STATES,
    ApprovalKind,
    ApprovalRequest,
    Baseline,
    Capa,
    Diagnosis,
    EvalResult,
    EvalStatus,
    FixLayer,
    GateDecision,
    GateVerdict,
    GoldenItem,
    GoldenSet,
    Patch,
    PerItemResult,
    Report,
    ReportDecision,
    RunState,
    Span,
    Writeup,
)
from tests.factories import (
    make_eval_result,
    make_gate_verdict,
    make_golden_set,
    make_monitor_signal,
    make_run_record,
    make_span,
    make_state_ref,
)

# ── Span (Value Object) ──────────────────────────────────────────────────────


def test_span_happy_len_positivo():
    span = make_span(start=3, end=10)
    assert span.length == 7


@pytest.mark.parametrize("start,end", [(5, 5), (10, 3), (0, 0)])
def test_span_rechaza_len_no_positivo(start, end):
    with pytest.raises(ValidationError):
        make_span(start=start, end=end)


def test_span_rechaza_offset_negativo():
    with pytest.raises(ValidationError):
        Span(doc_id="d", start=-1, end=5, text="x")


def test_span_es_inmutable():
    span = make_span()
    with pytest.raises(ValidationError):
        span.start = 99  # frozen VO


# ── Diagnosis / enums ────────────────────────────────────────────────────────


def test_diagnosis_capa_valida():
    dx = Diagnosis(
        capa=Capa.FUENTE_VIEJA, evidencia=("p1",), fix_layer=FixLayer.DATOS, verified=True
    )
    assert dx.capa is Capa.FUENTE_VIEJA


def test_diagnosis_rechaza_capa_fuera_del_enum():
    with pytest.raises(ValidationError):
        Diagnosis(capa="capa-inventada", evidencia=(), fix_layer=FixLayer.DATOS)


def test_gate_verdict_rechaza_decision_invalida():

    with pytest.raises(ValidationError):
        GateVerdict(decision="quizas", delta=0.0, ci_delta=(0.0, 0.0))


# ── EvalResult / rangos ──────────────────────────────────────────────────────


def test_eval_result_recall_en_rango():
    ev = make_eval_result(recall=0.7)
    assert 0.0 <= ev.recall_span <= 1.0
    assert len(ev.per_item) == 3


@pytest.mark.parametrize("recall", [-0.1, 1.5])
def test_eval_result_rechaza_recall_fuera_de_rango(recall):
    with pytest.raises(ValidationError):
        make_eval_result(recall=recall)


# ── StateRef / clave de estado ───────────────────────────────────────────────


def test_state_ref_key_incluye_eval_params_no_seed():
    ref = make_state_ref(k=5, tau=0.8)
    key = ref.key()
    assert key == ("gs-v1", "cfg", "corpus", None, (5, 0.8))


def test_state_ref_distinto_k_da_distinta_key():
    # dos corridas con distinto k NO deben deduplicarse (BR-73)
    assert make_state_ref(k=5).key() != make_state_ref(k=10).key()


def test_state_ref_rechaza_tau_fuera_de_rango():
    with pytest.raises(ValidationError):
        make_state_ref(tau=1.5)


# ── GoldenSet / Aggregate ────────────────────────────────────────────────────


def test_golden_set_tiene_items_y_critico():
    gs = make_golden_set(n=3)
    assert len(gs.items) == 3
    assert any(it.critical for it in gs.items)


def test_golden_set_rechaza_item_id_duplicado():
    item = make_golden_set(n=1).items[0]
    with pytest.raises(ValidationError):
        GoldenSet(version="gs-dup", items=(item, item))


# ── GateVerdict: invariante del guardrail 🔒 (BR-34) ─────────────────────────


def test_gate_verdict_revert_con_regresion_critica_ok():
    v = make_gate_verdict(
        decision=GateDecision.REVERT, regressions_criticas=2, ci_delta=(-0.1, 0.1)
    )
    assert v.regressions_criticas == 2


def test_gate_verdict_rechaza_approve_con_regresion_critica():
    # regresión inyectada: aprobar con regresión crítica es imposible (🔒)
    with pytest.raises(ValidationError):
        make_gate_verdict(decision=GateDecision.APPROVE, regressions_criticas=1)


def test_gate_verdict_rechaza_approve_con_ci_lower_negativo():
    with pytest.raises(ValidationError):
        make_gate_verdict(decision=GateDecision.APPROVE, ci_delta=(-0.05, 0.2))


# ── EvalResult: per_item pareable por item_id (BR-33/34) ─────────────────────


def test_eval_result_rechaza_item_id_duplicado():
    dup = (
        PerItemResult(item_id="it-1", hit=True, critical=False),
        PerItemResult(item_id="it-1", hit=False, critical=True),
    )
    with pytest.raises(ValidationError):
        make_eval_result(per_item=dup)


def test_eval_result_k_tau_tienen_default():
    ev = EvalResult(golden_set_version="gs", recall_span=0.7, ci=(0.6, 0.8), critical_recall=1.0)
    assert ev.k == 5
    assert ev.tau == 0.8


# ── RunState: máquina de estados fina ────────────────────────────────────────


def test_run_record_default_state_nueva():
    run = make_run_record()
    assert run.state is RunState.NUEVA


def test_run_state_terminales_definidos():
    assert RunState.COMPLETADA in TERMINAL_STATES
    assert RunState.REVERTIDA in TERMINAL_STATES
    # PROMOVIDA NO es terminal (avanza a REPORTE → COMPLETADA)
    assert RunState.PROMOVIDA not in TERMINAL_STATES
    assert RunState.EVALUANDO_BEFORE not in TERMINAL_STATES


def test_run_record_rechaza_state_invalido():
    with pytest.raises(ValidationError):
        make_run_record(state="volando")


# ── Inmutabilidad de entidades que el spec exige congeladas ──────────────────


def test_golden_set_es_inmutable():
    gs = make_golden_set()
    with pytest.raises(ValidationError):
        gs.version = "otra"


def test_writeup_es_inmutable():
    wu = Writeup(
        writeup_id="w-1",
        sintoma="s",
        capa_localizada=Capa.FUENTE_VIEJA,
        evidencia=("p1",),
        fix_prescrito="reemplazar doc",
        conclusion="→ datos",
    )
    with pytest.raises(ValidationError):
        wu.conclusion = "otra"


def test_baseline_es_inmutable():
    bl = Baseline(version="b-1", eval_result=make_eval_result())
    with pytest.raises(ValidationError):
        bl.version = "b-2"


# ── MonitorSignal: invariante inconclusa (BR-43) ─────────────────────────────


def test_monitor_signal_happy_dispara():
    sig = make_monitor_signal(triggered=True)
    assert sig.triggered is True


def test_monitor_signal_inconclusa_no_puede_disparar():
    inconclusa = make_eval_result(status=EvalStatus.INCONCLUSA)
    with pytest.raises(ValidationError):
        make_monitor_signal(triggered=True, current=inconclusa)


def test_monitor_signal_inconclusa_sin_disparo_ok():
    inconclusa = make_eval_result(status=EvalStatus.INCONCLUSA)
    sig = make_monitor_signal(triggered=False, current=inconclusa)
    assert sig.triggered is False


# ── GateVerdict: caso límite CI.lower == 0 (Q3: "CI.lower ≥ 0") ───────────────


def test_gate_verdict_approve_con_ci_lower_cero_es_valido():
    # límite: ci_delta.lower == 0 debe PERMITIR approve (chequeo es < 0 estricto)
    v = make_gate_verdict(decision=GateDecision.APPROVE, ci_delta=(0.0, 0.2))
    assert v.decision is GateDecision.APPROVE


# ── GoldenItem inmutable (la verdad, no mutante — BR-76) ──────────────────────


def test_golden_item_es_inmutable():
    it = make_golden_set(n=1).items[0]
    assert isinstance(it, GoldenItem)
    with pytest.raises(ValidationError):
        it.answer = "otra"


# ── Cobertura de tipos con enum/defaults (simetría) ──────────────────────────


def test_report_rechaza_decision_fuera_del_enum():
    with pytest.raises(ValidationError):
        Report(run_id="r-1", decision="quiza")


def test_report_decision_valida():
    rep = Report(run_id="r-1", decision=ReportDecision.DEPLOY)
    assert rep.decision is ReportDecision.DEPLOY


def test_approval_request_default_pending_y_kind_enum():
    ar = ApprovalRequest(request_id="a-1", kind=ApprovalKind.CONFIRM_PATCH, proposal_ref="patch-1")
    assert ar.decision.value == "pending"
    with pytest.raises(ValidationError):
        ApprovalRequest(request_id="a-2", kind="cualquiera", proposal_ref="x")


def test_patch_construye():
    p = Patch(patch_id="p-1", doc_id="niif16", new_content="vigente", rationale="r", patch_hash="h")
    assert p.doc_id == "niif16"


# ── PBT: invariante del Span ─────────────────────────────────────────────────


@given(
    start=st.integers(min_value=0, max_value=10_000),
    delta=st.integers(min_value=1, max_value=10_000),
)
def test_pbt_span_length_siempre_positivo(start: int, delta: int):
    span = Span(doc_id="d", start=start, end=start + delta, text="x" * delta)
    assert span.length == delta
    assert span.length > 0
