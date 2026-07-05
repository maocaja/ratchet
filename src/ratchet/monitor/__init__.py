"""C7 detecta caidas vs baseline y dispara el loop.

`check` re-evalúa el RAG contra la MISMA versión del golden set del baseline (BR-42) y dispara
si el recall cae ≥ δ (default 0.05, BR-41). Una corrida inconclusa NO dispara (BR-43/P1).
La clasificación fina del origen (own-deploy vs env-drift) es de U3 → `source="unknown"`.
"""

from __future__ import annotations

from ratchet.domain import Baseline, EvalStatus, GoldenSet, MonitorSignal, MonitorSource
from ratchet.evaluator import (
    DEFAULT_BOOTSTRAP_SEED,
    DEFAULT_K,
    DEFAULT_TAU,
    RagPatientPort,
    evaluate,
)

DEFAULT_DELTA = 0.05


def check(
    rag: RagPatientPort,
    baseline: Baseline,
    golden_set: GoldenSet,
    *,
    delta: float = DEFAULT_DELTA,
    k: int = DEFAULT_K,
    tau: float = DEFAULT_TAU,
    seed: int = DEFAULT_BOOTSTRAP_SEED,
    source: MonitorSource = MonitorSource.UNKNOWN,
) -> MonitorSignal:
    """Re-evalúa y dispara si el recall cae ≥ δ vs el baseline. Inconclusa ⇒ no dispara."""
    if golden_set.version != baseline.eval_result.golden_set_version:
        raise ValueError("monitor: el golden set debe ser la misma versión del baseline (BR-42)")
    if not golden_set.items:
        # Un golden set vacío daría recall=0.0 y un "drop" falso → fail-loud (el baseline se fija
        # solo sobre ≥50 ítems, BR-22, así que esto no debería ocurrir por el flujo normal).
        raise ValueError("monitor: el golden set no puede estar vacío")

    current = evaluate(rag, golden_set, k=k, tau=tau, seed=seed)
    if current.status is not EvalStatus.OK:
        # P1/BR-43: una re-evaluación inconclusa no da señal fiable → no dispara. `delta=0.0` es
        # placeholder (no una caída real; el recall de una corrida inconclusa no es comparable).
        return MonitorSignal(
            triggered=False,
            current=current,
            baseline_ref=baseline.version,
            delta=0.0,
            threshold=delta,
            source=source,
        )

    drop = baseline.eval_result.recall_span - current.recall_span
    return MonitorSignal(
        triggered=drop >= delta,  # BR-41
        current=current,
        baseline_ref=baseline.version,
        delta=drop,
        threshold=delta,
        source=source,
    )


__all__ = ["DEFAULT_DELTA", "check"]
