# Métodos de Componentes — Ratchet

> Firmas de métodos e I/O de alto nivel (Python-ish, ilustrativo). **Las reglas de negocio detalladas van en Functional Design (per-unit).**
> Tipos de dominio referenciados: `GoldenSet`, `EvalResult` (`recall_span: float`, `faithfulness: float`, `ci: (float,float)`), `Diagnosis` (`{capa, evidencia}`), `Variant`, `Patch`, `GateVerdict`, `Report`.

## C1 · RagAdapter  (`RagPatientPort`)
```python
# Lectura del lineage
def retrieve(query: str, k: int) -> list[Chunk]: ...
def generate(query: str, context: list[Chunk]) -> str: ...
# Config (siempre soportado)
def get_config() -> RagConfig: ...
def apply_config(cfg: RagConfig) -> ConfigHandle: ...      # atómico, reversible
def revert_config(handle: ConfigHandle) -> None: ...
# Datos (G1: capability-flagged)
def supports_data_ops() -> bool: ...
def apply_data_patch(patch: Patch) -> PatchHandle: ...     # reemplaza/actualiza doc
def reindex() -> None: ...
def revert_data_patch(handle: PatchHandle) -> None: ...
```

## C2 · GoldenSetRegistry
```python
def save_golden_set(items: list[GoldenItem]) -> GoldenSetVersion: ...   # item = {q, a, source_span}
def get_golden_set(version: GoldenSetVersion | None) -> GoldenSet: ...
def set_baseline(eval_result: EvalResult) -> BaselineVersion: ...       # rechaza si len < 50
def get_baseline() -> Baseline: ...
def record_run(run: RunRecord) -> RunId: ...          # idempotente
def record_decision(d: Decision) -> None: ...
def save_writeup(w: Writeup) -> WriteupId: ...
```

## C3 · Evaluator
```python
def evaluate(rag: RagPatientPort, gs: GoldenSet) -> EvalResult: ...
def recall_por_span(retrieved: list[Chunk], gold_span: Span) -> bool: ...   # determinista
def faithfulness(answer: str, gold: GoldenItem) -> float: ...               # LLM-judge (secundaria)
```

## C4 · Investigator
```python
# ProbeToolkit (deterministas) — devuelven hechos, no juicios
def span_en_topk(item: GoldenItem, k: int) -> bool: ...
def span_indexado(item: GoldenItem) -> bool: ...
def fronteras_de_chunk(item: GoldenItem) -> ChunkBoundaryInfo: ...
def span_vigente_en_corpus(item: GoldenItem) -> bool: ...
def respuesta_usa_span(item: GoldenItem, answer: str) -> bool: ...
# Localizer (LLM delgado) — G3: emite claim verificable, no acción
def localize(probe_results: ProbeResults) -> Diagnosis: ...   # {capa, evidencia:[probe_id]}
def write_incident(diagnosis: Diagnosis, evidence: ProbeResults) -> Writeup: ...   # read-only
# Verificación determinista del claim (cierra G3)
def verify_claim(diagnosis: Diagnosis) -> bool: ...
```

## C5 · Experimenter
```python
def propose_variants(diagnosis: Diagnosis, policy: Policy) -> list[Variant]: ...  # LLM propone, poda dirigida
def run_experiment(variant: Variant, rag: RagPatientPort, gs: GoldenSet) -> EvalResult: ...
```

## C6 · Gate  (determinista, sin LLM)
```python
def evaluate_change(candidate: EvalResult, baseline: Baseline) -> GateVerdict: ...  # aprueba solo si no empeora (CI)
def revert_if_worse(handle: ConfigHandle | PatchHandle, verdict: GateVerdict) -> None: ...
def classify_and_act(regression_source: Source) -> GateAction: ...   # deploy-propio→revert | deriva→re-experimentar
```

## C7 · Monitor
```python
def check(rag: RagPatientPort, baseline: Baseline) -> MonitorSignal: ...   # dispara si cae bajo umbral
def classify_source(signal: MonitorSignal) -> Source: ...                  # own-deploy | env-drift
```

## C8 · Reporter
```python
def build_report(run: RunRecord) -> Report: ...            # antes/después, reproducible
def request_approval(proposal: Proposal) -> ApprovalRequest: ...   # P2: gate humano
def record_approval(req: ApprovalRequest, decision: Literal["approve","reject"]) -> None: ...
```

## C9 · LoopOrchestrator  (G2: sin LLM.call)
```python
def run_loop(rag: RagPatientPort, gs: GoldenSet) -> Report: ...
# secuencia interna (rutea solo sobre datos deterministas):
#   Monitor.check → Investigator.localize+verify_claim → route(capa):
#     config → Experimenter.propose/run → Gate.evaluate_change
#     datos  → Reporter.request_approval → (si aprueba) RagAdapter.apply_data_patch+reindex → Gate.evaluate_change
#   → Gate.revert_if_worse → Reporter.build_report
```

## C10 · ApiCli
```python
POST /runs                # dispara una corrida
GET  /runs/{id}/report    # lee reporte
POST /approvals/{id}      # {approve|reject}   (P2)
# CLI espeja estos verbos: ratchet run | ratchet report <id> | ratchet approve <id>
```
