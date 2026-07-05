"""Motor de la superficie: cablea el LoopOrchestrator para el demo NIIF (in-memory, hermético).

`run` arranca el loop (pausa en un gate humano); `approve` acumula la decisión y re-corre desde
cero (seguro: el RAG de muestra se reconstruye fresco desde seeds/ en cada corrida). `report`
proyecta el `Report`. Es la extensión natural de los resolvers inyectados del orquestador.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from ratchet.adapter.sample_rag import SampleRagPatient
from ratchet.domain import (
    ApprovalDecision,
    ApprovalKind,
    Baseline,
    Diagnosis,
    GoldenItem,
    Patch,
    Report,
    RunRecord,
)
from ratchet.evaluator import DEFAULT_BOOTSTRAP_SEED, DEFAULT_K, DEFAULT_TAU, evaluate
from ratchet.orchestrator import LoopOrchestrator
from ratchet.registry import load_golden_set_seed
from ratchet.reporter import build_report

_VIGENTE_DIR = Path(__file__).resolve().parents[3] / "seeds" / "corpus_vigente"


def _utcnow() -> datetime:
    return datetime.now(UTC)


class RunNotFoundError(RuntimeError):
    """No hay una corrida registrada con ese id."""


class RunExistsError(RuntimeError):
    """Ya hay una corrida con ese id (no se sobrescriben decisiones humanas — §P-1)."""


class ReportService:
    """Orquesta corridas del demo NIIF y guarda su estado + decisiones humanas acumuladas."""

    def __init__(
        self,
        state_path: Path | None = None,
        *,
        k: int = DEFAULT_K,
        tau: float = DEFAULT_TAU,
        seed: int = DEFAULT_BOOTSTRAP_SEED,
    ) -> None:
        self._k, self._tau, self._seed = k, tau, seed
        self._orchestrator = LoopOrchestrator(k=k, tau=tau, seed=seed)
        self._golden_set = load_golden_set_seed()
        self._baseline = self._measure_baseline()
        self._runs: dict[str, RunRecord] = {}
        self._state_path = state_path  # None = in-memory (API); archivo = persistente (CLI)
        self._decisions: dict[str, dict[ApprovalKind, ApprovalDecision]] = self._load_state()

    def _load_state(self) -> dict[str, dict[ApprovalKind, ApprovalDecision]]:
        if self._state_path is None or not self._state_path.exists():
            return {}
        try:
            raw = json.loads(self._state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}  # estado corrupto → arrancar limpio en vez de romper todos los comandos
        return {
            rid: {ApprovalKind(k): ApprovalDecision(v) for k, v in decs.items()}
            for rid, decs in raw.items()
        }

    def _save_state(self) -> None:
        if self._state_path is None:
            return
        raw = {
            rid: {k.value: v.value for k, v in decs.items()}
            for rid, decs in self._decisions.items()
        }
        # Escritura atómica: temp + rename (un crash a mitad no corrompe el estado).
        tmp = self._state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(raw), encoding="utf-8")
        tmp.replace(self._state_path)

    def _measure_baseline(self) -> Baseline:
        # Baseline = recall medido sobre el corpus VIGENTE (el estado sano de referencia), con el
        # MISMO k/τ/seed que usará el orquestador para el "after" (comparación válida).
        vigente = SampleRagPatient.from_corpus_dir(_VIGENTE_DIR)
        return Baseline(
            version=self._golden_set.version,
            eval_result=evaluate(
                vigente, self._golden_set, k=self._k, tau=self._tau, seed=self._seed
            ),
            set_at=_utcnow(),
        )

    def _propose_patch(self, dx: Diagnosis, item: GoldenItem) -> Patch:
        doc_id = item.gold_span.doc_id
        vigente = (_VIGENTE_DIR / f"{doc_id}.txt").read_text(encoding="utf-8")
        return Patch(
            patch_id=f"patch:{doc_id}",
            doc_id=doc_id,
            new_content=vigente,
            rationale="reemplazar la fuente vieja por su versión vigente",
            patch_hash=hashlib.sha256(vigente.encode("utf-8")).hexdigest()[:16],
        )

    def start(self, run_id: str) -> RunRecord:
        if run_id in self._decisions:  # no sobrescribir decisiones ya registradas (§P-1)
            raise RunExistsError(run_id)
        self._decisions[run_id] = {}
        self._save_state()
        return self._execute(run_id)

    def approve(self, run_id: str, kind: ApprovalKind, decision: ApprovalDecision) -> RunRecord:
        if run_id not in self._decisions:
            raise RunNotFoundError(run_id)
        self._decisions[run_id][kind] = decision
        self._save_state()
        return self._execute(run_id)

    def get_run(self, run_id: str) -> RunRecord:
        if run_id in self._runs:
            return self._runs[run_id]
        if run_id in self._decisions:  # proceso fresco (CLI): re-derivar desde las decisiones
            return self._execute(run_id)
        raise RunNotFoundError(run_id)

    def report(self, run_id: str) -> Report:
        return build_report(self.get_run(run_id))

    def baseline_recall(self) -> float:
        return self._baseline.eval_result.recall_span

    def _execute(self, run_id: str) -> RunRecord:
        decisions = self._decisions[run_id]
        rag = SampleRagPatient()  # corpus VIEJO (estado degradado), fresco cada corrida
        run = self._orchestrator.run_loop(
            rag,
            self._baseline,
            self._golden_set,
            confirm_patch=lambda _p: decisions.get(
                ApprovalKind.CONFIRM_PATCH, ApprovalDecision.PENDING
            ),
            approve_deploy=lambda _r: decisions.get(
                ApprovalKind.APPROVE_DEPLOY, ApprovalDecision.PENDING
            ),
            propose_patch=self._propose_patch,
            now=_utcnow,
            run_id=run_id,
        )
        self._runs[run_id] = run
        return run
