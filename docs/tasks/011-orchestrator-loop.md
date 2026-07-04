---
id: TASK-011
title: Orchestrator — LoopOrchestrator (G2) + test no-inyección LlmPort
milestone: "M2: Datos y loop"
priority: 1
estimate: 4
blockedBy: [TASK-004, TASK-005, TASK-006, TASK-007, TASK-008, TASK-009, TASK-010]
blocks: [TASK-012]
parent: null
---

## Summary
Implementar el `LoopOrchestrator`: la secuencia determinista medir→localizar→(rama datos)→gate→reportar. **No contiene `LLM.call()`** (G2); rutea solo sobre datos deterministas. Punto de convergencia del loop.

## Scope
- `src/ratchet/orchestrator/`: `run_loop(rag, gs) -> Report`, máquina de estados del `RunRecord`, flujo de parche (apply/reindex/revert).
- **Reservado (G2/CG-2):** `orchestrator/` no importa ni recibe `LlmPort`.

## Deliverables
- Ciclo NIIF end-to-end: eval → monitor → probe → localize(verified) → writeup → propose_patch → (US-13) → apply+reindex → eval → gate → revert_if_worse → (US-16) → report.
- Transiciones de estado (terminales: SIN_CAMBIO, COMPLETADA, REVERTIDA, RECHAZADA, DETENIDA_HUMANO, INCONCLUSA).

## Acceptance Criteria
- BR-71 (G2): orchestrator no importa LLM (import-linter verde).
- CG-2: test que verifica que el constructor de `orchestrator/` (y `gate/`) **no acepta `LlmPort`**.
- BR-72: rutea sobre `Diagnosis.fix_layer` ya verificado.
- BR-75: en todo terminal salvo COMPLETADA/PROMOVIDA, baseline intacto.
- BR-65: reindex falla → revert + inconclusa.

## Test Plan
- e2e (en memoria/fake): escenario NIIF corre a COMPLETADA con recall recuperado.
- Inyectar regresión en el parche → gate revierte → REVERTIDA, baseline intacto.
- Inyectar `ReindexError` → INCONCLUSA + revert.
- Test CG-2: firma de constructor sin `LlmPort`.

## Context
- `functional-design/business-logic-model.md` BL-9 + máquina de estados · `business-rules.md` BR-7x
- `nfr-design/nfr-design-patterns.md` §P-3 · Carry-over CG-2

## Definition of Ready
TASK-004..010 hechos (todo el ciclo disponible).
