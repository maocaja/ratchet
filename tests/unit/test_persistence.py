"""Tests del fake RunRepository (TASK-005): BR-73 idempotencia, BR-21 inmutabilidad."""

from __future__ import annotations

import pytest

from ratchet.domain import Baseline, RunRecord
from ratchet.persistence import ImmutableVersionError, InMemoryRunRepository, state_key_str
from tests.factories import (
    make_eval_result,
    make_full_run_record,
    make_golden_set,
    make_run_record,
    make_state_ref,
)


def test_record_run_idempotente_por_state_key():
    repo = InMemoryRunRepository()
    ref = make_state_ref()

    first = repo.record_run(make_run_record(run_id="run-1"), ref)
    second = repo.record_run(make_run_record(run_id="run-2"), ref)  # misma clave de estado

    assert first.run_id == "run-1"
    assert second.run_id == "run-1"  # doble record → 1 run (devuelve el existente)
    assert repo.get_run(ref).run_id == "run-1"


def test_record_run_distinto_k_crea_run_distinto():
    repo = InMemoryRunRepository()
    ref_a = make_state_ref(k=5)
    ref_b = make_state_ref(k=10)  # distinto k ⇒ distinta StateKey

    repo.record_run(make_run_record(run_id="a"), ref_a)
    repo.record_run(make_run_record(run_id="b"), ref_b)

    assert repo.get_run(ref_a).run_id == "a"
    assert repo.get_run(ref_b).run_id == "b"


def test_record_run_distinto_corpus_crea_run_distinto():
    repo = InMemoryRunRepository()
    ref_a = make_state_ref(corpus_hash="corpus-viejo")
    ref_b = make_state_ref(corpus_hash="corpus-nuevo")

    repo.record_run(make_run_record(run_id="a"), ref_a)
    repo.record_run(make_run_record(run_id="b"), ref_b)

    assert repo.get_run(ref_a).run_id == "a"
    assert repo.get_run(ref_b).run_id == "b"


def test_get_run_ausente_devuelve_none():
    assert InMemoryRunRepository().get_run(make_state_ref()) is None


def test_golden_set_inmutable_por_version():
    repo = InMemoryRunRepository()
    gs1 = make_golden_set(version="gs-v1", n=2)
    gs2 = make_golden_set(version="gs-v1", n=3)  # misma versión, contenido distinto

    repo.save_golden_set(gs1)
    with pytest.raises(ImmutableVersionError):
        repo.save_golden_set(gs2)

    repo.save_golden_set(gs1)  # re-guardar idéntico = no-op idempotente
    assert repo.get_golden_set("gs-v1") == gs1


def test_baseline_inmutable_por_version():
    repo = InMemoryRunRepository()
    bl1 = Baseline(version="bl-v1", eval_result=make_eval_result(recall=0.7))
    bl2 = Baseline(version="bl-v1", eval_result=make_eval_result(recall=0.9))

    repo.save_baseline(bl1)
    with pytest.raises(ImmutableVersionError):
        repo.save_baseline(bl2)


def test_runrecord_roundtrip_json_conserva_estructura_anidada():
    # Ruta crítica de Postgres: model_dump(mode="json") → model_validate reconstruye igual
    # (before/after EvalResult, StateRef, MonitorSignal, Diagnosis, GateVerdict, datetime, enums).
    run = make_full_run_record()

    restored = RunRecord.model_validate(run.model_dump(mode="json"))

    assert restored == run


def test_state_key_str_estable_y_excluye_seed():
    # Misma clave de estado ⇒ mismo string (el seed no participa).
    ref = make_state_ref()
    assert state_key_str(ref) == state_key_str(make_state_ref())
    assert state_key_str(make_state_ref(k=5)) != state_key_str(make_state_ref(k=10))
