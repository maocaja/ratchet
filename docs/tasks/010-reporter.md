---
id: TASK-010
title: Reporter — writeup + build_report + ApprovalService
milestone: "M2: Datos y loop"
priority: 2
estimate: 3
blockedBy: [TASK-002, TASK-004]
blocks: [TASK-011]
parent: null
---

## Summary
Implementar el reporter: ensamblar el reporte antes/después reproducible, y el `ApprovalService` que gestiona los **dos gates humanos** (US-13 confirmar parche, US-16 aprobar deploy).

## Scope
- `src/ratchet/reporter/`: `build_report(run) -> Report`, `map_decision(run)`, `ApprovalService` (`request_approval`, `record_approval`).
- **Reservado:** el render HTML va en la superficie (TASK-012); aquí se produce el `Report` (objeto).

## Deliverables
- `Report` con recall before/after (con CI), delta, decisión mapeada (`approve+humano → deploy`), reproducible_from.
- Dos `ApprovalRequest` con `kind` distinto; `pending` = waiting seguro.

## Acceptance Criteria
- BR-61: dos gates humanos distintos.
- BR-62: sin `approve` (US-13) ⇒ no se aplica; `DETENIDA_HUMANO`.
- BR-74: `Report` recomputable desde datos versionados.
- Mapeo veredicto→reporte correcto (approve pendiente → `pending`).

## Test Plan
- `build_report` recomputado coincide.
- Dos approvals (confirm-patch, approve-deploy) con estados independientes.
- reject en US-13 → estado `DETENIDA_HUMANO`.

## Context
- `functional-design/business-logic-model.md` BL-10, máquina de estados · `business-rules.md` BR-6x
- `nfr-design/nfr-design.md` ADR-U1-07

## Definition of Ready
TASK-002, TASK-004 hechos (tipos + gate).
