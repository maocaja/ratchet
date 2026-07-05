"""Integration (TASK-005): UNIQUE(StateKey) en Postgres + migración Alembic.

Requiere `DATABASE_URL` (servicio Postgres del CI); se salta si no está.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text

from ratchet.persistence import ImmutableVersionError
from ratchet.persistence.models import Base
from ratchet.persistence.postgres import PostgresRunRepository
from tests.factories import (
    make_full_run_record,
    make_golden_set,
    make_run_record,
    make_state_ref,
)

DATABASE_URL = os.environ.get("DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="requiere DATABASE_URL (Postgres)")


def _reset(engine) -> None:
    # Estado cero total entre corridas: tablas del modelo + el bookkeeping de Alembic.
    Base.metadata.drop_all(engine)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))


@pytest.fixture
def engine():
    eng = create_engine(DATABASE_URL)
    _reset(eng)
    Base.metadata.create_all(eng)
    yield eng
    _reset(eng)
    eng.dispose()


def _count(engine, table: str) -> int:
    with engine.connect() as conn:
        return conn.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()


def test_unique_state_key_idempotente_un_solo_run(engine):
    repo = PostgresRunRepository(engine)
    ref = make_state_ref()

    repo.record_run(make_run_record(run_id="run-1"), ref)
    second = repo.record_run(make_run_record(run_id="run-2"), ref)  # misma StateKey

    assert _count(engine, "runs") == 1  # UNIQUE(StateKey) enforcado por la BD (BR-73)
    assert second.run_id == "run-1"  # upsert idempotente: gana el primero
    assert repo.get_run(ref).run_id == "run-1"


def test_distinta_state_key_crea_dos_runs(engine):
    repo = PostgresRunRepository(engine)

    repo.record_run(make_run_record(run_id="a"), make_state_ref(k=5))
    repo.record_run(make_run_record(run_id="b"), make_state_ref(k=10))

    assert _count(engine, "runs") == 2


def test_golden_set_inmutable_en_db(engine):
    repo = PostgresRunRepository(engine)
    repo.save_golden_set(make_golden_set(version="gs-v1", n=2))

    with pytest.raises(ImmutableVersionError):
        repo.save_golden_set(make_golden_set(version="gs-v1", n=3))


def test_record_y_get_run_completo_roundtrip_en_db(engine):
    # Ruta crítica real: persistir un RunRecord anidado completo y reconstruirlo desde JSONB.
    repo = PostgresRunRepository(engine)
    ref = make_state_ref()
    run = make_full_run_record()

    repo.record_run(run, ref)

    assert repo.get_run(ref) == run


def test_alembic_upgrade_head_aplica_limpio_desde_cero(engine):
    from alembic import command
    from alembic.config import Config

    _reset(engine)  # cero total: sin tablas del modelo ni alembic_version
    command.upgrade(Config("alembic.ini"), "head")

    with engine.connect() as conn:
        conn.execute(text("SELECT 1 FROM runs"))
        conn.execute(text("SELECT 1 FROM golden_sets"))
        conn.execute(text("SELECT 1 FROM baselines"))
