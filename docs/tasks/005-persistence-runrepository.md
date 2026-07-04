---
id: TASK-005
title: Persistence — RunRepository + fake + UNIQUE(StateKey)
milestone: "M2: Datos y loop"
priority: 2
estimate: 4
blockedBy: [TASK-002, TASK-003]
blocks: [TASK-006, TASK-011]
parent: null
---

## Summary
Implementar la capa de persistencia tras un puerto/repositorio: `RunRepository` sobre Postgres (SQLAlchemy + Alembic) con `UNIQUE(StateKey)`, y un fake in-memory para tests rápidos.

## Scope
- `src/ratchet/persistence/`: puerto `RunRepository`, impl. Postgres, impl. fake in-memory, migraciones Alembic.
- **Reservado:** el core no importa SQLAlchemy directamente (solo por el puerto).

## Deliverables
- Esquema: golden sets, baselines, runs (RunRecord), writeups, approvals, decisiones.
- Constraint `UNIQUE(StateKey)` + upsert idempotente.
- Fake in-memory con paridad de unicidad.

## Acceptance Criteria
- BR-73: `record_run` idempotente por la clave de estado; doble record → 1 run; distinto `k`/`τ` o corpus → 2 runs.
- BR-21: golden set/baseline inmutables por versión.
- Migración aplica limpia desde cero (`alembic upgrade head`).

## Test Plan
- `pytest tests/unit` contra fake: idempotencia (doble record → 1).
- `pytest tests/integration` contra Postgres de servicio: `UNIQUE(StateKey)` rechaza duplicado.

## Context
- `nfr-design/nfr-design-patterns.md` §P-1 (clave, UNIQUE) · `functional-design/business-rules.md` BR-73, BR-21
- `infrastructure-design.md` (Postgres, Alembic)

## Definition of Ready
TASK-002, TASK-003 hechos (tipos + StateKey definidos).
