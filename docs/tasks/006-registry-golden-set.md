---
id: TASK-006
title: Registry — golden set (≥50, seed desde repo) + baseline
milestone: "M2: Datos y loop"
priority: 2
estimate: 4
blockedBy: [TASK-000, TASK-003, TASK-005]
blocks: [TASK-009, TASK-011]
parent: null
---

## Summary
Implementar `GoldenSetRegistry`: curar/versionar el golden set (≥50, span-etiquetado), fijar baseline (rechaza <50), y **sembrar el golden set NIIF desde una fuente versionada en el repo** (CG-4).

## Scope
- `src/ratchet/registry/`: `save_golden_set`, `get_golden_set`, `set_baseline`, `get_baseline`.
- Seed: `seeds/golden_set_niif.yaml` (o similar) versionado en el repo, con ≥50 ítems span-etiquetados, incluyendo la clase crítica y el caso NIIF 16.
- **Reservado:** el golden set es la verdad humana; no se recomputa (CG-4).

## Deliverables
- Golden set NIIF sembrable desde el repo (reconstruible desde control de versiones).
- Baseline versionado que rechaza <50 o eval inconclusa.

## Acceptance Criteria
- BR-22: `set_baseline` con <50 → reject.
- BR-24: cada `GoldenItem` con `gold_span` válido + `critical`.
- BR-25: no baseline desde inconclusa.
- BR-76 / CG-4: golden set sembrado desde archivo versionado, no recomputado.

## Test Plan
- Factory con 49 ítems → `set_baseline` reject.
- Seed carga ≥50 ítems válidos desde el archivo.
- Golden set inmutable por versión (mutación → error).

## Context
- `functional-design/business-logic-model.md` BL-3 · `business-rules.md` BR-2x, BR-76
- `infrastructure-design.md` (SPOF golden set — seed) · Carry-over CG-4

## Definition of Ready
**TASK-000 (golden set curado ≥50)**, TASK-003, TASK-005 hechos.
