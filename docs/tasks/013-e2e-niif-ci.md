---
id: TASK-013
title: e2e NIIF (hermético) + CI completa
milestone: "M3: Superficie y demo (CLI + reporte HTML)"
priority: 1
estimate: 3
blockedBy: [TASK-012]
blocks: []
parent: null
---

## Summary
Cablear el escenario NIIF end-to-end (el `Scenario` de `stories.md`) y dejar la CI completa: ruff + import-linter + pytest (unit/PBT + integración/e2e), con el e2e **hermético** (sin `ANTHROPIC_API_KEY`, sin red).

## Scope
- `tests/e2e/test_camino_niif.py`: el escenario completo.
- `.github/workflows/ci.yml`: los 4 gates.
- **Reservado:** sin deploy automatizado en U1.

## Deliverables
- e2e NIIF: baseline → NIIF 16 vieja inyectada → monitor detecta → localiza fuente-vieja → parche → (aprobación) → gate recupera → reporte antes/después.
- CI que corre todo y **bloquea** si falla; e2e sin secretos de red.

## Acceptance Criteria
- El `Scenario` NIIF de `stories.md` corre end-to-end y termina en COMPLETADA con recall recuperado (ej. 0.70 → 0.88).
- El e2e corre **sin `ANTHROPIC_API_KEY`** (hermético — propiedad de diseño).
- CI verde: ruff + import-linter + pytest.
- Regresión inyectada atrapada por el gate (0 no detectadas dentro de cobertura).

## Test Plan
- e2e completo (camino feliz NIIF).
- e2e variante: parche que empeora → gate revierte → REVERTIDA.
- CI corre en GitHub Actions sin secretos de red para el e2e.

## Context
- `functional-design/business-logic-model.md` (Flujo 2, máquina de estados) · `user-stories/stories.md` (Épica-Journey NIIF)
- `infrastructure-design.md` §Determinismo + §CI mínima

## Definition of Ready
TASK-012 hecho (CLI/reporte). Todos los módulos integrados.
