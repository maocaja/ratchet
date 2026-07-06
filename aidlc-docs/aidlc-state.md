# AI-DLC State Tracking

## Project Information
- **Project Name**: Ratchet
- **Project Type**: Greenfield
- **AI-DLC Version**: v0.1.8 (AWS Labs aidlc-workflows)
- **Start Date**: 2026-07-03T01:21:55Z
- **Current Stage**: CONSTRUCTION · **U1 COMPLETO** (Code Gen + Build&Test ✅ — 14 tareas RAT-5…18, 184 tests, CI 4 gates, G2 KEPT). **Pivote v2 (2026-07-05):** reencuadre agéntico (`definicion.md`) → la unidad actual es **U2 · Investigador Agéntico**. Ver *Re-scope de unidades v2* abajo.

## Workspace State
- **Existing Code**: No
- **Reverse Engineering Needed**: No
- **Workspace Root**: /Users/mauricio/dev/ratchet

## Inputs (pre-AI-DLC artifacts)
- `specs/prd.md` — PRD completo (13 segmentos) — insumo principal de Requirements
- `specs/arquitectura.md` — Arquitectura v1 (C4 + NFR + SPOF)
- `docs/definicion.md` — **estrella polar v2 (agéntica, 2026-07-05)**; v1 preservada en `definicion-v1-eval.md`. Contexto del pivote: `docs/critica-panel-agentico.md` + `docs/investigacion-2026.md`. También `pvb.md`, `critica.md`.

## Code Location Rules
- **Application Code**: Workspace root (NEVER in aidlc-docs/)
- **Documentation**: aidlc-docs/ only
- **Structure patterns**: See code-generation.md Critical Rules

## Execution Plan Summary
- **Total Stages to Execute**: 8 (Application Design, Units Generation, Functional Design, NFR Requirements, NFR Design, Infrastructure Design [min], Code Generation, Build and Test)
- **Stages Skipped**: Reverse Engineering (greenfield)
- **Strategy**: walking-skeleton-first — unidad del Camino NIIF primero, end-to-end

## Stage Progress
### 🔵 INCEPTION PHASE
- [x] Workspace Detection
- [x] Reverse Engineering (SKIPPED — greenfield)
- [x] Requirements Analysis
- [x] User Stories
- [x] Workflow Planning
- [x] Application Design — EXECUTE
- [x] Units Generation — EXECUTE

**✅ FASE INCEPTION COMPLETA (2026-07-03).** Siguiente: CONSTRUCTION por unidad, empezando por U1 · Camino NIIF.

### 🟢 CONSTRUCTION PHASE
**U1 · Camino NIIF — COMPLETO ✅** (14 tareas RAT-5…18, 184 tests, CI 4 gates, G2 KEPT; incluye el fix del falso positivo de `cubre()` — 🔒 BR-34). Bitácora del detalle: memoria `u1-completo.md`.
- [x] Functional Design — EXECUTE (U1, aprobado 2026-07-03)
- [x] NFR Requirements — EXECUTE (ligero) (U1, aprobado 2026-07-03)
- [x] NFR Design — EXECUTE (U1, aprobado 2026-07-03)
- [x] Infrastructure Design — EXECUTE (mínimo) (U1, aprobado 2026-07-03)
- [x] Code Generation — EXECUTE (U1 ✅ — se levantó la pausa)
- [x] Build and Test — EXECUTE (U1 ✅ — 184 tests, e2e NIIF hermético)

**U2 · Investigador Agéntico — SIGUIENTE** → sub-cascada propia (Requirements → Functional → NFR → Infra → Code Gen → Build&Test), igual que U1.

## Re-scope de unidades v2 (2026-07-06) — tras el pivote agéntico
Loop-back deliberado en la cascada (HITL, forward-only; registrado en `audit.md`). Regla del framework respetada: **1 propósito por unidad.** Las unidades originales de Inception quedan como registro histórico (`unit-of-work.md` lleva la nota de reconciliación).

| Unidad | Propósito único | Estado |
|---|---|---|
| **U1** | 🔒 Sustrato determinista (Camino NIIF) | ✅ completo — intacto |
| **U2** | **Investigador Agéntico:** incidente de contradictorios + loop de razonamiento + RAG externo propio (ADR-008) + **eval del agente** + *definir* la política de autonomía | siguiente |
| **U3** | Credibilidad: 2º paciente (AnythingLLM) + faithfulness + robustez | diferido |
| **U4 / backlog** | Rama config + Experimenter + *demostrar* el auto-config | diferido **explícito** (no enterrado) |

### 🟡 OPERATIONS PHASE
- [ ] Operations — PLACEHOLDER

## Carry-overs — registro
### ✅ Cerrados en NFR Design (2026-07-03)
1. **Clave de estado canónica** — definida UNA vez en `nfr-design-patterns.md §P-1`; los 3 literales del FD (BR-73, `RunRecord.run_id`, `StateRef`) + BL-10 bajados a referencia. Erratum cerrado.
2. **Precondición de determinismo del `retrieve`** — ascendida a patrón P-2.
3. **Ubicación de `k/τ`** — resuelto: `eval_params=(k,τ)` **explícito** en la clave (Q1); `config_hash` queda solo para el RAG.

### 🔴 Abiertos → destino Code Generation
- **CG-1 · RetryPolicy solo sobre reads.** `RetryPolicy(max=3, backoff)` envuelve **solo operaciones de lectura** (`retrieve`, `generate`, `get_config`, `corpus_fingerprint`). Las **mutaciones** (`apply_data_patch`, `reindex`) **NO se reintentan a ciegas**: fallo → `revert` vía `PatchHandle` → `inconclusa` (BR-65). Reintentar una op no idempotente arriesga doble-aplicar el parche o dejar el índice inconsistente. (Ya reflejado como regla en `nfr-design-patterns.md §P-4`; verificar en implementación.)

### 🟡 Abierto → destino Code Generation (menor)
- **CG-2 · Cierre de inyección en frontera de agencia.** `import-linter` no basta; añadir test que verifica que los constructores de `gate/`/`orchestrator/` no aceptan `LlmPort`. (Ya especificado en §P-3; implementar el test.)
- **CG-3 · RAG de muestra stubbea `generate()` en U1.** El paciente de muestra devuelve un `generate()` **determinista sin red** (el camino NIIF no lo usa). Un `generate()` real usaría el **cliente LLM propio del RAG** (no el `LlmPort` de Ratchet — P5), y llega en **U3** con faithfulness/generación. Preserva la propiedad "e2e NIIF hermético".
- **CG-4 · Golden set sembrado desde fuente versionada.** El golden set (la verdad, NO recomputable) se siembra desde un archivo versionado en el repo / seed de migración, para ser reconstruible desde control de versiones. (Ver `infrastructure-design.md`, fila SPOF golden set.)

## Extension Configuration
| Extension | Enabled | Decided At |
|---|---|---|
| Security Baseline | No | Requirements Analysis |
| Property-Based Testing | Yes (Partial) | Requirements Analysis |
