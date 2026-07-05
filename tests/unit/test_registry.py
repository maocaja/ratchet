"""Tests del GoldenSetRegistry (TASK-006): BR-22/24/25/76, CG-4 seed desde repo."""

from __future__ import annotations

import pytest

from ratchet.domain import EvalStatus
from ratchet.persistence import ImmutableVersionError, InMemoryRunRepository
from ratchet.registry import (
    GoldenSetNotFoundError,
    GoldenSetRegistry,
    GoldenSetTooSmallError,
    InconclusiveBaselineError,
    load_golden_set_seed,
)
from tests.factories import make_eval_result, make_golden_set


def _registry() -> GoldenSetRegistry:
    return GoldenSetRegistry(InMemoryRunRepository())


def test_seed_carga_50_items_validos_desde_el_repo():
    # CG-4/BR-76: se siembra desde el archivo versionado, no se recomputa.
    golden_set = load_golden_set_seed()

    assert len(golden_set.items) >= 50
    assert sum(1 for item in golden_set.items if item.critical) >= 1
    assert any(item.gold_span.doc_id == "niif16" for item in golden_set.items)
    assert golden_set.version == "niif-v1"


def test_seed_from_repo_persiste_y_recupera():
    registry = _registry()

    seeded = registry.seed_from_repo()

    assert registry.get_golden_set(seeded.version) == seeded


def test_seed_from_repo_es_idempotente():
    # Re-sembrar el mismo archivo versionado no rompe (contenido idéntico = no-op, BR-21).
    registry = _registry()

    first = registry.seed_from_repo()
    second = registry.seed_from_repo()

    assert first == second
    assert registry.get_golden_set(first.version) == first


def test_set_baseline_rechaza_menos_de_50():
    registry = _registry()
    registry.save_golden_set(make_golden_set(version="gs-49", n=49))

    with pytest.raises(GoldenSetTooSmallError):
        registry.set_baseline("gs-49", make_eval_result())


def test_set_baseline_rechaza_evaluacion_inconclusa():
    registry = _registry()
    registry.save_golden_set(make_golden_set(version="gs-50", n=50))

    with pytest.raises(InconclusiveBaselineError):
        registry.set_baseline("gs-50", make_eval_result(status=EvalStatus.INCONCLUSA))


def test_set_baseline_happy_persiste_baseline():
    registry = _registry()
    registry.save_golden_set(make_golden_set(version="gs-50", n=50))

    baseline = registry.set_baseline("gs-50", make_eval_result(recall=0.82))

    assert baseline.version == "gs-50"
    assert registry.get_baseline("gs-50") == baseline


def test_set_baseline_sin_golden_set_registrado_falla():
    with pytest.raises(GoldenSetNotFoundError):
        _registry().set_baseline("inexistente", make_eval_result())


def test_golden_set_inmutable_por_version():
    registry = _registry()
    registry.save_golden_set(make_golden_set(version="gs-1", n=50))

    with pytest.raises(ImmutableVersionError):
        registry.save_golden_set(make_golden_set(version="gs-1", n=51))  # mismo version, distinto
