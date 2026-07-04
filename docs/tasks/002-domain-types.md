---
id: TASK-002
title: Tipos de dominio (domain/)
milestone: "M1: Núcleo determinista (libre-de-LLM)"
priority: 1
estimate: 3
blockedBy: [TASK-001]
blocks: [TASK-003, TASK-005, TASK-007, TASK-010]
parent: null
---

## Summary
Implementar los tipos de dominio (Entities, Value Objects, Aggregates) de U1 como modelos Pydantic v2, tecnología-agnósticos y sin lógica de negocio compleja.

## Scope
- Crear en `src/ratchet/domain/`: `Span`, `GoldenItem`, `GoldenSet`, `Chunk`, `EvalResult` (con `per_item: list[(item_id, hit, critical)]`), `Baseline`, `MonitorSignal`, `ProbeResults`, `Diagnosis`, `Writeup`, `Patch`/`PatchHandle`, `GateVerdict`, `ApprovalRequest`, `RunRecord`, `Report`, `StateRef`.
- **Reservado:** el cómputo de hashes de la clave de estado (va en evaluator/StateHasher, TASK-003).

## Deliverables
- Tipos con validaciones básicas (ej. `Span.len > 0`, `Diagnosis.capa` en enum, `GateVerdict.decision ∈ {approve,revert}`).
- `EvalResult.per_item` lleva `critical` por ítem (necesario para el guardrail 🔒).

## Acceptance Criteria
- Cada entidad/VO del `domain-entities.md` existe con sus campos.
- `Span` rechaza `start ≥ end`.
- `Diagnosis.capa` fuera del enum → error de validación.
- Tipos inmutables donde corresponde (VOs).

## Test Plan
- `pytest tests/unit/test_domain.py`: validaciones de cada tipo (happy + inválido).
- PBT: `Span` con offsets aleatorios mantiene invariante `len > 0`.

## Context
- `aidlc-docs/construction/u1-camino-niif/functional-design/domain-entities.md` (fuente principal)
- `.claude/rules/python.md` (type hints, estructura)

## Definition of Ready
TASK-001 hecho (scaffold existe). domain-entities.md aprobado (✅).
