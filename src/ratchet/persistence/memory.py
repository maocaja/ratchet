"""Fake in-memory del RunRepository con paridad de unicidad (BR-73/BR-21) para tests rápidos."""

from __future__ import annotations

from typing import TypeVar

from ratchet.domain import Baseline, GoldenSet, RunRecord, StateRef
from ratchet.persistence.keys import state_key_str
from ratchet.persistence.ports import ImmutableVersionError

_V = TypeVar("_V")


class InMemoryRunRepository:
    """Implementación in-memory: misma semántica de idempotencia/inmutabilidad que Postgres."""

    def __init__(self) -> None:
        self._runs: dict[str, RunRecord] = {}
        self._golden_sets: dict[str, GoldenSet] = {}
        self._baselines: dict[str, Baseline] = {}

    def record_run(self, run: RunRecord, state_ref: StateRef) -> RunRecord:
        # Idempotente por StateKey (BR-73): si ya hay run bajo esa clave, se devuelve el existente.
        return self._runs.setdefault(state_key_str(state_ref), run)

    def get_run(self, state_ref: StateRef) -> RunRecord | None:
        return self._runs.get(state_key_str(state_ref))

    def save_golden_set(self, golden_set: GoldenSet) -> None:
        self._save_versioned(self._golden_sets, golden_set.version, golden_set, "golden set")

    def get_golden_set(self, version: str) -> GoldenSet | None:
        return self._golden_sets.get(version)

    def save_baseline(self, baseline: Baseline) -> None:
        self._save_versioned(self._baselines, baseline.version, baseline, "baseline")

    def get_baseline(self, version: str) -> Baseline | None:
        return self._baselines.get(version)

    @staticmethod
    def _save_versioned(store: dict[str, _V], version: str, value: _V, label: str) -> None:
        # Inmutable por versión (BR-21): re-guardar idéntico es no-op; contenido distinto falla.
        # Se compara por la proyección JSON — MISMA semántica que Postgres (paridad fake↔BD).
        existing = store.get(version)
        if existing is not None and existing.model_dump(mode="json") != value.model_dump(
            mode="json"
        ):
            raise ImmutableVersionError(f"{label} '{version}' es inmutable por versión (BR-21)")
        store[version] = value
