"""C2 GoldenSetRegistry: golden set versionado (>=50), baseline, historial, decisiones.

Cura y versiona el golden set (la verdad humana — BR-76/CG-4: se SIEMBRA desde un archivo
versionado en el repo, no se recomputa) y fija el baseline (rechaza <50 o eval inconclusa).
La persistencia vive tras el puerto `RunRepository` (el registry no toca SQLAlchemy).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from ratchet.domain import Baseline, EvalResult, EvalStatus, GoldenItem, GoldenSet, Span
from ratchet.persistence.ports import RunRepository

MIN_GOLDEN_ITEMS = 50

DEFAULT_SEED_PATH = Path(__file__).resolve().parents[3] / "seeds" / "golden_set_niif.yaml"


class GoldenSetTooSmallError(RuntimeError):
    """El golden set/rebanada tiene <50 ítems: no se puede fijar baseline (BR-22)."""


class InconclusiveBaselineError(RuntimeError):
    """No se fija baseline desde una evaluación inconclusa (BR-25/P1)."""


class GoldenSetNotFoundError(RuntimeError):
    """No hay golden set persistido para esa versión."""


def load_golden_set_seed(path: Path = DEFAULT_SEED_PATH) -> GoldenSet:
    """Reconstruye el GoldenSet NIIF desde el archivo versionado (CG-4). No lo recomputa."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    items = tuple(
        GoldenItem(
            item_id=raw["item_id"],
            question=raw["question"],
            answer=raw["answer"],
            gold_span=Span(**raw["gold_span"]),
            critical=raw["critical"],
            slice=raw.get("slice"),
        )
        for raw in data["items"]
    )
    return GoldenSet(version=f"niif-v{data['version']}", items=items)


class GoldenSetRegistry:
    """Curación/versionado del golden set + baseline, sobre el puerto `RunRepository`."""

    def __init__(self, repository: RunRepository) -> None:
        self._repo = repository

    def save_golden_set(self, golden_set: GoldenSet) -> None:
        # Los tipos ya enforan spans válidos (Span: start<end); inmutabilidad por versión = repo.
        self._repo.save_golden_set(golden_set)

    def get_golden_set(self, version: str) -> GoldenSet | None:
        return self._repo.get_golden_set(version)

    def seed_from_repo(self, path: Path = DEFAULT_SEED_PATH) -> GoldenSet:
        """Siembra el golden set NIIF desde el archivo versionado y lo persiste (CG-4)."""
        golden_set = load_golden_set_seed(path)
        self.save_golden_set(golden_set)
        return golden_set

    def set_baseline(self, version: str, eval_result: EvalResult) -> Baseline:
        golden_set = self._repo.get_golden_set(version)
        if golden_set is None:
            raise GoldenSetNotFoundError(f"golden set '{version}' no está registrado")
        n_items = len(golden_set.items)
        if n_items < MIN_GOLDEN_ITEMS:
            raise GoldenSetTooSmallError(
                f"'{version}': {n_items} ítems < {MIN_GOLDEN_ITEMS} (BR-22)"
            )
        if eval_result.status is not EvalStatus.OK:
            raise InconclusiveBaselineError(
                "no se fija baseline desde evaluación inconclusa (BR-25)"
            )
        baseline = Baseline(version=version, eval_result=eval_result)
        self._repo.save_baseline(baseline)
        return baseline

    def get_baseline(self, version: str) -> Baseline | None:
        return self._repo.get_baseline(version)


__all__ = [
    "DEFAULT_SEED_PATH",
    "MIN_GOLDEN_ITEMS",
    "GoldenSetNotFoundError",
    "GoldenSetRegistry",
    "GoldenSetTooSmallError",
    "InconclusiveBaselineError",
    "load_golden_set_seed",
]
