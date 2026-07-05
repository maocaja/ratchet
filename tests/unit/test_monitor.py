"""Tests del monitor (TASK-009): BR-41 dispara si cae ≥ δ, BR-42 misma versión, BR-43 inconclusa."""

from __future__ import annotations

import pytest

from ratchet.domain import (
    Baseline,
    Chunk,
    EvalResult,
    EvalStatus,
    GoldenSet,
    RagError,
)
from ratchet.monitor import check
from tests.factories import make_golden_item, make_span


def _golden(n: int = 4, version: str = "niif-v1") -> GoldenSet:
    items = tuple(
        make_golden_item(
            item_id=f"it-{i}", question=f"q{i}", span=make_span(doc_id="doc-a", start=0, end=10)
        )
        for i in range(n)
    )
    return GoldenSet(version=version, items=items)


class HitRag:
    """RAG controlable: recupera un chunk que cubre el span solo para las preguntas 'hit'."""

    def __init__(self, hit_questions: set[str]) -> None:
        self._hits = set(hit_questions)

    def retrieve(self, question: str, k: int) -> list[Chunk]:
        if question in self._hits:
            # el texto cubre el span dorado (make_span default text="texto dorado")
            return [
                Chunk(chunk_id="c", doc_id="doc-a", start=0, end=10, text="texto dorado", rank=0)
            ]
        return []

    def get_config(self) -> dict:
        return {}

    def corpus_fingerprint(self) -> list[tuple[str, str]]:
        return []


class FailRag(HitRag):
    def retrieve(self, question: str, k: int) -> list[Chunk]:
        raise RagError("rag caído")


def _baseline(recall: float = 1.0, version: str = "niif-v1") -> Baseline:
    ev = EvalResult(
        golden_set_version=version,
        recall_span=recall,
        per_item=(),
        ci=(recall, recall),
        critical_recall=1.0,
    )
    return Baseline(version="bl-v1", eval_result=ev)


def test_dispara_cuando_recall_cae_bajo_umbral():
    signal = check(HitRag({"q0", "q1", "q2"}), _baseline(recall=1.0), _golden(4))  # 0.75, drop 0.25

    assert signal.triggered is True
    assert signal.delta == pytest.approx(0.25)
    assert signal.source.value == "unknown"


def test_no_dispara_cuando_recall_estable():
    signal = check(HitRag({"q0", "q1", "q2", "q3"}), _baseline(recall=1.0), _golden(4))  # 1.0

    assert signal.triggered is False


def test_dispara_en_el_umbral_exacto():
    # 19/20 = 0.95 ⇒ drop = 0.05 == δ ⇒ dispara (BR-41 usa ≥).
    hits = {f"q{i}" for i in range(19)}
    signal = check(HitRag(hits), _baseline(recall=1.0), _golden(20))

    assert signal.triggered is True


def test_no_dispara_si_inconclusa():
    signal = check(FailRag(set()), _baseline(recall=1.0), _golden(4))

    assert signal.triggered is False  # BR-43
    assert signal.current.status is EvalStatus.INCONCLUSA


def test_no_dispara_cuando_recall_mejora():
    # current (0.75) > baseline (0.5) ⇒ drop negativo ⇒ no dispara (sin abs()).
    signal = check(HitRag({"q0", "q1", "q2"}), _baseline(recall=0.5), _golden(4))

    assert signal.triggered is False
    assert signal.delta < 0


def test_exige_misma_golden_set_version_del_baseline():
    with pytest.raises(ValueError, match="misma versión"):
        check(HitRag(set()), _baseline(version="niif-v1"), _golden(4, version="otra-version"))


def test_golden_set_vacio_falla_ruidoso():
    with pytest.raises(ValueError, match="no puede estar vacío"):
        check(HitRag(set()), _baseline(version="niif-v1"), GoldenSet(version="niif-v1", items=()))
