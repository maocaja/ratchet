# Business Rules — U1 · Camino NIIF

> Reglas de negocio en formato `RULE-[ID]` (runbook E5, Act 1). **`BR-xx` es nuestro prefijo de RULE** — se conserva porque `nfr-design` y los tests ya lo referencian (renombrar rompería cross-refs; alias, no refactor).
> Cada regla: **Descripción · Condición · Consecuencia · Fuente · Test.** Origen general: `.claude/rules/evaluacion.md`, `stories.md` (Gherkin), decisiones del Functional Design.

---

## Métrica y evaluación (BR-1x)

### RULE BR-11: Recall determinista, recomputado
- **Descripción:** `recall_span` se **recomputa** desde `per_item`; nunca se lee de caché como verdad.
- **Condición:** cualquier lectura/uso del recall.
- **Consecuencia:** el test recomputa el recall; si difiere del persistido, falla.
- **Fuente:** `evaluacion.md` (regla de oro) · US-06a.
- **Test:** recomputar en el test (no hardcode).

### RULE BR-12: Cobertura del span por umbral τ
- **Descripción:** `hit(item) ⇔ max_chunk( overlap(chunk, gold_span)/len(gold_span) ) ≥ τ`, τ=0.8.
- **Condición:** evaluación de cada ítem contra top-k.
- **Consecuencia:** un chunk que cubre < τ del span no cuenta como acierto.
- **Fuente:** plan Functional Design Q1.
- **Test:** PBT — invariantes de cobertura.

### RULE BR-13: Overlap solo dentro del mismo documento
- **Descripción:** solo cuentan chunks con `chunk.doc_id == span.doc_id`.
- **Condición:** cómputo de `cubre(chunk, span)`.
- **Consecuencia:** overlap entre docs distintos = 0.
- **Fuente:** plan Q2 (offsets).
- **Test:** edge test.

### RULE BR-14: Overlap por intersección de intervalos
- **Descripción:** el overlap se computa por **intersección de intervalos de offsets** sobre texto normalizado.
- **Condición:** cómputo determinista de cobertura.
- **Consecuencia:** overlap ∈ [0,1], monótono.
- **Fuente:** plan Q2.
- **Test:** PBT — overlap ∈ [0,1], monótono.

### RULE BR-15: Faithfulness fuera de U1
- **Descripción:** **faithfulness NO se computa ni decide en U1** (llega en U3); el gate se ancla **solo** en `recall_span`.
- **Condición:** toda decisión del gate/monitor en U1.
- **Consecuencia:** ninguna ruta de decisión de U1 consulta faithfulness.
- **Fuente:** `evaluacion.md` · PRD Seg 8 #8.
- **Test:** ausencia de faithfulness en el gate.

### RULE BR-16: No decidir con datos incompletos
- **Descripción:** ante fallo de RAG/LLM/entorno, la corrida es **"inconclusa"**; no se decide, se mantiene baseline.
- **Condición:** excepción en `retrieve`/`generate`/`reindex`.
- **Consecuencia:** `status=inconclusa`; baseline intacto (P1).
- **Fuente:** `python.md` (P1) · arquitectura SPOF.
- **Test:** inyectar `RagError`.

---

## Golden set y baseline (BR-2x)

### RULE BR-21: Golden set inmutable por versión
- **Descripción:** el golden set es **inmutable por versión**; toda corrección crea una versión nueva.
- **Condición:** cualquier intento de modificar una versión existente.
- **Consecuencia:** error; se exige nueva versión.
- **Fuente:** `evaluacion.md` · NFR-2.
- **Test:** intento de mutación → error.

### RULE BR-22: Baseline exige ≥50 ítems
- **Descripción:** **no se fija baseline con `len(items) < 50`** (barra de significancia).
- **Condición:** `set_baseline`.
- **Consecuencia:** reject.
- **Fuente:** `evaluacion.md` · US-05.
- **Test:** factory con 49 ítems → reject.

### RULE BR-23: ≥50 por rebanada
- **Descripción:** la barra ≥50 se dimensiona **por rebanada/estrato** de la que se afirme algo, no por nº de documentos.
- **Condición:** afirmación de mejora sobre un slice.
- **Consecuencia:** un slice con < 50 no soporta afirmación.
- **Fuente:** `evaluacion.md`.
- **Test:** test por slice.

### RULE BR-24: GoldenItem bien formado
- **Descripción:** cada `GoldenItem` requiere `gold_span` válido (`len>0`) y marca `critical`.
- **Condición:** registro del golden set.
- **Consecuencia:** ítem inválido → rechazo del set.
- **Fuente:** `evaluacion.md`.
- **Test:** validación de factory.

### RULE BR-25: No baseline desde inconclusa
- **Descripción:** no se fija baseline desde una corrida `inconclusa`.
- **Condición:** `set_baseline` con eval `status≠ok`.
- **Consecuencia:** reject.
- **Fuente:** P1.
- **Test:** eval inconclusa → reject.

---

## Significancia y gate (BR-3x — el corazón)

### RULE BR-31: Gate determinista, sin LLM (G2)
- **Descripción:** el gate decide **solo con `per_item` + CI**; no importa el cliente LLM.
- **Condición:** toda decisión de deploy/revert.
- **Consecuencia:** import de LLM en `gate/` ⇒ build falla (import-linter).
- **Fuente:** G2 · `evaluacion.md`.
- **Test:** grep/import-linter: gate sin cliente LLM.

### RULE BR-32: Aprueba solo si no empeora con significancia
- **Descripción:** aprueba **solo si** `CI.lower(delta_pareado) ≥ 0`.
- **Condición:** re-evaluación de un candidato vs. baseline.
- **Consecuencia:** si `CI.lower < 0` → revert.
- **Fuente:** `evaluacion.md` · US-14 · plan Q3.
- **Test:** regresión inyectada → revert.

### RULE BR-33: Delta pareado por ítem
- **Descripción:** el delta se computa **pareado por `item_id`** (misma `golden_set_version`).
- **Condición:** `evaluate_change`.
- **Consecuencia:** comparación no pareada es inválida.
- **Fuente:** `evaluacion.md`.
- **Test:** test pareado.

### RULE BR-34: Guardrail 🔒 de clase crítica
- **Descripción:** cualquier regresión en **clase crítica** (`base_hit=1 ∧ cand_hit=0` sobre `critical=True`) ⇒ revert inmediato, sin importar el delta agregado. **0 regresiones no detectadas dentro de cobertura.**
- **Condición:** `evaluate_change`; criticidad viaja en `EvalResult.per_item` (computable sin el `GoldenSet`).
- **Consecuencia:** `reg_crit > 0` ⇒ `revert` forzado; un falso negativo crítico = incidente.
- **Fuente:** `evaluacion.md` (guardrail).
- **Test:** inyectar regresión crítica que no baja el agregado.

### RULE BR-35: Revert automático, sin humano
- **Descripción:** si el gate decide `revert`, el revert es **automático**; revertir a lo seguro nunca pide aprobación.
- **Condición:** `verdict.decision == revert`.
- **Consecuencia:** se restaura el estado previo sin gate humano (P2).
- **Fuente:** P1/P2 · US-14.
- **Test:** revert sin approval.

### RULE BR-36: Bootstrap con seed fijo
- **Descripción:** el bootstrap usa **seed fijo** por corrida ⇒ CI reproducible.
- **Condición:** cómputo de cualquier CI.
- **Consecuencia:** mismo input+seed → mismo CI bit a bit.
- **Fuente:** NFR-2.
- **Test:** mismo input+seed → mismo CI.

### RULE BR-37: Revert simétrico en U1
- **Descripción:** en U1 el revert es **simétrico** (empeora → revierte). El **asimétrico** (US-15) queda fuera.
- **Condición:** decisión de revert en U1.
- **Consecuencia:** no se distingue deriva vs. deploy propio (U3).
- **Fuente:** alcance U1 · US-15 (U3).
- **Test:** — (alcance).

---

## Monitor (BR-4x)

### RULE BR-41: Disparo por umbral δ
- **Descripción:** dispara ⇔ `(baseline.recall_span − current.recall_span) ≥ δ`, δ=0.05 configurable.
- **Condición:** evaluación disparada.
- **Consecuencia:** `triggered=True` → entra al loop.
- **Fuente:** US-08 · plan Q4.
- **Test:** eval bajo umbral → triggered.

### RULE BR-42: Misma versión de golden set
- **Descripción:** el monitor mide contra la **misma `golden_set_version`** del baseline.
- **Condición:** `Monitor.check`.
- **Consecuencia:** comparar contra otra versión es inválido.
- **Fuente:** NFR-2.
- **Test:** test de versión.

### RULE BR-43: Inconclusa no dispara
- **Descripción:** una corrida `inconclusa` **no** dispara el loop.
- **Condición:** `current.status == inconclusa`.
- **Consecuencia:** `triggered=False`.
- **Fuente:** P1.
- **Test:** eval inconclusa → ¬triggered.

### RULE BR-44: Clasificación de origen fuera de U1
- **Descripción:** clasificación fina de origen (own-deploy vs env-drift) **no** es requisito de U1.
- **Condición:** — .
- **Consecuencia:** `source` queda `unknown` en U1.
- **Fuente:** US-09 (U3).
- **Test:** — (alcance).

---

## Investigador y localizador (BR-5x — G3)

### RULE BR-51: Investigador read-only
- **Descripción:** el investigador emite `Diagnosis {capa, evidencia}` y `Writeup`; **no aplica** cambios.
- **Condición:** toda la fase de investigación.
- **Consecuencia:** no invoca `apply_*`; la acción la ejecuta otro componente.
- **Fuente:** G3 · US-10.
- **Test:** grep: investigator no llama apply_*.

### RULE BR-52: Capa determinista, LLM solo desambigua
- **Descripción:** la **capa se decide de forma determinista** donde las sondas son concluyentes; el LLM solo prioriza ante ambigüedad y no inventa capa fuera del enum.
- **Condición:** `localize`.
- **Consecuencia:** en el camino NIIF el LLM no interviene (regla concluyente dispara antes).
- **Fuente:** G3 · plan Q6.
- **Test:** PBT sobre `localize_rules`.

### RULE BR-53: Enum de capas cerrado
- **Descripción:** `capa ∈ {retrieval-miss, chunking, fuente-vieja, cobertura, generación}`.
- **Condición:** salida del localizador.
- **Consecuencia:** cualquier otro valor es inválido.
- **Fuente:** US-10.
- **Test:** validación de enum.

### RULE BR-54: Claim verificable habilita acción
- **Descripción:** `verify_claim` recomprueba la evidencia; una `Diagnosis` con `verified=False` **no habilita ninguna acción**.
- **Condición:** antes de rutear a fix.
- **Consecuencia:** claim no verificado ⇒ `inconclusa`.
- **Fuente:** G3.
- **Test:** claim falso → no acción.

### RULE BR-55: "fuente-vieja" ⇔ span no vigente
- **Descripción:** **"fuente-vieja" ⇔ `span_vigente_en_corpus = False`**; implica `fix_layer = datos`.
- **Condición:** sonda `span_vigente_en_corpus`.
- **Consecuencia:** "ninguna perilla lo arregla" → rama datos (escenario NIIF).
- **Fuente:** US-10 · escenario NIIF.
- **Test:** escenario NIIF e2e.

### RULE BR-56: Writeup read-only
- **Descripción:** el `Writeup` no muta el sistema ni referencia un cambio ya aplicado; declara "→ capa de datos" cuando aplica.
- **Condición:** cierre de la investigación.
- **Consecuencia:** writeup desacoplado del cambio.
- **Fuente:** G3 · US-11.
- **Test:** test de contenido.

### RULE BR-57: Ninguna sonda usa LLM-judge
- **Descripción:** `respuesta_usa_span` es **containment textual** (subcadena normalizada), NO faithfulness; todas las sondas son deterministas.
- **Condición:** `ProbeToolkit`.
- **Consecuencia:** las sondas no importan el cliente LLM.
- **Fuente:** `evaluacion.md` · U3 (faithfulness).
- **Test:** grep: probes sin cliente LLM.

### RULE BR-58: Capa `cobertura` underspecified (U2)
- **Descripción:** `cobertura` tiene `fix_layer` underspecified (datos vs config); se resuelve en U2.
- **Condición:** sonda `¬span_indexado`.
- **Consecuencia:** no se dispara en el camino no-negociable de U1.
- **Fuente:** alcance U1/U2.
- **Test:** — (nota de alcance).

---

## Rama de datos, confirmación y aplicación (BR-6x — G1, P2)

### RULE BR-61: Dos gates humanos distintos
- **Descripción:** US-13 (confirmar parche **antes** de aplicar) y US-16 (aprobar deploy **tras** el gate técnico) son dos aprobaciones.
- **Condición:** rama de datos.
- **Consecuencia:** dos `ApprovalRequest` con `kind` distinto.
- **Fuente:** P2 · US-13, US-16.
- **Test:** dos ApprovalRequest.

### RULE BR-62: Nada se aplica sin confirmación
- **Descripción:** **nada se aplica sin confirmación humana** (US-13).
- **Condición:** antes de `apply_data_patch`.
- **Consecuencia:** sin `approve` ⇒ `DETENIDA_HUMANO`, baseline intacto.
- **Fuente:** P2 · US-13.
- **Test:** reject → no apply.

### RULE BR-63: G1 capability-flag
- **Descripción:** si `supports_data_ops()` es falso, la rama de datos se marca no-disponible y aplica fallback — no rompe P5.
- **Condición:** inicio de la rama de datos.
- **Consecuencia:** paciente sin data-ops ⇒ fallback documentado.
- **Fuente:** G1.
- **Test:** flag falso → fallback.

### RULE BR-64: Parche atómico y reversible
- **Descripción:** `apply_data_patch` es **atómico y reversible**; `PatchHandle` restaura doc + índice al estado previo exacto.
- **Condición:** aplicación de parche.
- **Consecuencia:** `apply→revert` = estado previo.
- **Fuente:** US-03 · arquitectura SPOF (deploy a medias).
- **Test:** apply→revert = estado previo.

### RULE BR-65: Reindex falla ⇒ revert + inconclusa
- **Descripción:** si el `reindex` falla tras aplicar ⇒ **revert automático + corrida `inconclusa`**.
- **Condición:** excepción en `reindex`.
- **Consecuencia:** el parche no queda a medias; baseline intacto.
- **Fuente:** P1 · plan Q8.
- **Test:** inyectar `ReindexError`.

### RULE BR-66: Rechazo humano ⇒ revert
- **Descripción:** un rechazo en US-16 sobre un parche ya aplicado ⇒ **revert del parche**.
- **Condición:** `approve-deploy` = reject con parche aplicado.
- **Consecuencia:** no queda a medias → `RECHAZADA`.
- **Fuente:** P2 · US-16.
- **Test:** reject deploy → revert.

---

## Orquestación, reporte y persistencia (BR-7x — G2, NFR-2)

### RULE BR-71: Orchestrator sin LLM (G2)
- **Descripción:** el `LoopOrchestrator` **no contiene `LLM.call()`**; rutea solo sobre datos deterministas.
- **Condición:** toda la orquestación.
- **Consecuencia:** import de LLM en `orchestrator/` ⇒ build falla (import-linter).
- **Fuente:** G2.
- **Test:** grep/import-linter: orchestrator sin cliente LLM.

### RULE BR-72: Ruteo sobre claim verificado
- **Descripción:** el ruteo por capa usa `Diagnosis.fix_layer` **ya verificado**; el orquestador no re-razona la capa.
- **Condición:** `route(fix_layer)`.
- **Consecuencia:** ruteo determinista.
- **Fuente:** G2/G3.
- **Test:** test de ruteo.

### RULE BR-73: Idempotencia por clave de estado
- **Descripción:** `record_run` es **idempotente** por su **clave de estado** (composición y hashes: `nfr-design/nfr-design-patterns.md §P-1`); enforced por `UNIQUE(StateKey)` en DB.
- **Condición:** persistir una corrida.
- **Consecuencia:** re-ejecutar no duplica ni corrompe.
- **Fuente:** NFR-2 · §P-1.
- **Test:** doble record → 1 run; deriva de corpus → 2 runs; distinto `k`/`τ` → 2 runs.

### RULE BR-74: Reporte reproducible
- **Descripción:** el `Report` es **recomputable** desde datos versionados; la métrica no se persiste como verdad independiente.
- **Condición:** construir/leer un reporte.
- **Consecuencia:** el reporte se recomputa y coincide.
- **Fuente:** NFR-2.
- **Test:** recomputar report.

### RULE BR-75: Baseline se mantiene salvo COMPLETADA
- **Descripción:** en todo estado terminal salvo `PROMOVIDA/COMPLETADA`, **el baseline se mantiene**.
- **Condición:** cualquier terminal (revert/rechazo/inconclusa/detenida).
- **Consecuencia:** el sistema nunca queda peor que el baseline.
- **Fuente:** P1/P2.
- **Test:** tests por estado terminal.

### RULE BR-76: La verdad es el golden set humano
- **Descripción:** la **verdad es el golden set** que definió un humano; Ratchet enforca coincidir con esa verdad, no la inventa.
- **Condición:** toda decisión de Ratchet.
- **Consecuencia:** no se recomputa la verdad; se recupera de fuente versionada (CG-4).
- **Fuente:** `docs/critica.md` (versiones contradictorias) · `evaluacion.md`.
- **Test:** — (principio).

---

## Regresiones inyectadas (obligatorio — testing.md)
Todo el gate/localizador se acompaña de tests que **inyectan una regresión conocida** y verifican que el gate/revert la atrapa (**0 no detectadas dentro de cobertura**, BR-34). Mínimo: (a) parche que baja el recall agregado; (b) parche que rompe un ítem de **clase crítica** sin bajar el agregado; (c) claim de localización falso que `verify_claim` debe rechazar.
