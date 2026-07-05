"""RAG de muestra in-process para el camino NIIF."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import ClassVar

from rank_bm25 import BM25Okapi

from ratchet.adapter.ports import CorpusFingerprint, RagConfig
from ratchet.domain import Chunk, Document, Patch, PatchHandle

TOKEN_RE = re.compile(r"\w+", re.UNICODE)


class ReindexError(RuntimeError):
    """Fallo reconstruyendo el indice del RAG de muestra."""


class DataPatchError(RuntimeError):
    """Fallo atomico aplicando un parche de datos."""


@dataclass(frozen=True)
class LexicalRetriever:
    """Retriever lexico BM25 determinista para un conjunto fijo de documentos."""

    documents: tuple[Document, ...]
    bm25: BM25Okapi = field(init=False)
    tokenized_docs: list[list[str]] = field(init=False)

    def __post_init__(self) -> None:
        tokenized_docs = [_tokenize(document.text) for document in self.documents]
        object.__setattr__(self, "tokenized_docs", tokenized_docs)
        object.__setattr__(self, "bm25", BM25Okapi(tokenized_docs))

    def retrieve(self, query: str, k: int) -> list[Chunk]:
        if k <= 0:
            raise ValueError("k debe ser > 0")
        scores = self.bm25.get_scores(_tokenize(query))
        ranked = sorted(
            enumerate(scores),
            key=lambda item: (-float(item[1]), self.documents[item[0]].doc_id),
        )
        chunks: list[Chunk] = []
        for rank, (index, score) in enumerate(ranked[:k]):
            if score <= 0:
                continue
            document = self.documents[index]
            chunks.append(
                Chunk(
                    chunk_id=f"{document.doc_id}:0",
                    doc_id=document.doc_id,
                    start=0,
                    end=len(document.text),
                    text=document.text,
                    rank=rank,
                )
            )
        return chunks


class SampleRagPatient:
    """Paciente RAG hermetico: corpus NIIF/NIA, BM25 y generacion stub."""

    DEFAULT_DOCUMENTS: ClassVar[tuple[Document, ...]] = (
        Document(
            doc_id="niif-16-vieja",
            version="vieja",
            text=(
                "NIIF 16 version vieja: la clasificacion historica distingue arrendamientos "
                "operativos y financieros para el arrendatario. Este documento esta sembrado "
                "como regresion para el camino NIIF."
            ),
        ),
        Document(
            doc_id="niif-16-vigente",
            version="vigente",
            text=(
                "NIIF 16 vigente: el arrendatario reconoce un activo por derecho de uso y "
                "un pasivo por arrendamiento para la mayoria de los contratos de arrendamiento."
            ),
        ),
        Document(
            doc_id="nia-500",
            version="vigente",
            text=(
                "NIA 500 evidencia de auditoria: el auditor disena y aplica procedimientos "
                "para obtener evidencia suficiente y adecuada."
            ),
        ),
    )

    def __init__(
        self,
        documents: tuple[Document, ...] | None = None,
        config: RagConfig | None = None,
        *,
        fail_next_reindex: bool = False,
    ) -> None:
        self._documents = {
            document.doc_id: document for document in documents or self.DEFAULT_DOCUMENTS
        }
        self._config: RagConfig = dict(config or {"retriever": "bm25", "chunking": "whole-doc"})
        self._patch_snapshots: dict[str, tuple[str, Document | None]] = {}
        self._fail_next_reindex = fail_next_reindex
        self._retriever = self._build_retriever()

    def retrieve(self, query: str, k: int) -> list[Chunk]:
        return self._retriever.retrieve(query, k)

    def generate(self, query: str, context: list[Chunk]) -> str:
        doc_ids = ",".join(chunk.doc_id for chunk in context) or "sin-contexto"
        return f"stub:{query.strip()}|docs:{doc_ids}"

    def get_config(self) -> RagConfig:
        return dict(self._config)

    def apply_config(self, config: RagConfig) -> RagConfig:
        previous = self.get_config()
        self._config = dict(config)
        return previous

    def revert_config(self, previous_config: RagConfig) -> None:
        self._config = dict(previous_config)

    def supports_data_ops(self) -> bool:
        return True

    def apply_data_patch(self, patch: Patch) -> PatchHandle:
        previous = self._documents.get(patch.doc_id)
        previous_text = "" if previous is None else previous.text
        handle = PatchHandle(
            handle_id=f"handle:{patch.patch_id}",
            patch_id=patch.patch_id,
            prev_snapshot=previous_text,
        )
        self._patch_snapshots[handle.handle_id] = (patch.doc_id, previous)
        self._documents[patch.doc_id] = Document(
            doc_id=patch.doc_id,
            text=patch.new_content,
            version="patched",
        )
        try:
            self.reindex()
        except ReindexError as exc:
            self.revert_data_patch(handle)
            raise DataPatchError("apply_data_patch revertido por fallo de reindex") from exc
        return handle

    def reindex(self) -> None:
        if self._fail_next_reindex:
            self._fail_next_reindex = False
            raise ReindexError("fallo inyectado de reindex")
        self._retriever = self._build_retriever()

    def revert_data_patch(self, handle: PatchHandle) -> None:
        patch_doc_id, previous = self._patch_snapshots.pop(
            handle.handle_id, (handle.patch_id, None)
        )
        if previous is not None:
            self._documents[previous.doc_id] = previous
        else:
            self._documents.pop(patch_doc_id, None)
        self.reindex()

    def corpus_fingerprint(self) -> CorpusFingerprint:
        return [(doc_id, self._documents[doc_id].text) for doc_id in sorted(self._documents)]

    def inject_reindex_failure(self) -> None:
        self._fail_next_reindex = True

    def _build_retriever(self) -> LexicalRetriever:
        documents = tuple(self._documents[doc_id] for doc_id in sorted(self._documents))
        return LexicalRetriever(documents)


def _tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text)]
