---
id: TASK-009
title: Monitor — detección de caída vs. baseline
milestone: "M2: Datos y loop"
priority: 2
estimate: 2
blockedBy: [TASK-003, TASK-006]
blocks: [TASK-011]
parent: null
---

## Summary
Implementar el monitor: evalúa contra la misma versión del golden set del baseline y dispara el loop si el recall cae ≥ δ (default 0.05).

## Scope
- `src/ratchet/monitor/`: `check(rag, baseline, δ) -> MonitorSignal`.
- **Reservado:** clasificación fina de origen (own-deploy vs env-drift) = U3.

## Deliverables
- `MonitorSignal(triggered, current, delta, threshold, source="unknown")`.

## Acceptance Criteria
- BR-41: dispara ⇔ `(baseline.recall − current.recall) ≥ δ`.
- BR-42: misma `golden_set_version` del baseline.
- BR-43: corrida `inconclusa` → no dispara.

## Test Plan
- Eval bajo umbral → `triggered=True`.
- Eval sobre umbral → `triggered=False`.
- Eval inconclusa → `triggered=False`.

## Context
- `functional-design/business-logic-model.md` BL-5 · `business-rules.md` BR-4x

## Definition of Ready
TASK-003, TASK-006 hechos (evaluator + baseline).
