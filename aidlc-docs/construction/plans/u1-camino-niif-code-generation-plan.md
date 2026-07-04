# Plan de Code Generation — U1 · Camino NIIF

> Fase: **CONSTRUCTION** · Unidad: **U1 · Camino NIIF** · Fecha: 2026-07-03
> Primera etapa que escribirá **código en `src/ratchet/`**. Insumos: los 4 artefactos de diseño de U1 (functional / nfr-requirements / nfr-design / infrastructure).
> **Estado de ejecución: NADA implementado todavía.** Este documento SOLO fija el método y el orden. Por decisión del usuario, **no se ha escrito ni una línea de código** (ni scaffold, ni `pyproject.toml`). Las dos decisiones de abajo quedan **registradas**, no ejecutadas. La implementación arranca en una sesión posterior con aprobación explícita.

## Metodología (fijada) — test-alongside por módulo con subagentes propios
Cada módulo se considera **cerrado** solo cuando pasa este bucle, no antes:
```
generar módulo  →  test-writer lo cubre (happy/error/edge, PBT en núcleo,
                                          recall RECOMPUTADO, factories, regresión inyectada)
                →  code-reviewer lo aprueba (guardrails G1/G2/G3, recall=código,
                                             faithfulness=juez, anti-agentwashing)
                →  import-linter + pytest verdes en CI  →  módulo CERRADO
```
- Los guardrails se **enforcan mientras se escribe**, no después.
- `test-writer` y `code-reviewer` son los subagentes ya definidos en el repo.

## Orden de construcción (núcleo determinista / libre-de-LLM primero)
> Coherente con la propiedad "camino NIIF hermético": lo determinista se construye y testea antes que las costuras de red.
1. **CG-0 · Scaffold + import-linter (fail-closed)** — pyproject, paquetes, contrato G2, CI. *(especificado abajo; NO ejecutado)*
2. `domain/` — tipos: `Span`, `GoldenItem`, `GoldenSet`, `Chunk`, `EvalResult`, `Baseline`, `Diagnosis`, `Writeup`, `Patch`/`PatchHandle`, `GateVerdict`, `StateKey`/`StateRef`, `RunRecord`, `Report`.
3. `evaluator/` — recall-por-span (BL-1), `StateHasher` (P-1), `BootstrapEstimator(seed)` (P-2). **Núcleo determinista.**
4. `gate/` — no-regresión + revert + guardrail crítico (BL-4). **Determinista, sin LLM.**
5. `registry/` — `GoldenSetRegistry` (baseline ≥50), seed del golden set desde repo (**CG-4**).
6. `persistence/` — `RunRepository` + fake in-memory, `UNIQUE(StateKey)` (P-1).
7. `adapter/` — `RagPatientPort` + RAG de muestra in-process (`generate()` **stub** — **CG-3**), `corpus_fingerprint`, `RetryPolicy` **solo reads** (**CG-1**), `LlmPort`.
8. `investigator/` — `ProbeToolkit` determinista, `Localizer` (LLM delgado), `verify_claim`.
9. `monitor/` — detección de caída (BL-5).
10. `reporter/` — `build_report` + `ApprovalService` (dos gates P2).
11. `orchestrator/` — `LoopOrchestrator` (G2, sin LLM); test de no-inyección de `LlmPort` (**CG-2**).
12. `api/` — FastAPI + CLI Typer (C10).
13. **e2e NIIF** — cableado end-to-end + Build & Test.

## Carry-overs → dónde aterrizan
| Carry-over | Módulo(s) | Verificación |
|---|---|---|
| **CG-1** RetryPolicy solo reads | `adapter/` | test: mutaciones no envueltas en retry |
| **CG-2** no-inyección `LlmPort` | `gate/`, `orchestrator/` | import-linter (CG-0) + test de firmas de constructor |
| **CG-3** RAG stubbea `generate()` | `adapter/` | e2e NIIF hermético (sin red) |
| **CG-4** golden set sembrado desde repo | `registry/`, seed | reconstruible desde control de versiones |

## CG-0 — contenido a ejecutar (especificado, PENDIENTE)
> El primer paso de la implementación, cuando se apruebe. Se lista aquí para que exista **desde el scaffold**, no al final.
- `pyproject.toml` — Python 3.12+, deps fijadas (tech-stack-decisions), `ruff`, `pytest`, `hypothesis`, `import-linter`.
- `src/ratchet/<módulo>/__init__.py` — los 11 paquetes del layout (unit-of-work.md), vacíos.
- `src/ratchet/adapter/llm.py` — placeholder del cliente LLM (blanco prohibido del contrato).
- **`[tool.importlinter]` contrato G2 fail-closed:** `ratchet.gate` y `ratchet.orchestrator` **no pueden** importar `ratchet.adapter.llm` ni `anthropic`. Presente desde el commit 1 ⇒ G2 imposible de violar por accidente.
- `.github/workflows/ci.yml` — ruff + import-linter + pytest (stub).

## Parada (estado actual)
> **NADA implementado.** Este plan solo fija método y orden. La ejecución de CG-0 (y todo lo demás) requiere aprobación explícita en una sesión posterior.
