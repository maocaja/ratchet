"""C9 LoopOrchestrator: ruteo determinista del loop (SIN LLM - G2).

Secuencia medir→localizar→(rama datos)→gate→reportar (BL-9). El orquestador **no llama al LLM**
(G2/CG-2): rutea SOLO sobre datos deterministas (señal del monitor, Diagnosis verificado, veredicto
del gate). Los gates humanos (US-13/US-16) son bordes inyectados (resolvers). En todo terminal
salvo COMPLETADA/PROMOVIDA el baseline queda intacto (BR-75).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from ratchet.domain import (
    ApprovalDecision,
    ApprovalKind,
    ApprovalRequest,
    Baseline,
    DataOpError,
    Diagnosis,
    EvalStatus,
    FixLayer,
    GoldenItem,
    GoldenSet,
    Patch,
    RunRecord,
    RunState,
    RunStatus,
)
from ratchet.evaluator import DEFAULT_BOOTSTRAP_SEED, DEFAULT_K, DEFAULT_TAU, evaluate
from ratchet.gate import Gate
from ratchet.investigator import (
    LayerAmbiguousError,
    Localizer,
    ProbeToolkit,
    UnderspecifiedFixError,
    write_incident,
)
from ratchet.monitor import DEFAULT_DELTA
from ratchet.monitor import check as monitor_check

# Bordes humanos y de propuesta inyectados (frontera de agencia — el core no los implementa).
# El RAG (`rag`) es duck-typed: el loop usa retrieve/generate/get_config/corpus_fingerprint +
# apply_data_patch/reindex/revert_data_patch; el adaptador concreto los provee (P5).
ConfirmPatch = Callable[[Patch], ApprovalDecision]  # US-13
ApproveDeploy = Callable[[RunRecord], ApprovalDecision]  # US-16
ProposePatch = Callable[[Diagnosis, GoldenItem], Patch]
Clock = Callable[[], datetime]


class LoopOrchestrator:
    """Rutea el loop determinista. CG-2: el constructor NO acepta ningún `LlmPort`."""

    def __init__(
        self,
        *,
        delta: float = DEFAULT_DELTA,
        k: int = DEFAULT_K,
        tau: float = DEFAULT_TAU,
        seed: int = DEFAULT_BOOTSTRAP_SEED,
        gate: Gate | None = None,
    ) -> None:
        self._delta = delta
        self._k = k
        self._tau = tau
        self._seed = seed
        self._gate = gate or Gate(seed=seed)

    def run_loop(
        self,
        rag: object,
        baseline: Baseline,
        golden_set: GoldenSet,
        *,
        confirm_patch: ConfirmPatch,
        approve_deploy: ApproveDeploy,
        propose_patch: ProposePatch,
        now: Clock,
        run_id: str = "run-1",
    ) -> RunRecord:
        run = RunRecord(run_id=run_id, state=RunState.NUEVA, seed=self._seed)

        # 1. Monitorear: ¿cayó el recall vs baseline? (BL-5)
        signal = monitor_check(
            rag, baseline, golden_set, delta=self._delta, k=self._k, tau=self._tau, seed=self._seed
        )
        run = run.model_copy(update={"signal": signal, "state": RunState.MONITOREANDO})
        if not signal.triggered:
            return _terminal(run, RunState.SIN_CAMBIO)  # baseline intacto (BR-75)

        # 2. Investigar: elegir el ítem que REGRESIONÓ (base hit → current miss), no un miss
        # crónico; localizar la capa y verificar (BL-6, G3). Se emparea por item_id, no por orden.
        run = run.model_copy(update={"before": signal.current, "state": RunState.INVESTIGANDO})
        base_by_id = {pi.item_id: pi for pi in baseline.eval_result.per_item}
        cur_by_id = {pi.item_id: pi for pi in signal.current.per_item}

        def _missed(it: GoldenItem) -> bool:
            per = cur_by_id.get(it.item_id)
            return per is not None and not per.hit

        def _regressed(it: GoldenItem) -> bool:
            base = base_by_id.get(it.item_id)
            return base is not None and base.hit and _missed(it)

        candidates = [it for it in golden_set.items if _regressed(it)] or [
            it for it in golden_set.items if _missed(it)
        ]
        if not candidates:
            return _terminal(run, RunState.INCONCLUSA)
        item = candidates[0]
        try:
            dx = Localizer(ProbeToolkit(rag, k=self._k)).localize(item)
        except (LayerAmbiguousError, UnderspecifiedFixError):
            # Sondas no concluyen y sin LLM (U1 hermético) → inconclusa, baseline intacto (P1).
            return _terminal(run, RunState.INCONCLUSA)
        if not dx.verified:
            return _terminal(run, RunState.INCONCLUSA, diagnosis=dx)  # baseline intacto (P1)

        writeup = write_incident(dx, item, signal)
        run = run.model_copy(
            update={
                "diagnosis": dx,
                "writeup_id": writeup.writeup_id,
                "state": RunState.WRITEUP_LISTO,
            }
        )

        # 3. Rutear sobre la capa verificada (BR-72). U1 = solo rama datos.
        if dx.fix_layer is not FixLayer.DATOS:
            return _terminal(run, RunState.INCONCLUSA)  # config = U2, fuera de alcance
        if not rag.supports_data_ops():
            return _terminal(run, RunState.INCONCLUSA)  # BR-63/G1: rama de datos no disponible

        # 4. Proponer parche + gate humano US-13 (confirmar parche de datos, BR-62)
        patch = propose_patch(dx, item)
        run = run.model_copy(update={"patch": patch, "state": RunState.ESPERANDO_CONFIRMACION})
        decision13 = confirm_patch(patch)
        run = _with_approval(run, ApprovalKind.CONFIRM_PATCH, patch.patch_id, decision13, now)
        if decision13 is ApprovalDecision.PENDING:
            return run  # pausa (no terminal) — espera confirmación humana
        if decision13 is ApprovalDecision.REJECT:
            return _terminal(run, RunState.DETENIDA_HUMANO)  # BR-62, baseline intacto

        # 5. Aplicar parche + reindex (atómico: si reindex falla → revert + inconclusa, BR-65)
        run = run.model_copy(update={"state": RunState.APLICANDO_PARCHE_REINDEX})
        try:
            handle = rag.apply_data_patch(patch)
        except DataOpError:
            # BR-65: apply_data_patch revierte solo si reindex falla; el baseline queda intacto.
            return _terminal(run, RunState.INCONCLUSA)
        run = run.model_copy(update={"patch_handle": handle})

        # 6. Re-evaluar con el parche aplicado (BL-1)
        run = run.model_copy(update={"state": RunState.EVALUANDO_AFTER})
        after = evaluate(rag, golden_set, k=self._k, tau=self._tau, seed=self._seed)
        run = run.model_copy(update={"after": after})
        if after.status is not EvalStatus.OK:
            rag.revert_data_patch(handle)
            return _terminal(run, RunState.INCONCLUSA)  # baseline intacto (P1)

        # 7. Gate de no-regresión + revert automático si empeora (BL-4, BR-75)
        run = run.model_copy(update={"state": RunState.GATE})
        verdict = self._gate.evaluate_change(after, baseline.eval_result)
        run = run.model_copy(update={"verdict": verdict})
        if self._gate.revert_if_worse(rag, handle, verdict):
            return _terminal(run, RunState.REVERTIDA)  # baseline intacto (BR-75)

        # 8. Gate humano US-16 (aprobar deploy)
        run = run.model_copy(update={"state": RunState.ESPERANDO_APROBACION})
        decision16 = approve_deploy(run)
        run = _with_approval(run, ApprovalKind.APPROVE_DEPLOY, run_id, decision16, now)
        if decision16 is ApprovalDecision.PENDING:
            return run  # pausa — espera aprobación humana
        if decision16 is ApprovalDecision.REJECT:
            rag.revert_data_patch(handle)
            return _terminal(run, RunState.RECHAZADA)  # revertir a lo seguro; baseline intacto

        # 9. Promover: el parche se queda; recall recuperado (BL-9)
        run = run.model_copy(update={"state": RunState.PROMOVIDA})
        return _terminal(run, RunState.COMPLETADA)


def _terminal(run: RunRecord, state: RunState, **updates: object) -> RunRecord:
    # Rollup grueso (RunStatus) además del estado fino: inconclusa vs concluida (BL-9/BL-10).
    status = RunStatus.INCONCLUSA if state is RunState.INCONCLUSA else RunStatus.COMPLETADA
    return run.model_copy(update={"state": state, "status": status, **updates})


def _with_approval(
    run: RunRecord, kind: ApprovalKind, proposal_ref: str, decision: ApprovalDecision, now: Clock
) -> RunRecord:
    request = ApprovalRequest(
        request_id=f"{run.run_id}:{kind.value}",
        kind=kind,
        proposal_ref=proposal_ref,
        decision=decision,
        decided_by="operador" if decision is not ApprovalDecision.PENDING else None,
        decided_at=now() if decision is not ApprovalDecision.PENDING else None,
    )
    return run.model_copy(update={"approvals": (*run.approvals, request)})


__all__ = ["LoopOrchestrator"]
