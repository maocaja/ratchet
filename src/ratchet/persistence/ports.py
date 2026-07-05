"""Puerto de persistencia. El core habla con la BD SOLO por este puerto (no importa SQLAlchemy)."""

from __future__ import annotations

from typing import Protocol

from ratchet.domain import Baseline, GoldenSet, RunRecord, StateRef


class ImmutableVersionError(RuntimeError):
    """Sobrescribir un golden set / baseline versionado con contenido distinto (BR-21)."""


class RunRepository(Protocol):
    """Contrato de persistencia: runs idempotentes por clave de estado, versionados inmutables."""

    def record_run(self, run: RunRecord, state_ref: StateRef) -> RunRecord:
        """Registra el run; idempotente por `StateKey` (BR-73). Si ya existe, devuelve ese."""

    def get_run(self, state_ref: StateRef) -> RunRecord | None:
        """Devuelve el run registrado bajo esa clave de estado, o None."""

    def save_golden_set(self, golden_set: GoldenSet) -> None:
        """Persiste el golden set; inmutable por versión (BR-21)."""

    def get_golden_set(self, version: str) -> GoldenSet | None: ...

    def save_baseline(self, baseline: Baseline) -> None:
        """Persiste el baseline; inmutable por versión (BR-21)."""

    def get_baseline(self, version: str) -> Baseline | None: ...
