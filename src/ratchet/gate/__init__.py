"""C6 gate de no-regresion + revert (determinista, SIN LLM - G2).

Decide SOLO con `EvalResult.per_item` + CI bootstrap pareado (BR-31): aprueba si
`CI.lower(delta_pareado) >= 0` (BR-32) y 0 regresiones criticas (BR-34, guardrail 🔒);
si empeora, revert automatico sin humano (BR-35). NO importa ningun cliente LLM.
"""

from __future__ import annotations

from typing import Protocol

from ratchet.domain import EvalResult, EvalStatus, GateDecision, GateVerdict, PatchHandle
from ratchet.evaluator import DEFAULT_BOOTSTRAP_SAMPLES, DEFAULT_BOOTSTRAP_SEED, BootstrapEstimator


class DataRevertible(Protocol):
    """Superficie minima para revertir un parche de datos (evita acoplar gate→adapter)."""

    def revert_data_patch(self, handle: PatchHandle) -> None: ...


class Gate:
    """Gate de no-regresion determinista. CG-2: el constructor NO acepta ningun `LlmPort`."""

    def __init__(
        self,
        seed: int = DEFAULT_BOOTSTRAP_SEED,
        samples: int = DEFAULT_BOOTSTRAP_SAMPLES,
    ) -> None:
        # Seed fijo por corrida ⇒ CI reproducible (BR-36).
        self._estimator = BootstrapEstimator(seed=seed, samples=samples)

    def evaluate_change(self, candidate: EvalResult, baseline: EvalResult) -> GateVerdict:
        """Delta pareado por `item_id` + CI + guardrail critico ⇒ veredicto determinista."""

        if candidate.golden_set_version != baseline.golden_set_version:
            raise ValueError(
                "gate: candidate y baseline deben compartir golden_set_version (BR-33)"
            )
        if candidate.status is not EvalStatus.OK or baseline.status is not EvalStatus.OK:
            # P1: no se decide con datos inconclusos; el orquestador mantiene el baseline.
            raise ValueError("gate: no decide con evaluaciones inconclusas (P1)")

        base_by_id = {pi.item_id: pi for pi in baseline.per_item}
        cand_by_id = {pi.item_id: pi for pi in candidate.per_item}
        if base_by_id.keys() != cand_by_id.keys():
            # Fail-loud: mismo golden set ⇒ mismo conjunto de item_id. Un ítem que aparece o
            # DESAPARECE podría esconder una regresión crítica (BR-34: 0 no detectadas dentro de
            # cobertura). No se descarta en silencio.
            raise ValueError(
                "gate: candidate y baseline deben cubrir el mismo conjunto de item_id (BR-34)"
            )
        if not base_by_id:
            raise ValueError("gate: sin ítems que evaluar")

        deltas: list[int] = []
        reg_crit = 0
        for item_id in sorted(base_by_id):  # orden estable ⇒ CI reproducible (BR-36)
            base = base_by_id[item_id]
            cand = cand_by_id[item_id]
            deltas.append(int(cand.hit) - int(base.hit))
            # 🔒 BR-34: base_hit=1 ∧ cand_hit=0 sobre clase critica ⇒ regresion critica.
            if base.critical and base.hit and not cand.hit:
                reg_crit += 1

        delta = sum(deltas) / len(deltas)
        ci_delta = self._estimator.ci(deltas)

        # `criterio` refleja la CAUSA real (auditable en el Report BL-10), no un default fijo.
        if reg_crit > 0:
            decision, criterio = GateDecision.REVERT, "reg_crit>0 (🔒)"  # gana sobre el delta
        elif ci_delta[0] >= 0:
            decision, criterio = GateDecision.APPROVE, "CI.lower≥0"  # BR-32
        else:
            decision, criterio = GateDecision.REVERT, "CI.lower<0"

        return GateVerdict(
            decision=decision,
            delta=delta,
            ci_delta=ci_delta,
            criterio=criterio,
            regressions_criticas=reg_crit,
        )

    def revert_if_worse(
        self, rag: DataRevertible, handle: PatchHandle, verdict: GateVerdict
    ) -> bool:
        """Revert automatico si el veredicto es `revert` (BR-35, sin aprobacion humana)."""

        if verdict.decision is GateDecision.REVERT:
            rag.revert_data_patch(handle)
            return True
        return False


__all__ = ["DataRevertible", "Gate"]
