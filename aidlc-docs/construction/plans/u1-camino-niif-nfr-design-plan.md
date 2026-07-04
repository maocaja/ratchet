# Plan de NFR Design — U1 · Camino NIIF

> Fase: **CONSTRUCTION** · Unidad: **U1 · Camino NIIF** · Fecha: 2026-07-03
> Objetivo: incorporar los NFR de U1 como **patrones de diseño + componentes lógicos**, tecnología-agnóstico. Dueño legítimo de la **clave de estado** (hashing/idempotencia).
> Insumos: `nfr-requirements/`, `functional-design/`, `audit.md` (erratum), carry-overs en `aidlc-state.md`.
> Salidas: `nfr-design/nfr-design-patterns.md`, `nfr-design/logical-components.md`.

## Carry-overs de etapas previas (arrastrados — se cierran aquí)
1. **Clave de estado canónica** — definir UNA vez; luego bajar a referencia los 3 literales del Functional Design (BR-73, `RunRecord.run_id`, `StateRef`).
2. **Precondición de determinismo del `retrieve`** — enunciarla como patrón de reproducibilidad.
3. **Ubicación de `k/τ`** — decisión abierta (Q1 ⭐).

## Checklist de diseño
- [ ] **Patrón de hashing de estado / idempotencia** — clave canónica, cómputo de cada hash, quién computa `corpus_hash` (corpus externo).
- [ ] **Patrón de reproducibilidad** — seed fijo del bootstrap; precondición de determinismo del `retrieve`; recompute desde datos versionados.
- [ ] **Patrón de frontera de agencia (G2/G3)** — cómo se *enforce* que `gate/` y `orchestrator/` no importen el cliente LLM.
- [ ] **Patrones de resiliencia** — política ante fallo de RAG/LLM/reindex (P1 → "inconclusa"); retry/backoff; atomicidad del deploy de datos + revert.
- [ ] **Patrón de gate humano (P2)** — dos aprobaciones (US-13/US-16) como componentes lógicos; estado `pending` no bloquea el sistema.
- [ ] **Componentes lógicos** — `StateHasher`, `BootstrapEstimator(seed)`, `RunRepository` (idempotente), `AgencyBoundary` (regla de import), `RetryPolicy`, ubicación de cada uno en `src/ratchet/<módulo>/`.
- [ ] **Reconciliación del Functional Design** — bajar los 3 literales a referencia (mismo diff, logueado).
- [ ] **No-metas** — sin colas/circuit-breaker/caché de LLM en U1 (endurecer); justificar cada skip de categoría.

## Justificación de categorías (framework Step 3)
- **Scalability:** N/A en U1 (un RAG, una corrida a la vez — Q5 NFR). Documentado como endurecer.
- **Security:** mínima (secrets por env, Security Baseline off). Sin patrón adicional.
- **Performance:** presupuesto blando <5min secuencial (ya decidido). Sin patrón de optimización en U1.
- **Resilience / Logical Components:** **sí aplican** → preguntas abajo.

---

## Preguntas de clarificación (rellenar `[Answer]:`)

### Q1 ⭐ — Ubicación de `k/τ` en la clave de estado (carry-over #3)
`config_hash` está definido como config del RAG (`get_config()`). `k`/`τ` son knobs de evaluación de **Ratchet**, no del RAG. ¿Cómo se modela para que dos corridas con distinto `k`/`τ` no deduplicen?
- (A) **`eval_params` explícito en la clave** (estado actual): clave = `(gs_version, config_hash, corpus_hash, patch_hash, eval_params=(k,τ))`. Semántica limpia (cada hash = su dueño); clave de 5 componentes.
- (B) **Renombrar a `run_config_hash`** que englobe config del RAG + `k/τ` en un solo hash. Clave más corta (4 comp.); mezcla dos orígenes bajo un nombre.
- (C) Otro.
[Answer]: ✅ **(A) `eval_params` explícito** — clave de 5: `(gs_version, config_hash, corpus_hash, patch_hash, eval_params=(k,τ))`. `config_hash` queda limpio (solo config del RAG). Ventaja colateral: la reconciliación del Functional Design no requiere renombrar, solo bajar literales a referencia.

### Q2 ⭐ — Política de resiliencia ante fallo de RAG/LLM en el skeleton
Arquitectura menciona retry+backoff+circuit-breaker (endurecer). Para U1 skeleton, ¿qué patrón?
- (A) **Retry acotado + backoff** (p.ej. 3 intentos) → si persiste, corrida `inconclusa`, baseline intacto. Sin circuit-breaker.
- (B) **Fail-fast sin retry** → primer fallo ⇒ `inconclusa`. Más simple; más frágil ante hipos transitorios.
- (C) Retry acotado + circuit-breaker mínimo. Más robusto; más código en el skeleton.
[Answer]: ✅ **(A) Retry acotado + backoff** (3 intentos) → si persiste, corrida `inconclusa`, baseline intacto (P1). Sin circuit-breaker (endurecer).

### Q3 ⭐ — Enforcement de la idempotencia (clave de estado) en persistencia
¿Cómo se garantiza "re-ejecutar no duplica"?
- (A) **Constraint UNIQUE en la clave de estado a nivel DB** + upsert idempotente. La DB es la última línea; imposible duplicar aunque falle la app.
- (B) **Chequeo a nivel de aplicación** antes de insertar. Más portable al fake in-memory; la DB no lo garantiza sola.
- (C) Ambos: constraint DB (verdad) + chequeo app (rápido/UX).
[Answer]: ✅ **(A) Constraint UNIQUE en la clave de estado a nivel DB** + upsert idempotente. La DB es la última línea; el fake in-memory replica la unicidad para tests.

### Q4 ⭐ — Enforcement de la frontera de agencia (G2)
¿Cómo se garantiza mecánicamente que `gate/` y `orchestrator/` no importen el cliente LLM?
- (A) **import-linter en CI** (regla declarativa: capas prohibidas). Mecánico, falla el build.
- (B) **Test que asevera** ausencia de import de LLM en esos paquetes (pytest). Vive con la suite.
- (C) Convención + code review (subagente `code-reviewer`). Sin gate automático.
[Answer]: ✅ **(A) import-linter en CI** (regla declarativa de capas prohibidas: `gate/` y `orchestrator/` no pueden importar `adapter/llm`/cliente LLM). El build falla si se viola. Complementable con el `code-reviewer` como segunda red.

### Q5 — Granularidad de `corpus_fingerprint` (default confirmable)
¿Cómo se compone la huella del corpus para `corpus_hash`?
[Answer]: ✅ Lista `(doc_id, sha256(doc_content_normalizado))` ordenada por `doc_id`; `corpus_hash = sha256(canonical_json(...))`. Un parche que cambia un doc cambia su `doc_content` ⇒ cambia `corpus_hash`. Sin merkle-tree (innecesario en U1).

---

## Salidas al aprobar
- `aidlc-docs/construction/u1-camino-niif/nfr-design/nfr-design-patterns.md`
- `aidlc-docs/construction/u1-camino-niif/nfr-design/logical-components.md`
- (Reconciliación: BR-73, `RunRecord.run_id`, `StateRef` del Functional Design bajados a referencia — mismo diff, logueado.)
