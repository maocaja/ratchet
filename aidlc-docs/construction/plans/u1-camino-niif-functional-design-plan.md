# Plan de Functional Design — U1 · Camino NIIF (walking skeleton)

> Fase: **CONSTRUCTION** · Unidad: **U1 · Camino NIIF** · Fecha: 2026-07-03
> Objetivo del artefacto: **lógica de negocio detallada, tecnología-agnóstica** para la rebanada vertical end-to-end de la **rama de datos** (escenario NIIF).
> Insumos: `unit-of-work.md` (U1), `unit-of-work-story-map.md`, `stories.md` (US-01, US-05, US-06a, US-07, US-08, US-10, US-11, US-13, US-03, US-14, US-16, US-17), `components.md`/`component-methods.md` (C1–C10, C12), reglas `.claude/rules/evaluacion.md`.
> Guardrails a preservar: **G1** (data-ops capability-flagged) · **G2** (Orchestrator/Gate sin LLM) · **G3** (investigador read-only, claim verificable). Regla de oro: **recall = determinista, faithfulness = juez (faithfulness NO está en U1)**.

## Alcance de U1 (lo que este Functional Design debe modelar)
`US-05` golden set → `US-06a` recall-por-span → `US-07` baseline → `US-08` monitor → `US-10` localizar "fuente-vieja" → `US-11` writeup → `US-13` parche+confirmación → `US-03` aplicar+reindex → `US-14` gate+revert → `US-16` aprobación humana → `US-17` reporte antes/después. Depende de `US-01` (adaptador conectado).

**Fuera de U1 (no modelar aquí):** faithfulness/LLM-judge (U3), rama config + Experimenter (U2), 2º paciente (U3), revert asimétrico completo (U3, Should), política de autonomía (U3, Should).

---

## Checklist de diseño

- [ ] **Domain entities** — `GoldenItem`/`GoldenSet`, `Span`, `Chunk`, `EvalResult`, `Baseline`, `MonitorSignal`, `ProbeResults`, `Diagnosis`, `Writeup`, `Patch`/`PatchHandle`, `GateVerdict`, `ApprovalRequest`, `Report`, `RunRecord`. Relaciones y versionado.
- [ ] **Business logic — recall-por-span** (determinista, C3): definición exacta de "el chunk cubre el span dorado".
- [ ] **Business logic — baseline y significancia** (C2/C3): bootstrap CI, gate de ≥50, inmutabilidad por versión.
- [ ] **Business logic — monitor** (C7): condición de disparo de caída vs. baseline.
- [ ] **Business logic — localizador "fuente-vieja"** (C4): sondas deterministas → claim `{capa, evidencia}` → `verify_claim`. Regla "ninguna perilla lo arregla → datos".
- [ ] **Business logic — writeup** (C4/C8): estructura (síntoma, capa, evidencia, capa de fix prescrita), read-only.
- [ ] **Business logic — parche de datos + confirmación humana** (C8→C1): propuesta, gate humano P2, aplicación + reindex, reversibilidad.
- [ ] **Business logic — gate de no-regresión + revert** (C6, determinista): re-evaluación, criterio "no empeora con CI", revert automático si empeora.
- [ ] **Business logic — LoopOrchestrator** (C9, G2): secuencia determinista de ruteo sobre la rama de datos; estados de la corrida.
- [ ] **Business logic — reporte antes/después** (C8): reproducible desde datos versionados.
- [ ] **Business rules** — consolidar invariantes y validaciones (≥50, inmutabilidad, idempotencia de corridas, read-only del investigador, "inconclusa" ante fallo).
- [ ] **Máquina de estados de la corrida** (RunRecord): de disparo a reporte, incluyendo ramas revert / rechazo / inconclusa.

---

## Preguntas de clarificación (rellenar `[Answer]:`)

> Las 4 marcadas ⭐ se preguntarán también de forma interactiva (son las de mayor peso). El resto son defaults razonables que confirmo si no hay respuesta.

### Q1 ⭐ — Definición de "el chunk cubre el span dorado" (núcleo de recall-por-span)
Un ítem "acierta" si algún chunk recuperado en top-k cubre el span dorado. ¿Qué cuenta como "cubre"?
- (A) **Contención total**: el span dorado está completamente dentro de un solo chunk.
- (B) **Solapamiento por umbral**: `overlap(chunk, span) / len(span) ≥ τ` (p.ej. τ=0.8), permite spans a caballo si un chunk cubre lo suficiente.
- (C) Otro.
[Answer]: **(B) Solapamiento por umbral τ=0.8** — `acierta = max_chunk(overlap(chunk,span)/len(span)) ≥ 0.8`, τ configurable.

### Q2 ⭐ — Cómo se localiza y compara el span (representación)
¿Sobre qué se computa el solapamiento del span?
- (A) **Offsets de carácter** `(doc_id, start, end)` sobre el texto fuente normalizado.
- (B) **Match textual normalizado** (normalizar espacios/acentos/case y buscar la subcadena del span en el texto del chunk).
- (C) Ambos: offsets como verdad, match textual como fallback.
[Answer]: **(A) Offsets de carácter** `Span=(doc_id, start, end)` sobre texto normalizado; overlap = intersección de intervalos.

### Q3 ⭐ — Criterio del gate "no empeora" (significancia)
El gate aprueba solo si el candidato no empeora vs. baseline. Criterio concreto:
- (A) **Límite inferior del CI del delta ≥ 0** (bootstrap pareado 95%): aprueba si con confianza no es peor.
- (B) **McNemar pareado** sobre aciertos/fallos por ítem, p<0.05 para afirmar mejora; "no empeora" = no hay regresión significativa.
- (C) Delta puntual ≥ 0 con margen fijo (más simple, menos riguroso).
[Answer]: **(A) CI inferior del delta ≥ 0** (bootstrap pareado 95%). `delta_i` pareado por ítem; aprueba ⇔ `CI.lower ≥ 0`.

### Q4 ⭐ — Umbral de disparo del monitor (US-08)
El monitor dispara el loop cuando la evaluación cae "por debajo del umbral vs. baseline". Concretamente:
- (A) **Caída absoluta** ≥ δ respecto al recall del baseline (p.ej. δ=0.05).
- (B) **Fuera del CI del baseline** (cae por debajo del límite inferior del CI del baseline).
- (C) Umbral configurable con default (A) δ=0.05.
[Answer]: **(A/C) Caída absoluta configurable, default δ=0.05.** `dispara ⇔ (baseline.recall − actual.recall) ≥ δ`.

### Q5 — `k` de top-k para retrieval/evaluación (US-06a)
Valor por defecto de `k` con el que se evalúa recall-por-span en U1.
[Answer]: ✅ **k=5, configurable por corrida** (default aplicado).

### Q6 — Reglas deterministas del localizador para las 5 capas
`stories.md` US-10 ya da la tabla. ¿Confirmamos estas reglas como deterministas y que el LLM (Localizer) solo se usa para redactar/priorizar cuando hay ambigüedad, no para decidir la capa cuando las sondas son concluyentes?
- retrieval-miss: span indexado ∧ ¬(span en top-k)
- chunking: span partido entre ≥2 chunks (ninguno lo cubre solo)
- fuente-vieja: ¬span_vigente_en_corpus (difiere/ausente) ← **capa del escenario NIIF**
- cobertura: ningún chunk cubre el tema (ni indexado)
- generación: span en top-k ∧ respuesta no lo usa
[Answer]: ✅ **Confirmado.** El LLM (Localizer) solo redacta/prioriza ante ambigüedad; **no decide la capa cuando las sondas son concluyentes** (G3). `verify_claim` recomprueba el claim de forma determinista.

### Q7 — Alcance de la confirmación humana en U1 (P2)
US-13 (confirmar parche) y US-16 (aprobar deploy) son dos gates humanos. En el walking skeleton, ¿son **dos** confirmaciones distintas (confirmar parche antes de aplicar + aprobar tras pasar el gate técnico) o se colapsan en **una** para la demo?
[Answer]: ✅ **Dos gates distintos** (US-13 confirmar parche antes de aplicar; US-16 aprobar tras pasar el gate técnico). Encadenables en la CLI para la demo.

### Q8 — Comportamiento ante fallo del RAG/entorno (regla P1)
Confirmar: ante fallo de retrieve/generate/reindex, la corrida se marca **"inconclusa"**, se mantiene el baseline y no se aplica ningún cambio. ¿Se auto-revierte un parche ya aplicado si el reindex falla a medias?
[Answer]: ✅ **Sí** — parche aplicado con reindex fallido ⇒ revert automático del parche + corrida marcada **"inconclusa"**, baseline intacto (P1).

### Q9 — Idempotencia y reproducibilidad de la corrida (NFR-2)
Confirmar: `record_run` idempotente por `(golden_set_version, config_hash, patch_hash)`; el reporte se recomputa desde datos versionados (no se "cachea" la métrica como verdad).
[Answer]: ✅ **Confirmado, con corrección (review):** clave = `(golden_set_version, config_hash, corpus_hash, patch_hash)`. Se añade **`corpus_hash`** porque el disparador de U1 es la deriva del corpus (fuente-vieja); sin él, dos señales antes/después de la deriva colisionarían. Reporte recomputable desde datos versionados (NFR-2).

---

## Salidas al aprobar
- `aidlc-docs/construction/u1-camino-niif/functional-design/domain-entities.md`
- `aidlc-docs/construction/u1-camino-niif/functional-design/business-logic-model.md`
- `aidlc-docs/construction/u1-camino-niif/functional-design/business-rules.md`
- (Sin `frontend-components.md`: U1 es API + CLI, sin UI.)
