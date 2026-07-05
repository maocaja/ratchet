"""Tests del investigador read-only (TASK-008): BR-51..58, G3, §P-3."""

from __future__ import annotations

import itertools

import pytest

from ratchet.adapter import SampleRagPatient
from ratchet.domain import Capa, Chunk, ChunkBoundaryInfo, Diagnosis, FixLayer, ProbeResults
from ratchet.investigator import (
    LayerAmbiguousError,
    Localizer,
    ProbeToolkit,
    UnderspecifiedFixError,
    localize_rules,
    write_incident,
)
from tests.factories import make_golden_item, make_monitor_signal, make_span

# Frase que vive SOLO en corpus_vigente/niif16.txt (no en el corpus viejo por defecto).
NIIF16_VIGENTE = "El plazo del arrendamiento comprende el periodo no cancelable más los periodos"


def _niif16_item():
    return make_golden_item(
        item_id="niif16-plazo",
        question="¿Cómo se determina el plazo del arrendamiento según la NIIF 16?",
        span=make_span(doc_id="niif16", start=0, end=len(NIIF16_VIGENTE), text=NIIF16_VIGENTE),
    )


class GoodRag:
    """RAG donde todas las sondas dan bien (caso ambiguo): el span vive, se recupera y se usa."""

    def __init__(self, doc_id: str, text: str) -> None:
        self._doc_id = doc_id
        self._text = text

    def retrieve(self, query: str, k: int) -> list[Chunk]:
        return [
            Chunk(
                chunk_id=f"{self._doc_id}:0",
                doc_id=self._doc_id,
                start=0,
                end=len(self._text),
                text=self._text,
                rank=0,
            )
        ]

    def generate(self, query: str, context: list[Chunk]) -> str:
        return self._text  # la respuesta contiene el span (containment True)

    def corpus_fingerprint(self) -> list[tuple[str, str]]:
        return [(self._doc_id, self._text)]


def test_niif_localiza_fuente_vieja_sin_red():
    # Corpus por defecto = niif16 VIEJO ⇒ span vigente ausente ⇒ fuente-vieja, verificado.
    dx = Localizer(ProbeToolkit(SampleRagPatient())).localize(_niif16_item())

    assert dx.capa is Capa.FUENTE_VIEJA
    assert dx.fix_layer is FixLayer.DATOS
    assert dx.verified is True
    assert dx.evidencia == ("niif16-plazo:span_vigente_en_corpus",)


def test_verify_claim_rechaza_claim_falso():
    localizer = Localizer(ProbeToolkit(SampleRagPatient()))
    claim_falso = Diagnosis(
        capa=Capa.RETRIEVAL_MISS,
        evidencia=("niif16-plazo:span_en_topk",),
        fix_layer=FixLayer.CONFIG,
        verified=False,
    )

    # La re-sonda dice fuente-vieja ≠ retrieval-miss ⇒ no verifica (BR-54).
    assert localizer.verify_claim(claim_falso, _niif16_item()) is False


def test_investigador_es_read_only_no_aplica_cambios():
    # BR-51 / G3: ni localize ni write_incident invocan apply_data_patch/apply_config.
    calls: list[str] = []

    class SpyRag(SampleRagPatient):
        def apply_data_patch(self, patch):
            calls.append("apply_data_patch")
            return super().apply_data_patch(patch)

        def apply_config(self, config):
            calls.append("apply_config")
            return super().apply_config(config)

    localizer = Localizer(ProbeToolkit(SpyRag()))
    item = _niif16_item()
    dx = localizer.localize(item)
    write_incident(dx, item, make_monitor_signal())

    assert calls == []


def test_write_incident_read_only_concluye_datos():
    item = _niif16_item()
    dx = Diagnosis(
        capa=Capa.FUENTE_VIEJA,
        evidencia=("niif16-plazo:span_vigente_en_corpus",),
        fix_layer=FixLayer.DATOS,
        verified=True,
    )

    writeup = write_incident(dx, item, make_monitor_signal())

    assert writeup.capa_localizada is Capa.FUENTE_VIEJA
    assert "versión vigente" in writeup.fix_prescrito
    assert "capa de datos" in writeup.conclusion


def test_span_vigente_containment_limitacion_conocida():
    # LIMITACIÓN CONOCIDA (BR-55): span_vigente_en_corpus es containment textual. Si el corpus
    # viejo contiene el span dorado VERBATIM (aunque sea en contexto negado), la sonda da True y
    # NO se dispara "fuente-vieja". Se mitiga con spans distintivos (frases completas, curación
    # humana BR-76). Este test PIN-ea el comportamiento para que un cambio sea intencional.
    span_text = "un activo por derecho de uso"
    corpus_viejo_negado = f"La norma derogada NO reconocía {span_text} en el estado financiero."
    rag = GoodRag("niif16", corpus_viejo_negado)
    item = make_golden_item(
        item_id="it",
        question="q",
        span=make_span(doc_id="niif16", start=0, end=len(span_text), text=span_text),
    )

    pr = ProbeToolkit(rag).probe(item)

    # Falso positivo conocido del containment: el span aparece (negado) ⇒ vigente=True.
    assert pr.span_vigente_en_corpus is True


def test_localize_ambiguo_sin_desambiguador_levanta():
    text = "el span dorado vive dentro de este documento indexado y recuperado"
    rag = GoodRag("doc-x", text)
    item = make_golden_item(
        item_id="it",
        question="q",
        span=make_span(doc_id="doc-x", start=0, end=14, text="el span dorado"),
    )

    with pytest.raises(LayerAmbiguousError):
        Localizer(ProbeToolkit(rag)).localize(item)


def test_localize_ambiguo_con_desambiguador_usa_capa_del_enum():
    class Dis:
        def disambiguate(self, probes: ProbeResults) -> Capa:
            return Capa.RETRIEVAL_MISS  # BR-52: el LLM devuelve una Capa del enum

    text = "el span dorado vive dentro de este documento indexado y recuperado"
    item = make_golden_item(
        item_id="it",
        question="q",
        span=make_span(doc_id="doc-x", start=0, end=14, text="el span dorado"),
    )

    dx = Localizer(ProbeToolkit(GoodRag("doc-x", text)), disambiguator=Dis()).localize(item)

    assert dx.capa is Capa.RETRIEVAL_MISS  # capa plumbed del desambiguador, dentro del enum
    # BR-54: la re-sonda determinista sigue ambigua ⇒ el claim LLM NO se auto-verifica → no acción.
    assert dx.verified is False


def test_localize_desambiguador_cobertura_levanta_underspecified():
    # BR-58: si el LLM desambigua a `cobertura`, el fix queda underspecified (U2), igual que la
    # rama determinista — no colapsa a CONFIG.
    class DisCobertura:
        def disambiguate(self, probes: ProbeResults) -> Capa:
            return Capa.COBERTURA

    text = "el span dorado vive dentro de este documento indexado y recuperado"
    item = make_golden_item(
        item_id="it",
        question="q",
        span=make_span(doc_id="doc-x", start=0, end=14, text="el span dorado"),
    )

    with pytest.raises(UnderspecifiedFixError):
        Localizer(ProbeToolkit(GoodRag("doc-x", text)), disambiguator=DisCobertura()).localize(item)


@pytest.mark.parametrize(
    ("vigente", "indexado", "en_topk", "split", "usa_span"),
    list(itertools.product([True, False], repeat=5)),  # 32 combinaciones, exhaustivo
)
def test_localize_rules_prioridad_y_enum(vigente, indexado, en_topk, split, usa_span):
    pr = ProbeResults(
        item_id="it",
        span_indexado=indexado,
        span_en_topk=en_topk,
        fronteras_de_chunk=ChunkBoundaryInfo(split=split),
        span_vigente_en_corpus=vigente,
        respuesta_usa_span=usa_span,
    )

    result = localize_rules(pr)

    if not vigente:
        assert result == (Capa.FUENTE_VIEJA, FixLayer.DATOS)
    elif not indexado:
        assert result == (Capa.COBERTURA, None)
    elif not en_topk and split:
        assert result == (Capa.CHUNKING, FixLayer.CONFIG)
    elif not en_topk:
        assert result == (Capa.RETRIEVAL_MISS, FixLayer.CONFIG)
    elif not usa_span:
        assert result == (Capa.GENERACION, FixLayer.CONFIG)
    else:
        assert result is None  # ambiguo → LLM

    if result is not None:  # BR-53: capa siempre dentro del enum cerrado
        assert result[0] in set(Capa)
