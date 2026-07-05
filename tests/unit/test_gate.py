"""Tests del gate de no-regresion (TASK-004): 🔒 BR-31..37, CG-2."""

from __future__ import annotations

import inspect

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ratchet.domain import EvalResult, EvalStatus, GateDecision, PatchHandle, PerItemResult
from ratchet.gate import Gate
from tests.factories import make_gate_verdict


def make_eval(
    specs: list[tuple[str, bool, bool]],
    version: str = "gs-v1",
    status: EvalStatus = EvalStatus.OK,
) -> EvalResult:
    """EvalResult desde `(item_id, hit, critical)` con recall/crit recomputados."""
    per_item = tuple(PerItemResult(item_id=i, hit=h, critical=c) for i, h, c in specs)
    hits = [pi.hit for pi in per_item]
    crit = [pi.hit for pi in per_item if pi.critical]
    return EvalResult(
        golden_set_version=version,
        recall_span=sum(hits) / len(hits) if hits else 0.0,
        per_item=per_item,
        ci=(0.0, 1.0),
        critical_recall=sum(crit) / len(crit) if crit else 0.0,
        status=status,
    )


class SpyRag:
    def __init__(self) -> None:
        self.reverted: list[PatchHandle] = []

    def revert_data_patch(self, handle: PatchHandle) -> None:
        self.reverted.append(handle)


def test_gate_aprueba_cuando_mejora_con_ci_que_excluye_cero():
    base = make_eval([(f"it-{i}", False, i == 0) for i in range(20)])
    cand = make_eval([(f"it-{i}", True, i == 0) for i in range(20)])

    verdict = Gate().evaluate_change(cand, base)

    assert verdict.decision is GateDecision.APPROVE
    assert verdict.ci_delta[0] >= 0
    assert verdict.regressions_criticas == 0
    assert verdict.delta == 1.0
    assert verdict.criterio == "CI.lower≥0"


def test_gate_revierte_cuando_baja_recall_agregado():
    # Regresion inyectada (a): parche que baja el recall agregado (no-criticos) → revert.
    base = make_eval([(f"it-{i}", True, False) for i in range(20)])
    cand = make_eval([(f"it-{i}", False, False) for i in range(20)])

    verdict = Gate().evaluate_change(cand, base)

    assert verdict.decision is GateDecision.REVERT
    assert verdict.ci_delta[1] <= 0
    assert verdict.regressions_criticas == 0  # revert por delta, no por el 🔒


def test_gate_revierte_por_regresion_critica_aunque_agregado_no_baje():
    # Regresion inyectada (b) 🔒: rompe un item critico SIN bajar el agregado → revert igual.
    base = make_eval([("crit", True, True), ("comp", False, False)])
    cand = make_eval([("crit", False, True), ("comp", True, False)])

    verdict = Gate().evaluate_change(cand, base)

    assert verdict.regressions_criticas == 1
    assert verdict.decision is GateDecision.REVERT
    assert verdict.delta == 0.0  # el agregado no cambia; el 🔒 es quien fuerza el revert
    assert verdict.criterio == "reg_crit>0 (🔒)"  # el reporte refleja la causa real


def test_gate_exige_misma_golden_set_version():
    base = make_eval([("it-0", True, False)], version="gs-v1")
    cand = make_eval([("it-0", True, False)], version="gs-v2")

    with pytest.raises(ValueError, match="golden_set_version"):
        Gate().evaluate_change(cand, base)


def test_gate_conjuntos_de_items_distintos_fallan():
    base = make_eval([("a", True, False)])
    cand = make_eval([("b", True, False)])

    with pytest.raises(ValueError, match="mismo conjunto de item_id"):
        Gate().evaluate_change(cand, base)


def test_gate_item_critico_desaparecido_no_se_ignora_en_silencio():
    # 🔒 BR-34: si un ítem crítico con base_hit=1 DESAPARECE del candidate, NO debe descartarse
    # en silencio (sería una regresión no detectada dentro de cobertura). El gate falla ruidoso.
    base = make_eval([("a", True, False), ("crit", True, True)])
    cand = make_eval([("a", True, False)])  # "crit" desapareció

    with pytest.raises(ValueError, match="mismo conjunto de item_id"):
        Gate().evaluate_change(cand, base)


def test_gate_no_decide_con_evaluacion_inconclusa():
    # P1: una re-evaluación inconclusa no habilita approve; el gate no decide.
    base = make_eval([("a", True, False)])
    cand = make_eval([], status=EvalStatus.INCONCLUSA)

    with pytest.raises(ValueError, match="inconclusas"):
        Gate().evaluate_change(cand, base)


def test_gate_constructor_no_acepta_llmport():
    # CG-2: import-linter no atrapa la inyeccion por constructor; se testea explicito.
    for param in inspect.signature(Gate.__init__).parameters.values():
        assert "llm" not in param.name.lower()
        assert "Llm" not in str(param.annotation)
    for method in (Gate.evaluate_change, Gate.revert_if_worse):
        for param in inspect.signature(method).parameters.values():
            assert "Llm" not in str(param.annotation)


def test_revert_if_worse_revierte_solo_en_revert_sin_humano():
    handle = PatchHandle(handle_id="h1", patch_id="p1", prev_snapshot="")
    gate = Gate()

    spy_revert = SpyRag()
    reverted = gate.revert_if_worse(
        spy_revert, handle, make_gate_verdict(decision=GateDecision.REVERT, ci_delta=(-0.2, 0.0))
    )
    assert reverted is True
    assert spy_revert.reverted == [handle]

    spy_approve = SpyRag()
    reverted = gate.revert_if_worse(spy_approve, handle, make_gate_verdict())  # approve por default
    assert reverted is False
    assert spy_approve.reverted == []


def test_gate_ci_reproducible_con_misma_seed():
    base = make_eval([(f"it-{i}", i % 2 == 0, False) for i in range(10)])
    cand = make_eval([(f"it-{i}", True, False) for i in range(10)])

    first = Gate(seed=7).evaluate_change(cand, base)
    second = Gate(seed=7).evaluate_change(cand, base)

    assert first.ci_delta == second.ci_delta


@given(
    specs=st.lists(
        st.tuples(st.booleans(), st.booleans(), st.booleans()),
        min_size=1,
        max_size=20,
    )
)
def test_pbt_verdict_respeta_invariantes(specs):
    base = make_eval([(f"it-{i}", b, c) for i, (b, _cd, c) in enumerate(specs)])
    cand = make_eval([(f"it-{i}", cd, c) for i, (_b, cd, c) in enumerate(specs)])

    verdict = Gate(samples=100).evaluate_change(cand, base)

    reg = sum(1 for b, cd, c in specs if c and b and not cd)
    assert verdict.regressions_criticas == reg
    if reg > 0:
        assert verdict.decision is GateDecision.REVERT
    if verdict.decision is GateDecision.APPROVE:
        assert verdict.ci_delta[0] >= 0
        assert verdict.regressions_criticas == 0
