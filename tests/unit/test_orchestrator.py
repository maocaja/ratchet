"""Tests del LoopOrchestrator (TASK-011): e2e NIIF, state machine, G2/CG-2, BR-65/72/75."""

from __future__ import annotations

import inspect
from datetime import UTC, datetime

from ratchet.domain import (
    ApprovalDecision,
    ApprovalKind,
    Baseline,
    Chunk,
    EvalResult,
    GoldenSet,
    Patch,
    PatchHandle,
    PerItemResult,
    RunState,
    RunStatus,
)
from ratchet.orchestrator import LoopOrchestrator
from tests.factories import make_golden_item, make_span


class ScenarioRag:
    """RAG controlable para el loop: niif16 falla hasta que se aplica el parche (fuente-vieja)."""

    def __init__(
        self,
        *,
        reindex_fails: bool = False,
        break_after: str | None = None,
        niif16_ok: bool = False,
        fail_after_patch: bool = False,
        no_data_ops: bool = False,
    ) -> None:
        self._patched = False
        self._reindex_fails = reindex_fails
        self._break = break_after  # pregunta que se ROMPE tras el parche (regresión inyectada)
        self._niif16_ok = niif16_ok  # niif16 ya sano antes del parche (caso sin-cambio)
        self._fail_after_patch = fail_after_patch  # la re-eval post-parche falla (RagError)
        self._no_data_ops = no_data_ops  # G1: el RAG no soporta operaciones de datos

    def _hits(self, question: str) -> bool:
        good = {"q1", "q2", "q3"}
        if self._niif16_ok:
            good = good | {"q0"}
        if self._patched:
            good = (good | {"q0"}) - ({self._break} if self._break else set())
        return question in good

    def retrieve(self, question: str, k: int) -> list[Chunk]:
        if self._patched and self._fail_after_patch:
            from ratchet.domain import RagError

            raise RagError("re-eval post-parche caída")
        if self._hits(question):
            doc = "niif16" if question == "q0" else "doc-a"
            return [Chunk(chunk_id=f"{doc}:0", doc_id=doc, start=0, end=1000, text="x", rank=0)]
        return []

    def generate(self, query: str, context: list[Chunk]) -> str:
        return ""

    def get_config(self) -> dict:
        return {}

    def corpus_fingerprint(self) -> list[tuple[str, str]]:
        niif16 = (
            "el span vigente de niif16 vive aqui" if self._patched else "version vieja derogada"
        )
        return [("niif16", niif16), ("doc-a", "texto de doc a")]

    def supports_data_ops(self) -> bool:
        return not self._no_data_ops

    def apply_data_patch(self, patch: Patch) -> PatchHandle:
        from ratchet.adapter.sample_rag import DataPatchError

        if self._reindex_fails:
            raise DataPatchError("reindex inyectado falla")
        self._patched = True
        return PatchHandle(handle_id="h", patch_id=patch.patch_id, prev_snapshot="")

    def revert_data_patch(self, handle: PatchHandle) -> None:
        self._patched = False


def _golden() -> GoldenSet:
    return GoldenSet(
        version="niif-v1",
        items=(
            make_golden_item(
                item_id="it-0",
                question="q0",
                critical=True,
                span=make_span(doc_id="niif16", start=0, end=25, text="el span vigente de niif16"),
            ),
            make_golden_item(
                item_id="it-1",
                question="q1",
                critical=True,
                span=make_span(doc_id="doc-a", start=0, end=10),
            ),
            make_golden_item(item_id="it-2", question="q2", span=make_span(doc_id="doc-a")),
            make_golden_item(item_id="it-3", question="q3", span=make_span(doc_id="doc-a")),
        ),
    )


def _baseline(golden_set: GoldenSet) -> Baseline:
    per_item = tuple(
        PerItemResult(item_id=it.item_id, hit=True, critical=it.critical) for it in golden_set.items
    )
    ev = EvalResult(
        golden_set_version=golden_set.version,
        recall_span=1.0,
        per_item=per_item,
        ci=(1.0, 1.0),
        critical_recall=1.0,
    )
    return Baseline(version="bl-v1", eval_result=ev)


def _now() -> datetime:
    return datetime(2026, 7, 5, tzinfo=UTC)


def _propose_patch(dx, item) -> Patch:
    return Patch(
        patch_id="p-niif16",
        doc_id="niif16",
        new_content="el span vigente de niif16 vive aqui",
        rationale="reemplazar fuente vieja por versión vigente",
        patch_hash="h",
    )


def _run(rag, **resolvers):
    gs = _golden()
    return LoopOrchestrator().run_loop(
        rag,
        _baseline(gs),
        gs,
        confirm_patch=resolvers.get("confirm", lambda _p: ApprovalDecision.APPROVE),
        approve_deploy=resolvers.get("deploy", lambda _r: ApprovalDecision.APPROVE),
        propose_patch=_propose_patch,
        now=_now,
    )


def test_e2e_niif_corre_a_completada_con_recall_recuperado():
    rag = ScenarioRag()

    run = _run(rag)

    assert run.state is RunState.COMPLETADA
    assert run.status is RunStatus.COMPLETADA  # rollup grueso coherente
    assert run.diagnosis.capa.value == "fuente-vieja"
    assert (
        run.before is not None and run.after.recall_span == 1.0
    )  # before poblado, recall recuperado
    assert rag._patched is True  # el parche quedó aplicado (promovido)
    # BR-61: dos gates humanos distintos registrados en el run.
    assert {a.kind for a in run.approvals} == {
        ApprovalKind.CONFIRM_PATCH,
        ApprovalKind.APPROVE_DEPLOY,
    }


def test_sin_cambio_cuando_no_hay_caida():
    run = _run(ScenarioRag(niif16_ok=True))

    assert run.state is RunState.SIN_CAMBIO
    assert run.diagnosis is None  # ni siquiera investiga


def test_regresion_inyectada_en_parche_revierte():
    # El parche "arregla" niif16 pero rompe un ítem crítico → gate revierte (🔒 BR-34).
    rag = ScenarioRag(break_after="q1")

    run = _run(rag)

    assert run.state is RunState.REVERTIDA
    assert run.verdict.regressions_criticas >= 1
    assert rag._patched is False  # baseline intacto (BR-75), parche revertido


def test_reindex_falla_inconclusa_baseline_intacto():
    rag = ScenarioRag(reindex_fails=True)

    run = _run(rag)

    assert run.state is RunState.INCONCLUSA  # BR-65
    assert rag._patched is False


def test_us13_reject_detiene_humano_sin_aplicar():
    rag = ScenarioRag()

    run = _run(rag, confirm=lambda _p: ApprovalDecision.REJECT)

    assert run.state is RunState.DETENIDA_HUMANO  # BR-62
    assert rag._patched is False  # nunca se aplicó el parche


def test_us13_pending_pausa_en_esperando_confirmacion():
    rag = ScenarioRag()

    run = _run(rag, confirm=lambda _p: ApprovalDecision.PENDING)

    assert run.state is RunState.ESPERANDO_CONFIRMACION  # pausa, no terminal
    assert rag._patched is False


def test_us16_reject_rechazada_revierte_parche():
    rag = ScenarioRag()

    run = _run(rag, deploy=lambda _r: ApprovalDecision.REJECT)

    assert run.state is RunState.RECHAZADA
    assert rag._patched is False  # revertido a lo seguro


def test_reeval_post_parche_falla_revierte_inconclusa():
    # after inconclusa (RagError tras el parche) ⇒ revert + INCONCLUSA, baseline intacto (P1).
    rag = ScenarioRag(fail_after_patch=True)

    run = _run(rag)

    assert run.state is RunState.INCONCLUSA
    assert rag._patched is False  # revertido


def test_sin_data_ops_inconclusa():
    # BR-63/G1: si el RAG no soporta operaciones de datos, la rama de datos no está disponible.
    run = _run(ScenarioRag(no_data_ops=True))

    assert run.state is RunState.INCONCLUSA


def test_us16_pending_pausa_en_esperando_aprobacion():
    rag = ScenarioRag()

    run = _run(rag, deploy=lambda _r: ApprovalDecision.PENDING)

    assert run.state is RunState.ESPERANDO_APROBACION  # pausa (no terminal)
    assert rag._patched is True  # el parche ya está aplicado mientras espera aprobación


def test_selecciona_item_regresionado_no_el_cronico():
    # baseline con un ítem crónicamente fallido (primero en orden); solo niif16 regresiona.
    gs = GoldenSet(
        version="niif-v1",
        items=(
            make_golden_item(item_id="cronico", question="qX", span=make_span(doc_id="doc-a")),
            make_golden_item(
                item_id="it-0",
                question="q0",
                critical=True,
                span=make_span(doc_id="niif16", start=0, end=25, text="el span vigente de niif16"),
            ),
            make_golden_item(item_id="it-1", question="q1", span=make_span(doc_id="doc-a")),
            make_golden_item(item_id="it-2", question="q2", span=make_span(doc_id="doc-a")),
        ),
    )
    baseline = Baseline(
        version="bl-v1",
        eval_result=EvalResult(
            golden_set_version="niif-v1",
            recall_span=0.75,
            per_item=(
                PerItemResult(item_id="cronico", hit=False, critical=False),
                PerItemResult(item_id="it-0", hit=True, critical=True),
                PerItemResult(item_id="it-1", hit=True, critical=False),
                PerItemResult(item_id="it-2", hit=True, critical=False),
            ),
            ci=(0.75, 0.75),
            critical_recall=1.0,
        ),
    )

    run = LoopOrchestrator().run_loop(
        ScenarioRag(),
        baseline,
        gs,
        confirm_patch=lambda _p: ApprovalDecision.REJECT,
        approve_deploy=lambda _r: ApprovalDecision.APPROVE,
        propose_patch=_propose_patch,
        now=_now,
    )

    # Investigó it-0 (regresionó), NO "cronico" (que ya fallaba en baseline).
    assert run.diagnosis.evidencia == ("it-0:span_vigente_en_corpus",)


class _PartialRag:
    """Recupera el span PARCIALmente (miss en eval) pero todas las sondas dan bien → ambiguo."""

    def retrieve(self, question: str, k: int) -> list[Chunk]:
        return [Chunk(chunk_id="c", doc_id="doc-a", start=0, end=40, text="x", rank=0)]  # 40/100

    def generate(self, query: str, context: list[Chunk]) -> str:
        return "el span dorado presente"

    def get_config(self) -> dict:
        return {}

    def corpus_fingerprint(self) -> list[tuple[str, str]]:
        return [("doc-a", "el span dorado presente en el corpus")]

    def supports_data_ops(self) -> bool:
        return True


def test_localizador_ambiguo_degrada_a_inconclusa():
    # HIGH del review: si localize levanta (ambiguo/underspecified), el loop degrada a INCONCLUSA,
    # no crashea (P1).
    gs = GoldenSet(
        version="niif-v1",
        items=(
            make_golden_item(
                item_id="amb",
                question="q",
                critical=True,
                span=make_span(doc_id="doc-a", start=0, end=100, text="el span dorado"),
            ),
        ),
    )
    baseline = Baseline(
        version="bl-v1",
        eval_result=EvalResult(
            golden_set_version="niif-v1",
            recall_span=1.0,
            per_item=(PerItemResult(item_id="amb", hit=True, critical=True),),
            ci=(1.0, 1.0),
            critical_recall=1.0,
        ),
    )

    run = LoopOrchestrator().run_loop(
        _PartialRag(),
        baseline,
        gs,
        confirm_patch=lambda _p: ApprovalDecision.APPROVE,
        approve_deploy=lambda _r: ApprovalDecision.APPROVE,
        propose_patch=_propose_patch,
        now=_now,
    )

    assert run.state is RunState.INCONCLUSA  # capturó la excepción del localizador, no crasheó


def test_cg2_constructor_no_acepta_llmport():
    for param in inspect.signature(LoopOrchestrator.__init__).parameters.values():
        assert "llm" not in param.name.lower()
        assert "Llm" not in str(param.annotation)
    for param in inspect.signature(LoopOrchestrator.run_loop).parameters.values():
        assert "Llm" not in str(param.annotation)
