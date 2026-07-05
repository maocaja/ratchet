"""C3 recall-por-span (determinista) + StateHasher + BootstrapEstimator(seed)."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Protocol

import numpy as np

from ratchet.domain import Chunk, EvalResult, EvalStatus, GoldenSet, PerItemResult, Span, StateRef

DEFAULT_BOOTSTRAP_SEED = 42
DEFAULT_BOOTSTRAP_SAMPLES = 1000
DEFAULT_K = 5
DEFAULT_TAU = 0.8


class RagPatientPort(Protocol):
    """Read-only evaluator surface expected from a RAG patient."""

    def retrieve(self, question: str, k: int) -> Sequence[Chunk]: ...

    def get_config(self) -> Mapping[str, Any]: ...

    def corpus_fingerprint(self) -> Iterable[tuple[str, str]]: ...


def normalize(text: str) -> str:
    """Canonical text normalization shared by recall offsets and corpus hashing."""

    normalized = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"\s+", " ", normalized).strip()


def cubre(chunk: Chunk, span: Span) -> float:
    """Return the fraction of `span` covered by `chunk`, using same-doc intervals only."""

    if chunk.doc_id != span.doc_id:
        return 0.0

    intersection = max(0, min(chunk.end, span.end) - max(chunk.start, span.start))
    return intersection / span.length


def recall_por_span(chunks: Sequence[Chunk], span: Span, tau: float = DEFAULT_TAU) -> bool:
    """A span is hit when the best same-doc chunk coverage reaches `tau`."""

    if not 0 < tau <= 1:
        raise ValueError("tau must be in (0, 1]")
    return max((cubre(chunk, span) for chunk in chunks), default=0.0) >= tau


class BootstrapEstimator:
    """Deterministic percentile bootstrap for recall means."""

    def __init__(
        self,
        seed: int = DEFAULT_BOOTSTRAP_SEED,
        samples: int = DEFAULT_BOOTSTRAP_SAMPLES,
        level: float = 0.95,
    ) -> None:
        if samples <= 0:
            raise ValueError("samples must be positive")
        if not 0 < level < 1:
            raise ValueError("level must be in (0, 1)")
        self.seed = seed
        self.samples = samples
        self.level = level

    def ci(self, hits: Sequence[bool | int | float]) -> tuple[float, float]:
        values = np.asarray(hits, dtype=np.float64)
        if values.size == 0:
            return (0.0, 0.0)

        rng = np.random.default_rng(self.seed)
        indexes = rng.integers(0, values.size, size=(self.samples, values.size))
        means = values[indexes].mean(axis=1)
        alpha = (1.0 - self.level) / 2.0
        lower, upper = np.percentile(means, [alpha * 100.0, (1.0 - alpha) * 100.0])
        return (float(lower), float(upper))


class StateHasher:
    """Build StateRef from the canonical state-hash rules in NFR design §P-1."""

    @classmethod
    def canonical_value(cls, value: Any) -> Any:
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json")
        if isinstance(value, Mapping):
            return {key: cls.canonical_value(item) for key, item in value.items()}
        if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
            return [cls.canonical_value(item) for item in value]
        return value

    @classmethod
    def canonical_json(cls, value: Any) -> str:
        return json.dumps(
            cls.canonical_value(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )

    @classmethod
    def hash_value(cls, value: Any) -> str:
        return hashlib.sha256(cls.canonical_json(value).encode("utf-8")).hexdigest()

    @classmethod
    def config_hash(cls, config: Mapping[str, Any]) -> str:
        return cls.hash_value(config)

    @classmethod
    def corpus_hash(cls, fingerprint: Iterable[tuple[str, str]]) -> str:
        per_doc = sorted(
            (doc_id, hashlib.sha256(normalize(content).encode("utf-8")).hexdigest())
            for doc_id, content in fingerprint
        )
        return cls.hash_value(per_doc)

    @classmethod
    def patch_hash(cls, patch: Any | None) -> str | None:
        if patch is None:
            return None
        if hasattr(patch, "model_dump"):
            return cls.hash_value(patch.model_dump(mode="json", exclude={"patch_hash"}))
        return cls.hash_value(patch)

    def state_ref(
        self,
        *,
        golden_set_version: str,
        config: Mapping[str, Any],
        corpus_fingerprint: Iterable[tuple[str, str]],
        patch: Any | None = None,
        k: int = DEFAULT_K,
        tau: float = DEFAULT_TAU,
    ) -> StateRef:
        return StateRef(
            golden_set_version=golden_set_version,
            config_hash=self.config_hash(config),
            corpus_hash=self.corpus_hash(corpus_fingerprint),
            patch_hash=self.patch_hash(patch),
            k=k,
            tau=tau,
        )


def evaluate(
    rag: RagPatientPort,
    gs: GoldenSet,
    k: int = DEFAULT_K,
    tau: float = DEFAULT_TAU,
    *,
    seed: int = DEFAULT_BOOTSTRAP_SEED,
    state_hasher: StateHasher | None = None,
    patch: Any | None = None,
) -> EvalResult:
    """Evaluate a golden set with deterministic recall-por-span."""

    per_item: list[PerItemResult] = []
    try:
        for item in gs.items:
            topk = rag.retrieve(item.question, k)
            hit = recall_por_span(topk, item.gold_span, tau)
            per_item.append(PerItemResult(item_id=item.item_id, hit=hit, critical=item.critical))
    except Exception:
        return EvalResult(
            golden_set_version=gs.version,
            k=k,
            tau=tau,
            recall_span=0.0,
            per_item=(),
            ci=(0.0, 0.0),
            critical_recall=0.0,
            status=EvalStatus.INCONCLUSA,
        )

    hits = [item.hit for item in per_item]
    recall_span = sum(hits) / len(hits) if hits else 0.0
    critical_hits = [item.hit for item in per_item if item.critical]
    critical_recall = sum(critical_hits) / len(critical_hits) if critical_hits else 0.0

    state_ref = None
    if state_hasher is not None:
        try:
            state_ref = state_hasher.state_ref(
                golden_set_version=gs.version,
                config=rag.get_config(),
                corpus_fingerprint=rag.corpus_fingerprint(),
                patch=patch,
                k=k,
                tau=tau,
            )
        except Exception:
            return EvalResult(
                golden_set_version=gs.version,
                k=k,
                tau=tau,
                recall_span=0.0,
                per_item=(),
                ci=(0.0, 0.0),
                critical_recall=0.0,
                status=EvalStatus.INCONCLUSA,
            )

    return EvalResult(
        golden_set_version=gs.version,
        k=k,
        tau=tau,
        recall_span=recall_span,
        per_item=tuple(per_item),
        ci=BootstrapEstimator(seed=seed).ci(hits),
        critical_recall=critical_recall,
        state_ref=state_ref,
        status=EvalStatus.OK,
    )


__all__ = [
    "DEFAULT_BOOTSTRAP_SAMPLES",
    "DEFAULT_BOOTSTRAP_SEED",
    "DEFAULT_K",
    "DEFAULT_TAU",
    "BootstrapEstimator",
    "RagPatientPort",
    "StateHasher",
    "cubre",
    "evaluate",
    "normalize",
    "recall_por_span",
]
