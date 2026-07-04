---
id: TASK-001
title: Scaffold + import-linter (fail-closed, G2)
milestone: "M1: Núcleo determinista (libre-de-LLM)"
priority: 1
estimate: 2
blockedBy: []
blocks: [TASK-002]
parent: null
---

## Summary
Crear el esqueleto del proyecto (CG-0): estructura de paquetes, `pyproject.toml`, `docker-compose.yml` (app + Postgres) y el contrato **import-linter fail-closed** que protege el guardrail G2 desde el commit 1.

## Scope
- Crear: `pyproject.toml`, `src/ratchet/<módulo>/__init__.py` (los 11 módulos), `src/ratchet/adapter/llm.py` (placeholder), `docker-compose.yml`, `.github/workflows/ci.yml`, `.env.example`, `.gitignore`.
- **Reservado:** ninguna lógica de negocio todavía.

## Deliverables
- Layout `src/ratchet/{adapter,registry,evaluator,investigator,gate,monitor,reporter,orchestrator,api,persistence,domain}/`.
- `[tool.importlinter]` con contrato: `ratchet.gate` y `ratchet.orchestrator` NO pueden importar `ratchet.adapter.llm` ni `anthropic`.
- Deps fijadas (tech-stack): Python 3.12+, FastAPI, Typer, Pydantic v2, SQLAlchemy 2, Alembic, psycopg, NumPy, anthropic; dev: pytest, hypothesis, ruff, import-linter.
- CI stub: ruff + import-linter + pytest.

## Acceptance Criteria
- `uv sync` instala sin error.
- `lint-imports` corre y **pasa** (no hay violaciones aún).
- `ruff check` pasa.
- `docker-compose up` levanta `app` + `db` (Postgres 16).

## Test Plan
- `lint-imports` → exit 0.
- Test negativo (temporal): agregar un `import ratchet.adapter.llm` en `gate/` → `lint-imports` **falla** → revertir. Documenta que el contrato es fail-closed.

## Context
- `aidlc-docs/construction/u1-camino-niif/nfr-design/nfr-design-patterns.md` §P-3 (frontera de agencia)
- `.../infrastructure-design/infrastructure-design.md` (docker-compose, CI)
- `.../nfr-requirements/tech-stack-decisions.md`
- Carry-over CG-0.

## Definition of Ready
Specs de infraestructura y tech-stack aprobadas (✅). Sin dependencias.
