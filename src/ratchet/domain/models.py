"""Tipos de dominio de U1 (Pydantic v2) — DDD táctico.

Value Objects (frozen, igualdad por valor) y Entities/Aggregates (identidad propia).
Solo tipos + validaciones básicas; la lógica de negocio (recall, hashing, gate) vive en
sus módulos (evaluator/, gate/, …). Ver functional-design/domain-entities.md.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ratchet.domain.enums import (
    ApprovalDecision,
    ApprovalKind,
    Capa,
    EvalStatus,
    FixLayer,
    GateDecision,
    MonitorSource,
    ReportDecision,
    Role,
    RunState,
    RunStatus,
)

# ── Value Objects ────────────────────────────────────────────────────────────


class _VO(BaseModel):
    """Base de los Value Objects: inmutables (frozen)."""

    model_config = ConfigDict(frozen=True)


class Span(_VO):
    """Span de fuente dorado: offsets de carácter sobre `Document.text` normalizado."""

    doc_id: str
    start: int = Field(ge=0)
    end: int
    text: str

    @model_validator(mode="after")
    def _len_positivo(self) -> Span:
        if self.start >= self.end:
            raise ValueError("Span requiere start < end (len > 0)")
        return self

    @property
    def length(self) -> int:
        return self.end - self.start


# Nota: Chunk y Document son **Entities externas** (identidad chunk_id/doc_id, read-only vía
# adaptador) — se frizan por conveniencia (nunca mutan del lado de Ratchet), no porque sean VOs.
class Chunk(_VO):
    """Fragmento recuperable devuelto por retrieve (Entity externa, read-only)."""

    chunk_id: str
    doc_id: str
    start: int = Field(ge=0)
    end: int
    text: str
    rank: int = Field(ge=0)


class Document(_VO):
    """Documento fuente del corpus (externo, read-only vía adaptador)."""

    doc_id: str
    text: str
    version: str | None = None


class StateRef(_VO):
    """Clave de estado canónica (dueño de la composición: nfr-design-patterns §P-1).

    Los hashes se computan en evaluator/StateHasher (TASK-003); aquí solo se almacenan.
    """

    golden_set_version: str
    config_hash: str
    corpus_hash: str
    patch_hash: str | None = None
    k: int = Field(gt=0)
    tau: float = Field(gt=0, le=1)

    def key(self) -> tuple:
        """Tupla de identidad (idempotencia). El seed NO va aquí (repro bit-exacta aparte)."""
        return (
            self.golden_set_version,
            self.config_hash,
            self.corpus_hash,
            self.patch_hash,
            (self.k, self.tau),
        )


class PerItemResult(_VO):
    """Acierto por ítem, con criticidad (necesaria para el guardrail 🔒 del gate — BR-34)."""

    item_id: str
    hit: bool
    critical: bool


class EvalResult(_VO):
    """Resultado de evaluar un RAG contra un GoldenSet(v). Sin faithfulness en U1 (BR-15)."""

    golden_set_version: str
    k: int = Field(default=5, gt=0)
    tau: float = Field(default=0.8, gt=0, le=1)
    recall_span: float = Field(ge=0, le=1)
    per_item: tuple[PerItemResult, ...] = ()
    ci: tuple[float, float]
    critical_recall: float = Field(ge=0, le=1)
    state_ref: StateRef | None = None
    status: EvalStatus = EvalStatus.OK

    @model_validator(mode="after")
    def _item_ids_unicos(self) -> EvalResult:
        # per_item debe ser pareable por item_id (gate pareado + guardrail 🔒 — BR-33/34).
        ids = [pi.item_id for pi in self.per_item]
        if len(ids) != len(set(ids)):
            raise ValueError("EvalResult.per_item requiere item_id únicos (pareo before/after)")
        return self


class ChunkBoundaryInfo(_VO):
    """¿El span quedó partido entre ≥2 chunks?"""

    split: bool


class ProbeResults(_VO):
    """Hechos deterministas del ProbeToolkit por ítem (no juicios; sin LLM — BR-57).

    Convención de `probe_id` (materializada en TASK-008 / Localizer): `f"{item_id}:{campo}"`
    (p.ej. `it-1:span_vigente_en_corpus`). `Diagnosis.evidencia` cita esos probe_id (G3, claim
    verificable). Aquí solo los hechos; el mapeo a probe_id se hace río arriba.
    """

    item_id: str
    span_indexado: bool
    span_en_topk: bool
    fronteras_de_chunk: ChunkBoundaryInfo
    span_vigente_en_corpus: bool
    respuesta_usa_span: bool


class Diagnosis(_VO):
    """Claim verificable del Localizer (G3): estructurado, no acción ni prosa."""

    capa: Capa
    evidencia: tuple[str, ...] = ()
    fix_layer: FixLayer
    verified: bool = False


class GateVerdict(_VO):
    """Decisión del gate determinista (sin LLM — G2)."""

    decision: GateDecision
    delta: float
    ci_delta: tuple[float, float]
    criterio: str = "CI.lower ≥ 0"
    regressions_criticas: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def _invariante_guardrail(self) -> GateVerdict:
        # Defense-in-depth del guardrail 🔒 (BR-34) a nivel de tipo (domain-entities §GateVerdict).
        if self.regressions_criticas > 0 and self.decision is not GateDecision.REVERT:
            raise ValueError("regressions_criticas > 0 ⇒ decision debe ser revert (guardrail 🔒)")
        if self.decision is GateDecision.APPROVE and self.ci_delta[0] < 0:
            raise ValueError("approve solo si CI.lower(delta) ≥ 0")
        return self


class MonitorSignal(_VO):
    """Señal de disparo del loop."""

    triggered: bool
    current: EvalResult
    baseline_ref: str
    delta: float
    threshold: float
    source: MonitorSource = MonitorSource.UNKNOWN

    @model_validator(mode="after")
    def _inconclusa_no_dispara(self) -> MonitorSignal:
        # Una corrida inconclusa no da señal fiable → no dispara (BR-43).
        if self.current.status is EvalStatus.INCONCLUSA and self.triggered:
            raise ValueError("una corrida inconclusa no dispara (triggered debe ser False)")
        return self


class Report(_VO):
    """Vista antes/después reproducible (proyección de resultado)."""

    run_id: str
    recall_before: float | None = None
    recall_after: float | None = None
    delta: float | None = None
    ci_delta: tuple[float, float] | None = None
    change: str | None = None
    writeup_id: str | None = None
    decision: ReportDecision
    reproducible_from: StateRef | None = None


# ── Entities & Aggregates (identidad propia) ─────────────────────────────────


class GoldenItem(BaseModel):
    """Caso etiquetado del golden set (la verdad humana — BR-76)."""

    model_config = ConfigDict(frozen=True)  # hecho etiquetado, no mutante

    item_id: str
    question: str
    answer: str
    gold_span: Span
    critical: bool = False
    slice: str | None = None


class GoldenSet(BaseModel):
    """Aggregate root: colección versionada e inmutable por versión (BR-21)."""

    model_config = ConfigDict(frozen=True)  # corregir = nueva versión, nunca mutar

    version: str
    items: tuple[GoldenItem, ...] = ()
    created_at: datetime | None = None


class Baseline(BaseModel):
    """EvalResult congelado como referencia estable."""

    model_config = ConfigDict(frozen=True)  # baseline congelado

    version: str
    eval_result: EvalResult
    set_at: datetime | None = None


class Writeup(BaseModel):
    """Documento de incidente auditable (read-only — G3)."""

    model_config = ConfigDict(frozen=True)  # read-only: no muta tras emitirse (G3)

    writeup_id: str
    sintoma: str
    capa_localizada: Capa
    evidencia: tuple[str, ...] = ()
    fix_prescrito: str
    conclusion: str


class Patch(BaseModel):
    """Parche de datos propuesto (rama de datos)."""

    patch_id: str
    doc_id: str
    new_content: str
    rationale: str
    patch_hash: str


class PatchHandle(BaseModel):
    """Recibo reversible de un parche aplicado."""

    handle_id: str
    patch_id: str
    prev_snapshot: str


class ApprovalRequest(BaseModel):
    """Gate humano P2 (dos kinds distintos — BR-61)."""

    request_id: str
    kind: ApprovalKind
    proposal_ref: str
    decision: ApprovalDecision = ApprovalDecision.PENDING
    decided_by: str | None = None
    decided_at: datetime | None = None


class Operator(BaseModel):
    """Actor humano (Andrés/Carolina)."""

    operator_id: str
    role: Role


class RunRecord(BaseModel):
    """Aggregate root de la corrida. Idempotente por su clave de estado (§P-1)."""

    run_id: str
    state: RunState = RunState.NUEVA  # máquina de estados fina (Parte C)
    status: RunStatus = RunStatus.EN_PROGRESO  # rollup grueso
    seed: int
    before: EvalResult | None = None
    after: EvalResult | None = None
    signal: MonitorSignal | None = None
    diagnosis: Diagnosis | None = None
    writeup_id: str | None = None
    patch: Patch | None = None
    patch_handle: PatchHandle | None = None
    verdict: GateVerdict | None = None
    approvals: tuple[ApprovalRequest, ...] = ()
