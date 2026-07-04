# Domain Entities — U1 · Camino NIIF

> **DDD táctico, tecnología-agnóstico.** Entities, Value Objects y Aggregates del dominio; el mapeo a Postgres/Pydantic llega en Infra Design y Code Generation.
> Alcance: solo la **rama de datos** (recall-por-span; sin faithfulness, sin config/Experimenter).
> Trazabilidad: los tipos de `component-methods.md` (Inception) se concretan aquí como building blocks DDD.

## Bounded Context
**Evaluación y corrección de la rama de datos de un RAG (Camino NIIF).**
Límite del contexto: **desde** un golden set etiquetado por span de fuente **hasta** un reporte antes/después auditable, pasando por medir (recall-por-span), localizar la capa del defecto (read-only), parchar los datos (con confirmación humana) y decidir con el gate de no-regresión.
**Fuera del contexto (otros bounded contexts / unidades):** faithfulness/LLM-juez (U3), rama de config y experimentación (U2), 2º paciente (U3). El **RAG objetivo** es un **sistema externo** al que se accede solo por el puerto `RagPatientPort` (P5); sus `Document`/`Chunk` entran al contexto como entidades externas de solo lectura.
**Lenguaje ubicuo:** span de fuente, recall-por-span, baseline, deriva ("fuente-vieja"), capa del defecto, claim verificable, gate de no-regresión, revert, corrida (run), clave de estado.

## Diagrama de relaciones (conceptual)

```text
Document ──< Chunk                (externos: corpus del RAG, tras el adaptador)
GoldenSet(v) ──< GoldenItem ──1── Span ──> Document      (span dorado apunta a un doc)
Baseline(v) ──1── EvalResult ──> GoldenSet(v)            (baseline congela una eval)
RunRecord ──1── EvalResult(before) , EvalResult(after)
RunRecord ──1── MonitorSignal
RunRecord ──1── ProbeResults ──1── Diagnosis ──1── Writeup
RunRecord ──0..1── Patch ──1── PatchHandle
RunRecord ──1── GateVerdict
RunRecord ──*── ApprovalRequest   (US-13 confirmar parche · US-16 aprobar deploy)
RunRecord ──1── Report
```

---

## Entities
*(objeto con **identidad propia** que persiste; su igualdad es por identidad, no por valor)*

### Operator *(actor — identidad externa)*
El humano que dispara corridas, confirma parches y aprueba deploys (Andrés/Carolina de `personas.md`).
- **Identidad:** `operator_id`
- **Atributos:** `operator_id`, `role ∈ {engineer, operador-admin}`
- **Comportamientos:** `confirm_patch()` (US-13), `approve_deploy()` / `reject()` (US-16). En U1 = operador único local (sin authn; ver ADR de seguridad mínima).

### GoldenItem
Un caso etiquetado del golden set (item = {pregunta, respuesta, span de fuente} + criticidad).
- **Identidad:** `item_id`
- **Atributos:** `item_id`, `question:str`, `answer:str` (referencia humana), `gold_span:Span`, `critical:bool` (clase crítica → un falso negativo = incidente), `slice:str?` (estrato)
- **Comportamientos:** ninguno mutante — es un **hecho etiquetado por un humano** (la verdad; BR-76). El acierto se **computa** en el Evaluator, no se guarda en el ítem.

### GoldenSet *(raíz de aggregate)*
Colección versionada e **inmutable por versión** de `GoldenItem`.
- **Identidad:** `version` (`GoldenSetVersion`, monótona)
- **Atributos:** `version`, `items: list[GoldenItem]`, `created_at`
- **Comportamientos:** se crea inmutable; **corregir = nueva versión** (nunca se muta una existente).

### Baseline
Un `EvalResult` **congelado** como referencia estable de comparación.
- **Identidad:** `version` (`BaselineVersion`)
- **Atributos:** `version`, `eval_result: EvalResult` (inmutable), `set_at`
- **Comportamientos:** `set_baseline(eval_result)` — **rechaza** si `len(items) < 50` (barra de significancia) o si la eval es `inconclusa`.

### Writeup *(read-only)*
Documento de incidente auditable producido por el investigador.
- **Identidad:** `writeup_id`
- **Atributos:** `writeup_id`, `sintoma:str`, `capa_localizada`, `evidencia:list[probe_id]`, `fix_prescrito:str`, `conclusion:str` (incluye "ninguna perilla lo arregla → datos" cuando aplica)
- **Comportamientos:** ninguno mutante — **read-only** (G3): no toca el sistema ni referencia un cambio ya aplicado.

### Patch *(rama de datos)*
Parche de datos propuesto (reemplazar/actualizar un `Document` del corpus).
- **Identidad:** `patch_id`
- **Atributos:** `patch_id`, `doc_id`, `new_content:str`, `rationale:str` (ligado al Writeup), `patch_hash`
- **Comportamientos:** `propose()` — se propone; **no se aplica sin confirmación humana** (US-13).

### PatchHandle
Recibo reversible de un parche aplicado.
- **Identidad:** `handle_id`
- **Atributos:** `handle_id`, `patch_id`, `prev_snapshot` (estado previo del doc + índice)
- **Comportamientos:** `revert()` — restaura doc + índice al estado previo exacto.

### ApprovalRequest *(gate humano P2)*
- **Identidad:** `request_id`
- **Atributos:** `request_id`, `kind ∈ {confirm-patch (US-13), approve-deploy (US-16)}`, `proposal_ref`, `decision ∈ {pending, approve, reject}` (default `pending`), `decided_by`, `decided_at`
- **Comportamientos:** `approve()`, `reject()`. **Invariante:** sin `approve`, nada avanza y el baseline se mantiene.

### RunRecord *(raíz de aggregate — la corrida)*
- **Identidad:** `run_id` — idempotente por la **clave de estado** (composición canónica: `nfr-design/nfr-design-patterns.md` §P-1)
- **Atributos:** `run_id`, `state:RunState` (máquina de estados, ver business-logic-model), `before/after:EvalResult`, `signal:MonitorSignal`, `diagnosis:Diagnosis`, `writeup_id`, `patch:Patch?`, `patch_handle:PatchHandle?`, `verdict:GateVerdict?`, `approvals:list[ApprovalRequest]`, `status ∈ {en-progreso, completada, inconclusa}`, `seed`
- **Comportamientos:** `advance(state)` (transiciones válidas de la máquina de estados), `record_decision()`. Garantiza la **consistencia transaccional** de toda la corrida.

### Document *(externo — pertenece al RAG, read-only vía adaptador)*
- **Identidad:** `doc_id`
- **Atributos:** `doc_id`, `text:str` (se normaliza para comparar spans), `version:str?` (permite detectar "fuente-vieja")
- **Comportamientos:** ninguno propio — Ratchet **no lo posee**; lo lee/parcha por el puerto.

### Chunk *(externo — lo produce el chunking del RAG)*
- **Identidad:** `chunk_id`
- **Atributos:** `chunk_id`, `doc_id`, `start:int`, `end:int` (offsets de carácter en `Document.text` normalizado), `text:str`, `rank:int` (posición en top-k)
- **Comportamientos:** ninguno — fragmento recuperable devuelto por `retrieve`.

---

## Value Objects
*(sin identidad; **definidos por su valor**; inmutables; igualdad por valor)*

### Span
El **span de fuente dorado**: la porción exacta del documento que responde la pregunta. Unidad de la métrica (`evaluacion.md`).
- **Valor que encapsula:** `(doc_id, start:int, end:int, text:str)` — offsets de carácter sobre texto normalizado.
- **Reglas de validación:** `start < end`; `len = end − start > 0`; los offsets se interpretan sobre el **mismo `normalize()`** que usa el recall (BL-1) y el `corpus_hash` (§P-1).

### EvalResult
Resultado (valor) de evaluar un RAG en cierto estado contra un `GoldenSet(v)`.
- **Valor que encapsula:** `golden_set_version`, `k:int` (default 5), `tau:float` (default 0.8), `recall_span:float` (métrica ancla determinista), `per_item:list[(item_id, hit:bool, critical:bool)]`, `ci:(float,float)`, `critical_recall:float` (derivado de `per_item`), `state_ref:StateRef`, `status ∈ {ok, inconclusa}`.
- **Reglas de validación:** `recall_span ∈ [0,1]`; `per_item` **pareable por `item_id`** (habilita gate pareado y guardrail 🔒); `faithfulness` **no existe en U1** (U3). **Por qué `critical` viaja en `per_item`:** el Gate recibe solo `EvalResult`+`Baseline` (no el `GoldenSet`); necesita la criticidad por ítem para computar `reg_crit` (BR-34).

### MonitorSignal
Señal (valor) de disparo del loop.
- **Valor que encapsula:** `triggered:bool`, `current:EvalResult`, `baseline_ref:BaselineVersion`, `delta:float` (`baseline.recall_span − current.recall_span`), `threshold:float` (default 0.05), `source ∈ {own-deploy, env-drift, unknown}`.
- **Reglas de validación:** una corrida `inconclusa` **no** dispara (`triggered=False`); clasificación fina de `source` = U3.

### ProbeResults
Hechos deterministas del `ProbeToolkit` por ítem fallido (**no juicios**).
- **Valor que encapsula (por ítem):** `span_indexado:bool`, `span_en_topk:bool`, `fronteras_de_chunk:ChunkBoundaryInfo`, `span_vigente_en_corpus:bool`, `respuesta_usa_span:bool` (containment textual, **no** faithfulness).
- **Reglas de validación:** cada campo lleva un `probe_id` citable como evidencia; ninguno usa LLM-juez.

### Diagnosis *(claim verificable — G3)*
Salida del `Localizer`. **Claim estructurado, no acción ni prosa libre.**
- **Valor que encapsula:** `capa ∈ {retrieval-miss, chunking, fuente-vieja, cobertura, generación}`, `evidencia:list[probe_id]`, `fix_layer ∈ {config, datos}` (U1: **datos**), `verified:bool`.
- **Reglas de validación (G3):** una `Diagnosis` sin `verified=True` (recomprobación determinista de `verify_claim`) **no habilita ninguna acción**; `capa` fuera del enum es inválida.

### GateVerdict *(determinista, sin LLM)*
Decisión (valor) del gate de no-regresión.
- **Valor que encapsula:** `decision ∈ {approve, revert}`, `delta:float`, `ci_delta:(float,float)`, `criterio:str` ("CI.lower ≥ 0"), `regressions_criticas:int`.
- **Reglas de validación:** `approve` **solo si** `ci_delta.lower ≥ 0`; `regressions_criticas > 0` ⇒ `revert` forzado (guardrail 🔒). Sin LLM.

### StateRef *(clave de estado canónica)*
Describe el estado del RAG que produjo un `EvalResult`.
- **Valor que encapsula:** la **clave de estado canónica** — composición, cómputo de hashes y enforcement (`UNIQUE(StateKey)`) tienen **un solo dueño**: `nfr-design/nfr-design-patterns.md` §P-1.
- **Reglas de validación:** deliberadamente **no** se re-enumera aquí (evita el drift que el erratum eliminó). Nombre + puntero a §P-1.

### Report *(proyección de resultado)*
Vista (valor) antes/después reproducible.
- **Valor que encapsula:** `run_id`, `recall_before/after` (con CI), `delta`, `ci_delta`, `change` (resumen del Patch), `writeup`, `decision ∈ {deploy, revert, pending, inconclusa}`, `reproducible_from:StateRef`.
- **Reglas de validación:** recomputable desde datos versionados (no se persiste como verdad independiente). **Mapeo veredicto→reporte** (`GateVerdict.decision ∈ {approve,revert}` ≠ `Report.decision`):

| GateVerdict / estado | Report.decision |
|---|---|
| `approve` + aprobación humana (US-16) | `deploy` |
| `revert` (empeora / regresión crítica / rechazo humano) | `revert` |
| `approve` a la espera de aprobación humana | `pending` |
| corrida `inconclusa` | `inconclusa` |

---

## Aggregates
*(grupo con una **raíz** que garantiza la consistencia de sus miembros)*

### Aggregate: GoldenSet
- **Raíz:** `GoldenSet`
- **Incluye:** `GoldenItem` (+ `Span` como Value Object embebido).
- **Invariante que garantiza la raíz:** inmutabilidad por versión; toda corrección crea una versión nueva. El acceso a los ítems es siempre por la versión.

### Aggregate: Baseline
- **Raíz:** `Baseline`
- **Incluye:** un `EvalResult` congelado.
- **Invariante:** solo se fija desde una eval `ok` con `len(items) ≥ 50`.

### Aggregate: RunRecord *(el central)*
- **Raíz:** `RunRecord`
- **Incluye:** `MonitorSignal`, `ProbeResults`, `Diagnosis`, `Writeup` (ref), `Patch` + `PatchHandle`, `GateVerdict`, `ApprovalRequest*`, `EvalResult` (before/after), `Report`.
- **Invariante que garantiza la raíz:** el ciclo de vida de la corrida es consistente y auditables sus transiciones (máquina de estados en `business-logic-model.md`); idempotente por la clave de estado (§P-1); en todo estado terminal salvo `PROMOVIDA/COMPLETADA`, **el baseline se mantiene**.

---

## Glosario de identidades de versión
- `GoldenSetVersion`, `BaselineVersion` — monótonas, inmutables por versión.
- `StateRef` / `StateKey` — clave de estado canónica; **dueño único** `nfr-design/nfr-design-patterns.md` §P-1.
