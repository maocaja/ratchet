"""C4 investigador read-only (G3): ProbeToolkit + Localizer + verify_claim + write_incident.

Sondas deterministas del lineage (sin LLM-judge, BR-57), reglas de capa deterministas por
orden de prioridad (BR-52); el LLM SOLO desambigua lo ambiguo y no inventa capa fuera del enum.
El investigador NO aplica cambios (BR-51): solo emite `Diagnosis` + `Writeup`.
"""

from __future__ import annotations

from typing import Protocol

from ratchet.domain import (
    Capa,
    Chunk,
    ChunkBoundaryInfo,
    Diagnosis,
    FixLayer,
    GoldenItem,
    MonitorSignal,
    ProbeResults,
    Span,
    Writeup,
)
from ratchet.evaluator import DEFAULT_K, cubre, normalize


class ProbeRag(Protocol):
    """Superficie read-only del RAG que necesita el investigador (nunca `apply_*` — G3)."""

    def retrieve(self, query: str, k: int) -> list[Chunk]: ...

    def generate(self, query: str, context: list[Chunk]) -> str: ...

    def corpus_fingerprint(self) -> list[tuple[str, str]]: ...


class LayerDisambiguator(Protocol):
    """Frontera de agencia (§P-3): el LLM SOLO desambigua; devuelve una `Capa` del enum (BR-52)."""

    def disambiguate(self, probes: ProbeResults) -> Capa: ...


class LayerAmbiguousError(RuntimeError):
    """Las sondas no concluyen y no hay desambiguador (LLM) — fuera de alcance U1 hermético."""


class UnderspecifiedFixError(RuntimeError):
    """La capa localizada tiene `fix_layer` sin especificar (`cobertura` → se resuelve en U2)."""


# Sondas decisivas por capa → `probe_id = f"{item_id}:{campo}"` (evidencia verificable, G3).
_DECISIVE_PROBES: dict[Capa, tuple[str, ...]] = {
    Capa.FUENTE_VIEJA: ("span_vigente_en_corpus",),
    Capa.COBERTURA: ("span_indexado",),
    Capa.CHUNKING: ("span_en_topk", "fronteras_de_chunk"),
    Capa.RETRIEVAL_MISS: ("span_en_topk",),
    Capa.GENERACION: ("respuesta_usa_span",),
}


class ProbeToolkit:
    """Calcula `ProbeResults` deterministas del lineage de un ítem (sin LLM — BR-57)."""

    def __init__(self, rag: ProbeRag, k: int = DEFAULT_K) -> None:
        self._rag = rag
        self._k = k

    def probe(self, item: GoldenItem) -> ProbeResults:
        span = item.gold_span
        retrieved = list(self._rag.retrieve(item.question, self._k))
        corpus = dict(self._rag.corpus_fingerprint())
        doc_norm = normalize(corpus.get(span.doc_id, ""))
        span_norm = normalize(span.text)
        doc_chunks = [chunk for chunk in retrieved if chunk.doc_id == span.doc_id]
        answer = self._rag.generate(item.question, retrieved)
        return ProbeResults(
            item_id=item.item_id,
            span_indexado=span.doc_id in corpus,
            span_en_topk=any(cubre(chunk, span) > 0 for chunk in doc_chunks),
            fronteras_de_chunk=ChunkBoundaryInfo(split=_span_split(doc_chunks, span)),
            # BR-55: "fuente-vieja" ⇔ el span vigente NO está en el corpus actual.
            span_vigente_en_corpus=span_norm in doc_norm,
            # BR-57: containment textual (subcadena normalizada), NO faithfulness.
            respuesta_usa_span=span_norm in normalize(answer),
        )


def localize_rules(pr: ProbeResults) -> tuple[Capa, FixLayer | None] | None:
    """Reglas deterministas por orden de prioridad (BL-6). `None` ⇒ ambiguo (requiere LLM)."""
    if not pr.span_vigente_en_corpus:
        return (Capa.FUENTE_VIEJA, FixLayer.DATOS)  # ← NIIF (BR-55)
    if not pr.span_indexado:
        return (Capa.COBERTURA, None)  # fix underspecified (U2, BR-58)
    if not pr.span_en_topk and pr.fronteras_de_chunk.split:
        return (Capa.CHUNKING, FixLayer.CONFIG)
    if not pr.span_en_topk:
        return (Capa.RETRIEVAL_MISS, FixLayer.CONFIG)
    if not pr.respuesta_usa_span:
        return (Capa.GENERACION, FixLayer.CONFIG)
    return None  # todo se ve bien pero el ítem falló → ambiguo → LLM desambigua


class Localizer:
    """Localiza la capa (determinista; LLM solo ante ambigüedad) y emite `Diagnosis` verificado."""

    def __init__(
        self, toolkit: ProbeToolkit, disambiguator: LayerDisambiguator | None = None
    ) -> None:
        self._toolkit = toolkit
        self._disambiguator = disambiguator

    def localize(self, item: GoldenItem) -> Diagnosis:
        capa, fix_layer = self._resolve(self._toolkit.probe(item))
        if fix_layer is None:
            raise UnderspecifiedFixError(f"capa {capa} tiene fix underspecified (U2)")
        claim = Diagnosis(
            capa=capa,
            evidencia=_evidence_for(capa, item.item_id),
            fix_layer=fix_layer,
            verified=False,
        )
        return claim.model_copy(update={"verified": self.verify_claim(claim, item)})

    def verify_claim(self, dx: Diagnosis, item: GoldenItem) -> bool:
        """Recomprueba re-sondando: la capa/fix re-derivada debe coincidir (BR-54). Falso ⇒ rechaza.

        Re-deriva el veredicto COMPLETO con `localize_rules` (más fuerte que dereferenciar los
        `probe_id` de `dx.evidencia`): un claim solo se auto-verifica si las sondas frescas siguen
        concluyendo la misma capa. Un claim LLM-desambiguado re-deriva `None` ⇒ verified=False.
        """
        verdict = localize_rules(self._toolkit.probe(item))
        if verdict is None:
            return False
        capa2, fix2 = verdict
        return capa2 == dx.capa and fix2 == dx.fix_layer

    def _resolve(self, pr: ProbeResults) -> tuple[Capa, FixLayer | None]:
        verdict = localize_rules(pr)
        if verdict is not None:
            return verdict
        if self._disambiguator is None:
            raise LayerAmbiguousError(f"capa ambigua para {pr.item_id} (requiere LLM, fuera de U1)")
        capa = self._disambiguator.disambiguate(pr)  # BR-52: devuelve Capa (enum), no inventa
        return (capa, _fix_for(capa))


def write_incident(dx: Diagnosis, item: GoldenItem, signal: MonitorSignal) -> Writeup:
    """Writeup de incidente read-only (BL-7/BR-56): síntoma, capa, evidencia, fix, conclusión.

    Nota de contrato: recibe `item` (no `pr` como el pseudocódigo BL-7) porque `fix_prescrito`
    necesita `item.gold_span.doc_id`, que `ProbeResults` no lleva. TASK-011 consume esta firma.
    """
    return Writeup(
        writeup_id=f"wu:{item.item_id}",
        sintoma=f"caída de confiabilidad (delta={signal.delta})",
        capa_localizada=dx.capa,
        evidencia=dx.evidencia,
        fix_prescrito=_fix_prescrito(dx, item),
        conclusion=(
            "ninguna perilla de config lo arregla → capa de datos"
            if dx.fix_layer is FixLayer.DATOS
            else f"→ capa de {dx.fix_layer.value}"
        ),
    )


def _span_split(chunks: list[Chunk], span: Span) -> bool:
    # split ⇔ ningún chunk cubre el span entero pero ≥2 chunks lo solapan.
    if any(chunk.start <= span.start and chunk.end >= span.end for chunk in chunks):
        return False
    return sum(1 for chunk in chunks if cubre(chunk, span) > 0) >= 2


def _evidence_for(capa: Capa, item_id: str) -> tuple[str, ...]:
    return tuple(f"{item_id}:{field}" for field in _DECISIVE_PROBES[capa])


def _fix_for(capa: Capa) -> FixLayer | None:
    # Coherente con localize_rules: cobertura queda underspecified (U2, BR-58) también cuando
    # el LLM la desambigua → Localizer.localize levantará UnderspecifiedFixError, no CONFIG.
    if capa is Capa.FUENTE_VIEJA:
        return FixLayer.DATOS
    if capa is Capa.COBERTURA:
        return None
    return FixLayer.CONFIG


def _fix_prescrito(dx: Diagnosis, item: GoldenItem) -> str:
    if dx.capa is Capa.FUENTE_VIEJA:
        return f"reemplazar Document {item.gold_span.doc_id} por su versión vigente"
    return f"ajustar config del RAG para la capa {dx.capa.value}"


__all__ = [
    "LayerAmbiguousError",
    "LayerDisambiguator",
    "Localizer",
    "ProbeRag",
    "ProbeToolkit",
    "UnderspecifiedFixError",
    "localize_rules",
    "write_incident",
]
