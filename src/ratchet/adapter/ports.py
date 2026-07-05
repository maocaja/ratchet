"""Puertos hexagonales para pacientes RAG."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ratchet.domain import Chunk, Patch, PatchHandle

type CorpusFingerprint = list[tuple[str, str]]
type RagConfig = dict[str, object]


@runtime_checkable
class RagPatientPort(Protocol):
    """Contrato del RAG paciente externo detras del adaptador (P5)."""

    def retrieve(self, query: str, k: int) -> list[Chunk]:
        """Recupera chunks deterministas para un indice fijo."""

    def generate(self, query: str, context: list[Chunk]) -> str:
        """Genera respuesta del RAG paciente."""

    def get_config(self) -> RagConfig:
        """Devuelve configuracion cruda del paciente para hashing de Ratchet."""

    def apply_config(self, config: RagConfig) -> RagConfig:
        """Aplica config y devuelve snapshot previo reversible."""

    def revert_config(self, previous_config: RagConfig) -> None:
        """Revierte a un snapshot de configuracion previo."""

    def supports_data_ops(self) -> bool:
        """Capability flag G1 para operaciones de datos."""

    def apply_data_patch(self, patch: Patch) -> PatchHandle:
        """Aplica un parche de datos y devuelve un handle reversible."""

    def reindex(self) -> None:
        """Reconstruye el indice del RAG paciente."""

    def revert_data_patch(self, handle: PatchHandle) -> None:
        """Revierte un parche de datos aplicado previamente."""

    def corpus_fingerprint(self) -> CorpusFingerprint:
        """Devuelve pares crudos `(doc_id, doc_content)`; Ratchet hashea."""
