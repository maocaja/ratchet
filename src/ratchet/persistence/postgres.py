"""Impl. Postgres del RunRepository: UNIQUE(StateKey) + upsert idempotente (BR-73/BR-21)."""

from __future__ import annotations

from sqlalchemy import Engine, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ratchet.domain import Baseline, GoldenSet, RunRecord, StateRef
from ratchet.persistence.keys import state_key_str
from ratchet.persistence.models import BaselineRow, GoldenSetRow, RunRow
from ratchet.persistence.ports import ImmutableVersionError


class PostgresRunRepository:
    """RunRepository sobre Postgres. La unicidad de la StateKey la enforca la BD (UNIQUE)."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def record_run(self, run: RunRecord, state_ref: StateRef) -> RunRecord:
        key = state_key_str(state_ref)
        with Session(self._engine) as session:
            # Upsert idempotente: ON CONFLICT (state_key) DO NOTHING ⇒ el primer run gana (BR-73).
            stmt = (
                pg_insert(RunRow)
                .values(state_key=key, run_json=run.model_dump(mode="json"))
                .on_conflict_do_nothing(index_elements=["state_key"])
            )
            session.execute(stmt)
            session.commit()
            row = session.execute(select(RunRow).where(RunRow.state_key == key)).scalar_one()
            return RunRecord.model_validate(row.run_json)

    def get_run(self, state_ref: StateRef) -> RunRecord | None:
        with Session(self._engine) as session:
            row = session.execute(
                select(RunRow).where(RunRow.state_key == state_key_str(state_ref))
            ).scalar_one_or_none()
            return RunRecord.model_validate(row.run_json) if row is not None else None

    def save_golden_set(self, golden_set: GoldenSet) -> None:
        self._save_versioned(
            GoldenSetRow,
            "gs_json",
            golden_set.version,
            golden_set.model_dump(mode="json"),
            "golden set",
        )

    def get_golden_set(self, version: str) -> GoldenSet | None:
        with Session(self._engine) as session:
            row = session.get(GoldenSetRow, version)
            return GoldenSet.model_validate(row.gs_json) if row is not None else None

    def save_baseline(self, baseline: Baseline) -> None:
        self._save_versioned(
            BaselineRow,
            "baseline_json",
            baseline.version,
            baseline.model_dump(mode="json"),
            "baseline",
        )

    def get_baseline(self, version: str) -> Baseline | None:
        with Session(self._engine) as session:
            row = session.get(BaselineRow, version)
            return Baseline.model_validate(row.baseline_json) if row is not None else None

    def _save_versioned(
        self, row_cls: type, column: str, version: str, payload: dict, label: str
    ) -> None:
        """Inserta versionado inmutable (BR-21); traduce la carrera de PK a error de dominio."""
        with Session(self._engine) as session:
            existing = session.get(row_cls, version)
            if existing is not None:
                if getattr(existing, column) != payload:
                    raise ImmutableVersionError(
                        f"{label} '{version}' es inmutable por versión (BR-21)"
                    )
                return  # re-guardar idéntico = no-op idempotente
            session.add(row_cls(version=version, **{column: payload}))
            try:
                session.commit()
            except IntegrityError:
                # Carrera: otro proceso creó esta versión primero. Re-leer y comparar contenido.
                session.rollback()
                existing = session.get(row_cls, version)
                if existing is None or getattr(existing, column) != payload:
                    raise ImmutableVersionError(
                        f"{label} '{version}' es inmutable por versión (BR-21)"
                    ) from None
