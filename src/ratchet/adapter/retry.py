"""Retry acotado solo para lecturas idempotentes del adaptador."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from time import sleep
from typing import TypeVar

from ratchet.adapter.ports import CorpusFingerprint, RagConfig, RagPatientPort
from ratchet.domain import Chunk, Patch, PatchHandle, RagError

T = TypeVar("T")


class RetryExhaustedError(RagError):
    """La operacion fallo despues de agotar los intentos configurados (es un RagError)."""


@dataclass(frozen=True)
class RetryPolicy:
    """Retry con backoff exponencial para operaciones idempotentes."""

    max_attempts: int = 3
    backoff_seconds: float = 0.0
    # Solo reintenta fallos operacionales del RAG (transitorios). Un bug propio (KeyError,
    # etc.) NO es RagError → se propaga de inmediato, no se reintenta ni se envuelve en
    # RetryExhaustedError (que es RagError) — así el evaluador no lo enmascara como INCONCLUSA.
    retry_exceptions: tuple[type[Exception], ...] = (RagError,)

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts debe ser >= 1")
        if self.backoff_seconds < 0:
            raise ValueError("backoff_seconds debe ser >= 0")

    def call(self, operation: Callable[[], T]) -> T:
        """Ejecuta `operation` hasta agotar intentos."""

        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                return operation()
            except self.retry_exceptions as exc:
                last_error = exc
                if attempt == self.max_attempts:
                    break
                if self.backoff_seconds:
                    sleep(self.backoff_seconds * (2 ** (attempt - 1)))
        raise RetryExhaustedError("operacion idempotente fallo tras retry") from last_error


class RetryingRagPatient:
    """Wrapper que aplica retry solo a lecturas idempotentes (CG-1)."""

    def __init__(self, inner: RagPatientPort, retry_policy: RetryPolicy) -> None:
        self._inner = inner
        self._retry_policy = retry_policy

    def retrieve(self, query: str, k: int) -> list[Chunk]:
        return self._retry_policy.call(lambda: self._inner.retrieve(query, k))

    def generate(self, query: str, context: list[Chunk]) -> str:
        return self._retry_policy.call(lambda: self._inner.generate(query, context))

    def get_config(self) -> RagConfig:
        return self._retry_policy.call(self._inner.get_config)

    def corpus_fingerprint(self) -> CorpusFingerprint:
        return self._retry_policy.call(self._inner.corpus_fingerprint)

    def apply_config(self, config: RagConfig) -> RagConfig:
        return self._inner.apply_config(config)

    def revert_config(self, previous_config: RagConfig) -> None:
        self._inner.revert_config(previous_config)

    def supports_data_ops(self) -> bool:
        return self._inner.supports_data_ops()

    def apply_data_patch(self, patch: Patch) -> PatchHandle:
        return self._inner.apply_data_patch(patch)

    def reindex(self) -> None:
        self._inner.reindex()

    def revert_data_patch(self, handle: PatchHandle) -> None:
        self._inner.revert_data_patch(handle)
