"""Tests del adapter RAG de muestra (TASK-007)."""

from __future__ import annotations

import inspect
import os

import pytest

from ratchet.adapter import (
    DataPatchError,
    RetryingRagPatient,
    RetryPolicy,
    SampleRagPatient,
)
from ratchet.domain import Patch


def make_patch(doc_id: str = "niif-16-vieja", content: str | None = None) -> Patch:
    return Patch(
        patch_id=f"patch:{doc_id}",
        doc_id=doc_id,
        new_content=content
        or (
            "NIIF 16 vigente parcheada: reconoce activo por derecho de uso y pasivo "
            "por arrendamiento."
        ),
        rationale="actualizar fuente vieja",
        patch_hash=f"hash:{doc_id}",
    )


def test_supports_data_ops_capability_flag_true():
    assert SampleRagPatient().supports_data_ops() is True


def test_retrieve_deterministico_para_indice_fijo():
    rag = SampleRagPatient()

    first = rag.retrieve("NIIF 16 arrendatario activo pasivo arrendamiento", k=2)
    second = rag.retrieve("NIIF 16 arrendatario activo pasivo arrendamiento", k=2)

    assert first == second
    assert [chunk.rank for chunk in first] == list(range(len(first)))


def test_generate_stub_deterministico_sin_api_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    rag = SampleRagPatient()
    context = rag.retrieve("NIIF 16 arrendatario", k=1)

    first = rag.generate("NIIF 16 arrendatario", context)
    second = rag.generate("NIIF 16 arrendatario", context)

    assert first == second
    assert first.startswith("stub:")
    assert "ANTHROPIC_API_KEY" not in os.environ


def test_corpus_fingerprint_devuelve_contenido_crudo_ordenado():
    fingerprint = SampleRagPatient().corpus_fingerprint()

    assert fingerprint == sorted(fingerprint)
    assert all(
        isinstance(doc_id, str) and isinstance(content, str) for doc_id, content in fingerprint
    )
    assert any(
        doc_id == "niif-16-vieja" and "version vieja" in content for doc_id, content in fingerprint
    )


def test_corpus_base_excluye_niif16_vigente_hasta_parche():
    rag = SampleRagPatient()

    assert all(doc_id != "niif-16-vigente" for doc_id, _ in rag.corpus_fingerprint())
    assert rag.retrieve("derecho pasivo arrendamiento", k=1) == []

    rag.apply_data_patch(make_patch())

    assert rag.retrieve("derecho pasivo arrendamiento", k=1)[0].doc_id == "niif-16-vieja"


def test_apply_data_patch_y_revert_restauran_doc_e_indice():
    rag = SampleRagPatient()
    before_fingerprint = rag.corpus_fingerprint()
    before_retrieval = rag.retrieve("clasificacion historica operativos financieros", k=1)

    handle = rag.apply_data_patch(make_patch())
    patched_retrieval = rag.retrieve("derecho pasivo arrendamiento", k=1)
    rag.revert_data_patch(handle)

    assert patched_retrieval[0].doc_id == "niif-16-vieja"
    assert rag.corpus_fingerprint() == before_fingerprint
    assert rag.retrieve("clasificacion historica operativos financieros", k=1) == before_retrieval


def test_reindex_error_revierte_patch_y_senala_inconclusa():
    rag = SampleRagPatient()
    before_fingerprint = rag.corpus_fingerprint()
    before_retrieval = rag.retrieve("clasificacion historica operativos financieros", k=1)
    rag.inject_reindex_failure()

    with pytest.raises(DataPatchError):
        rag.apply_data_patch(make_patch())

    assert rag.corpus_fingerprint() == before_fingerprint
    assert rag.retrieve("clasificacion historica operativos financieros", k=1) == before_retrieval


def test_retry_policy_reintenta_lecturas_y_no_mutaciones():
    class FlakyRag(SampleRagPatient):
        def __init__(self) -> None:
            super().__init__()
            self.retrieve_attempts = 0
            self.patch_attempts = 0

        def retrieve(self, query: str, k: int):
            self.retrieve_attempts += 1
            if self.retrieve_attempts == 1:
                raise RuntimeError("lectura transitoria")
            return super().retrieve(query, k)

        def apply_data_patch(self, patch: Patch):
            self.patch_attempts += 1
            raise RuntimeError("mutacion falla")

    inner = FlakyRag()
    wrapped = RetryingRagPatient(inner, RetryPolicy(max_attempts=2))

    assert wrapped.retrieve("NIIF 16", 1)
    assert inner.retrieve_attempts == 2
    with pytest.raises(RuntimeError, match="mutacion falla"):
        wrapped.apply_data_patch(make_patch())
    assert inner.patch_attempts == 1


def test_retry_wrapper_mutaciones_delegan_sin_retry_policy_call():
    apply_source = inspect.getsource(RetryingRagPatient.apply_data_patch)
    reindex_source = inspect.getsource(RetryingRagPatient.reindex)

    assert "_retry_policy" not in apply_source
    assert "_retry_policy" not in reindex_source
