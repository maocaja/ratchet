"""Tests for deterministic evaluator core (TASK-003)."""

from __future__ import annotations

import math

from hypothesis import given
from hypothesis import strategies as st

from ratchet.domain import Chunk, EvalStatus, GoldenSet, Patch
from ratchet.evaluator import BootstrapEstimator, StateHasher, cubre, evaluate, recall_por_span
from tests.factories import make_golden_item, make_span


class FakeRag:
    def __init__(
        self,
        retrieved: dict[str, tuple[Chunk, ...]],
        *,
        config: dict | None = None,
        fingerprint: tuple[tuple[str, str], ...] = (),
        fail: bool = False,
        fail_config: bool = False,
        fail_fingerprint: bool = False,
    ) -> None:
        self._retrieved = retrieved
        self._config = config or {"retriever": {"k": 5, "model": "bm25"}}
        self._fingerprint = fingerprint or (("doc-a", " Texto   Fuente "),)
        self._fail = fail
        self._fail_config = fail_config
        self._fail_fingerprint = fail_fingerprint

    def retrieve(self, question: str, k: int) -> tuple[Chunk, ...]:
        if self._fail:
            raise RuntimeError("retrieve failed")
        return self._retrieved.get(question, ())[:k]

    def get_config(self) -> dict:
        if self._fail_config:
            raise RuntimeError("config read failed")
        return self._config

    def corpus_fingerprint(self) -> tuple[tuple[str, str], ...]:
        if self._fail_fingerprint:
            raise RuntimeError("fingerprint read failed")
        return self._fingerprint


def make_chunk(
    doc_id: str = "doc-a", start: int = 0, end: int = 10, chunk_id: str = "ch-1"
) -> Chunk:
    return Chunk(chunk_id=chunk_id, doc_id=doc_id, start=start, end=end, text="", rank=0)


def test_cubre_usa_mismo_doc_e_interseccion_de_intervalos():
    span = make_span(doc_id="doc-a", start=10, end=20, text="0123456789")

    assert cubre(make_chunk(doc_id="doc-b", start=10, end=20), span) == 0.0
    assert cubre(make_chunk(start=12, end=18), span) == 0.6
    assert cubre(make_chunk(start=0, end=100), span) == 1.0


def test_recall_por_span_aplica_tau_sobre_mejor_cobertura():
    span = make_span(doc_id="doc-a", start=10, end=20, text="0123456789")
    chunks = (make_chunk(start=0, end=17), make_chunk(start=10, end=18))

    assert recall_por_span(chunks, span, tau=0.8) is True
    assert recall_por_span(chunks, span, tau=0.9) is False


def test_evaluate_recomputa_recall_y_per_item_desde_golden_set():
    hit_item = make_golden_item(
        item_id="it-hit",
        question="q-hit",
        critical=True,
        span=make_span(doc_id="doc-a", start=0, end=10),
    )
    miss_item = make_golden_item(
        item_id="it-miss",
        question="q-miss",
        span=make_span(doc_id="doc-a", start=20, end=30),
    )
    gs = GoldenSet(version="gs-v1", items=(hit_item, miss_item))
    rag = FakeRag(
        {
            "q-hit": (make_chunk(start=0, end=8),),
            "q-miss": (make_chunk(start=20, end=27),),
        }
    )

    result = evaluate(rag, gs, k=5, tau=0.8, seed=123)

    recomputed = sum(item.hit for item in result.per_item) / len(result.per_item)
    assert result.recall_span == recomputed
    assert result.recall_span == 0.5
    assert result.critical_recall == 1.0
    assert [(item.item_id, item.hit, item.critical) for item in result.per_item] == [
        ("it-hit", True, True),
        ("it-miss", False, False),
    ]


def test_evaluate_retrieve_failure_returns_inconclusa():
    gs = GoldenSet(version="gs-v1", items=(make_golden_item(question="q"),))

    result = evaluate(FakeRag({}, fail=True), gs)

    assert result.status is EvalStatus.INCONCLUSA
    assert result.recall_span == 0.0
    assert result.per_item == ()


def test_bootstrap_same_input_and_seed_is_bit_exact():
    hits = [True, False, True, True, False, False]
    first = BootstrapEstimator(seed=99).ci(hits)
    second = BootstrapEstimator(seed=99).ci(hits)

    assert first == second


def test_state_hasher_corpus_hash_is_order_independent_and_normalized():
    hasher = StateHasher()

    first = hasher.corpus_hash((("b", "Dos\nlineas"), ("a", " Texto   Fuente ")))
    second = hasher.corpus_hash((("a", "texto fuente"), ("b", "dos lineas")))

    assert first == second


def test_state_ref_includes_eval_params_so_tau_changes_key():
    hit_item = make_golden_item(question="q", span=make_span(doc_id="doc-a", start=0, end=10))
    gs = GoldenSet(version="gs-v1", items=(hit_item,))
    rag = FakeRag({"q": (make_chunk(start=0, end=8),)})
    hasher = StateHasher()

    tau_08 = evaluate(rag, gs, tau=0.8, state_hasher=hasher).state_ref
    tau_09 = evaluate(rag, gs, tau=0.9, state_hasher=hasher).state_ref

    assert tau_08 is not None
    assert tau_09 is not None
    assert tau_08.key() != tau_09.key()
    assert tau_08.tau == 0.8
    assert tau_09.tau == 0.9


def test_state_hasher_accepts_pydantic_patch_model_without_using_embedded_hash():
    patch = Patch(
        patch_id="patch-1",
        doc_id="doc-a",
        new_content="contenido corregido",
        rationale="span faltante",
        patch_hash="precomputed-patch-hash",
    )

    assert StateHasher().patch_hash(patch) != "precomputed-patch-hash"


def test_state_hasher_patch_hash_uses_canonical_patch_payload():
    hasher = StateHasher()
    first = Patch(
        patch_id="patch-1",
        doc_id="doc-a",
        new_content="contenido corregido",
        rationale="span faltante",
        patch_hash="stale-caller-hash",
    )
    second = Patch(
        patch_id="patch-1",
        doc_id="doc-a",
        new_content="otro contenido",
        rationale="span faltante",
        patch_hash="stale-caller-hash",
    )

    assert hasher.patch_hash(first) != hasher.patch_hash(second)


def test_evaluate_state_read_failure_returns_inconclusa():
    gs = GoldenSet(version="gs-v1", items=(make_golden_item(question="q"),))
    rag = FakeRag({"q": (make_chunk(),)}, fail_fingerprint=True)

    result = evaluate(rag, gs, state_hasher=StateHasher())

    assert result.status is EvalStatus.INCONCLUSA
    assert result.state_ref is None
    assert result.per_item == ()


@given(
    span_start=st.integers(min_value=0, max_value=200),
    span_len=st.integers(min_value=1, max_value=200),
    chunk_start=st.integers(min_value=0, max_value=250),
    chunk_len=st.integers(min_value=1, max_value=250),
)
def test_pbt_cobertura_esta_en_rango(span_start, span_len, chunk_start, chunk_len):
    span = make_span(doc_id="doc-a", start=span_start, end=span_start + span_len)
    chunk = make_chunk(start=chunk_start, end=chunk_start + chunk_len)

    coverage = cubre(chunk, span)

    assert 0.0 <= coverage <= 1.0


@given(
    span_start=st.integers(min_value=0, max_value=200),
    span_len=st.integers(min_value=1, max_value=200),
    chunk_start=st.integers(min_value=0, max_value=250),
    chunk_len=st.integers(min_value=1, max_value=250),
    extra=st.integers(min_value=0, max_value=250),
)
def test_pbt_cobertura_es_monotona_al_expandir_chunk(
    span_start, span_len, chunk_start, chunk_len, extra
):
    span = make_span(doc_id="doc-a", start=span_start, end=span_start + span_len)
    chunk = make_chunk(start=chunk_start, end=chunk_start + chunk_len)
    expanded = make_chunk(start=max(0, chunk_start - extra), end=chunk_start + chunk_len + extra)

    assert cubre(expanded, span) >= cubre(chunk, span)


@given(hits=st.lists(st.booleans(), min_size=1, max_size=30))
def test_pbt_bootstrap_ci_bounds(hits):
    lower, upper = BootstrapEstimator(seed=7, samples=100).ci(hits)

    assert 0.0 <= lower <= upper <= 1.0
    assert math.isfinite(lower)
    assert math.isfinite(upper)
