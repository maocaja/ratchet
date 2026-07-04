# Milestones — U1 · Camino NIIF

Planning wave: `u1-camino-niif-implementation`. Orden **walking-skeleton-first**: núcleo determinista primero (libre-de-LLM, máxima testabilidad), luego datos+loop, luego superficie+demo.

## M0: Datos (curación humana) — RUTA CRÍTICA
El único trabajo **no-código** y **no delegable a un agente**. Arranca **ya**, en paralelo con M1 (que no lo necesita — usa factories); debe estar Done antes de que el código lo consuma (TASK-006/007).
- **TASK-000** Curación de datos: golden set NIIF ≥50 (span-etiquetado, clase crítica) + corpus de muestra (par NIIF 16 vieja/nueva). **Owner: humano (Mauricio).** El riesgo #1 de la fecha si no arranca ya.

## M1: Núcleo determinista (libre-de-LLM)
La base testeable sin red. Al cerrar M1, el recall-por-span y el gate de no-regresión funcionan y están cubiertos por PBT.
- TASK-001 Scaffold + import-linter (fail-closed, G2 desde el commit 1)
- TASK-002 Tipos de dominio (`domain/`)
- TASK-003 Evaluator: recall-por-span + StateHasher + BootstrapEstimator
- TASK-004 Gate: no-regresión + revert + guardrail crítico

## M2: Datos y loop
El ciclo completo de la rama de datos. Al cerrar M2, la corrida NIIF corre end-to-end en memoria/tests (detecta → localiza → parcha → gate).
- TASK-005 Persistence: `RunRepository` + fake in-memory + `UNIQUE(StateKey)`
- TASK-006 Registry: golden set (≥50, seed desde repo — CG-4) + baseline
- TASK-007 Adapter: `RagPatientPort` + RAG de muestra in-process (`generate()` stub — CG-3) + `corpus_fingerprint` + `RetryPolicy` solo reads (CG-1)
- TASK-008 Investigator: `ProbeToolkit` + `Localizer` + `verify_claim` (read-only, G3)
- TASK-009 Monitor: detección de caída vs. baseline
- TASK-010 Reporter: writeup + `build_report` + `ApprovalService` (dos gates P2)
- TASK-011 Orchestrator: `LoopOrchestrator` (G2) + test de no-inyección de `LlmPort` (CG-2)

## M3: Superficie y demo (CLI + reporte HTML)
Lo que se ve en Demo Day. Al cerrar M3, `ratchet run/approve/report` funciona y emite el reporte HTML antes/después.
- TASK-012 API + CLI (`run`/`approve`/`report`) + render del reporte **HTML**
- TASK-013 e2e NIIF (hermético) + CI (ruff + import-linter + pytest)

## Criterio de "hecho" de U1
El `Scenario` NIIF de `stories.md` corre end-to-end; el gate revierte si empeora; el reporte antes/después es reproducible. Todo el camino NIIF es **libre-de-LLM y hermético**.
