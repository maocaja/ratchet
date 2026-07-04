---
id: TASK-012
title: API + CLI (run/approve/report) + render de reporte HTML
milestone: "M3: Superficie y demo (CLI + reporte HTML)"
priority: 1
estimate: 4
blockedBy: [TASK-011]
blocks: [TASK-013]
parent: null
---

## Summary
Implementar la superficie del demo: FastAPI (endpoints) + CLI Typer que espeja los verbos, y el **render del reporte antes/después en HTML self-contained** (la pieza visual del Demo Day, sin frontend).

## Scope
- `src/ratchet/api/`: FastAPI (`POST /runs`, `GET /runs/{id}/report`, `POST /approvals/{id}`), CLI Typer (`ratchet run|report|approve`), render HTML del `Report`.
- **Reservado:** sin frontend app; el HTML es un artefacto autogenerado self-contained.

## Deliverables
- CLI: `ratchet run`, `ratchet approve <id>`, `ratchet report <id>`.
- Endpoint que devuelve el reporte (JSON) + variante HTML.
- Reporte HTML: recall before/after con CI, delta, diagnóstico, decisión, reproducible — legible sin recomputar.

## Acceptance Criteria
- NFR-U1-10 (Usabilidad): "disparar → aprobar → leer reporte" en ≤ 3 comandos.
- El reporte HTML es self-contained (abrible en navegador, sin assets externos).
- Superficie CLI = API (mismos verbos, C10).

## Test Plan
- `pytest tests/integration/test_api.py`: los 3 endpoints responden.
- CLI: los 3 comandos ejecutan el flujo.
- El HTML generado valida (self-contained, sin red).

## Context
- `functional-design/domain-entities.md` (Report) · `component-methods.md` C10
- `nfr-requirements/nfr-requirements.md` NFR-U1-10
- **Antes de escribir el chart antes/después: invocar la skill `dataviz`** — el reporte HTML es el artefacto de Demo Day; que se vea como un sistema (paleta, contraste, jerarquía).

## Definition of Ready
TASK-011 hecho (loop produce Report).
