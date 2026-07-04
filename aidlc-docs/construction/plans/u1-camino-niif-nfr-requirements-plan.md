# Plan de NFR Requirements (ligero) — U1 · Camino NIIF

> Fase: **CONSTRUCTION** · Unidad: **U1 · Camino NIIF** · Fecha: 2026-07-03
> Objetivo: aterrizar los NFR de U1 en **criterios concretos y testeables** + fijar el **tech stack** de la unidad.
> **Ligero por diseño:** `specs/arquitectura.md` Seg 3 ya fijó el top-3 (Confiabilidad, Reproducibilidad, Extensibilidad) y Seg 4 los SPOF. Aquí NO se re-decide eso; se traduce a U1 y se cierran las pocas decisiones abiertas.
> Extensión **Security Baseline = No** (Requirements): sin NFR de seguridad más allá de manejo básico de secrets (keys LLM).

## NFR heredados de arquitectura (NO se re-preguntan — se acotan a U1)
| # | NFR (arquitectura) | Cómo aplica a U1 |
|---|---|---|
| NFR-1 | **Confiabilidad/Corrección** | gate no-regresión + revert automático + anclaje en recall determinista + guardrail 🔒 (0 regresiones críticas). Ya modelado en BR-3x. |
| NFR-2 | **Reproducibilidad/Auditabilidad** | versionar gs+config+corpus+resultados; recomputar recall+CI; corridas idempotentes; seed fijo. Ya en BR-7x. |
| NFR-3 | **Extensibilidad** | adaptador `RagPatientPort` por interfaz; módulos con costuras. Ya en `python.md`. |
| — | **Escala/latencia/costo** | arquitectura: fuera del top-3, sin SLA. En U1 = walking skeleton síncrono in-process, un RAG, una corrida a la vez. |

## Checklist de NFR (U1)
- [ ] **Confiabilidad** — criterios testeables del gate/revert/guardrail crítico (ya cubierto por business-rules; referenciar, no duplicar).
- [ ] **Reproducibilidad** — bit-exactitud del recompute determinista; alcance (qué queda fuera por depender del LLM).
- [ ] **Performance (blando)** — presupuesto de una corrida del loop para la demo; B del bootstrap.
- [ ] **Disponibilidad/Fault-tolerance** — comportamiento ante caída de RAG/reindex (P1); en skeleton el fallo es visible y se re-corre.
- [ ] **Persistencia/Durabilidad** — motor de datos de U1 (decisión abierta: SQLite-first vs Postgres desde el arranque).
- [ ] **Mantenibilidad/Testabilidad** — cobertura mínima, PBT en el núcleo, e2e del escenario NIIF (ya en testing.md; referenciar).
- [ ] **Observabilidad/Audit trail (mínimo)** — qué se registra por corrida y decisión.
- [ ] **Seguridad (mínima)** — solo manejo de secrets (keys LLM); Security Baseline off.
- [ ] **Tech stack de U1** — consolidar versiones concretas (Python, FastAPI, libs de stats, etc.).

---

## Preguntas de clarificación (rellenar `[Answer]:`)

> Las 3 ⭐ se preguntan también interactivamente. El resto son defaults confirmables.

### Q1 ⭐ — Motor de persistencia para U1 (walking skeleton)
`arquitectura.md` fija PostgreSQL como destino. Para el **skeleton**, ¿arrancamos ya con Postgres o con SQLite y migramos?
- (A) **Postgres desde el arranque** (docker-compose): fiel al destino, sin sorpresas de migración, un poco más de fricción local.
- (B) **SQLite-first** detrás del repo/puerto de persistencia, migrar a Postgres al endurecer: arranque más rápido, riesgo de fugas SQL-específicas.
- (C) Otro.
[Answer]: ✅ **(A) Postgres desde el arranque** (docker-compose) — recomendación aceptada. Persistencia **detrás del puerto/repo**: tests unitarios contra *fake* in-memory; integración/e2e contra Postgres real. Razón: NFR-2 (idempotencia por clave compuesta + versionado inmutable) es NFR estrella y debe probarse en el motor real.

### Q2 ⭐ — Presupuesto de latencia de una corrida del loop (para la demo)
Arquitectura dice "sin SLA". Pero para Demo Day, ¿hay un **target blando** de cuánto debe tardar una corrida completa del loop (evaluar gs≥50 + investigar + parche + re-eval)?
- (A) **< 60 s** por corrida (demo fluida) — puede exigir paralelizar `retrieve` sobre el golden set.
- (B) **< 5 min**, sin optimizar (secuencial simple) — más fácil, demo con una pausa.
- (C) Sin target; lo que tarde (prioridad total a correctitud).
[Answer]: ✅ **(B) < 5 min, secuencial.** Evaluación secuencial de gs≥50; sin optimización prematura. Correctitud sobre velocidad; la paralelización de `retrieve` queda como mejora opcional si sobra tiempo.

### Q3 ⭐ — Alcance de la garantía de reproducibilidad (NFR-2)
¿Qué prometemos que es **bit-exacto** al recomputar desde datos versionados?
- (A) **Solo lo determinista** (recall_span, per_item, CI con seed fijo) es bit-exacto; lo que toca el LLM (generación/respuesta) NO se promete reproducible y se excluye explícitamente.
- (B) Todo, cacheando también las salidas del LLM por (query, corpus, config) para poder re-servirlas.
- (C) Otro.
[Answer]: ✅ **(A) Solo lo determinista** es bit-exacto (recall_span, per_item, CI con seed fijo). Lo que toca el LLM (generación/respuesta) **se excluye explícitamente** de la garantía. Coherente con la regla de oro y con no hacer del juez un SPOF.

### Q4 — B del bootstrap (precisión vs. tiempo)
Nº de remuestreos del bootstrap para el CI.
[Answer]: ✅ **B=1000**, seed fijo, configurable.

### Q5 — Concurrencia de corridas en U1
¿U1 necesita correr múltiples loops en paralelo?
[Answer]: ✅ **No** — una corrida a la vez, síncrona in-process (Job Runner real = endurecer). El gate humano ya es un cuello deliberado.

### Q6 — Observabilidad mínima de U1
¿Qué se registra por corrida?
[Answer]: ✅ Log estructurado por transición de estado del RunRecord + persistir writeup, verdict, approvals y decisiones (audit trail). Sin métricas/tracing externos (LangFuse = endurecer).

### Q7 — Manejo de secrets (keys LLM)
Security Baseline off; solo confirmar higiene mínima.
[Answer]: ✅ Keys por variable de entorno / `.env` no versionado; nunca en código ni en el repo. Sin gestor de secrets en MVP.

---

## Salidas al aprobar
- `aidlc-docs/construction/u1-camino-niif/nfr-requirements/nfr-requirements.md`
- `aidlc-docs/construction/u1-camino-niif/nfr-requirements/tech-stack-decisions.md`
