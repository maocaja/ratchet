---
id: TASK-004
title: Gate — no-regresión + revert + guardrail crítico
milestone: "M1: Núcleo determinista (libre-de-LLM)"
priority: 1
estimate: 4
blockedBy: [TASK-003]
blocks: [TASK-010, TASK-011]
parent: null
---

## Summary
Implementar el gate de no-regresión **determinista, sin LLM** (G2): aprueba solo si el CI del delta pareado ≥ 0; regresión en clase crítica ⇒ revert forzado; revert automático si empeora.

## Scope
- `src/ratchet/gate/`: `evaluate_change(candidate, baseline) -> GateVerdict`, `revert_if_worse(handle, verdict)`.
- **Reservado:** `gate/` NO importa el cliente LLM (import-linter lo enforca).

## Deliverables
- Delta pareado por `item_id`; CI bootstrap pareado; `reg_crit` computado desde `per_item` (sin necesitar el `GoldenSet`).

## Acceptance Criteria
- BR-31: `gate/` no importa LLM (import-linter verde).
- **CG-2 (runtime):** el **constructor/firma de `gate/` NO acepta `LlmPort`** — test explícito (import-linter no atrapa la inyección por constructor; ver §P-3). Complementa el contrato estático de TASK-001.
- BR-32: aprueba ⇔ `ci_delta.lower ≥ 0`.
- BR-34 (🔒): regresión en clase crítica (`base_hit=1 ∧ cand_hit=0`, `critical=True`) ⇒ `revert` sin importar el delta agregado.
- BR-35: revert automático, sin aprobación humana.

## Test Plan
- Regresión inyectada (a): parche que baja recall agregado → `revert`.
- Regresión inyectada (b): rompe un ítem crítico **sin** bajar el agregado → `revert` (🔒).
- Caso mejora: recall sube con CI que excluye 0 → `approve`.
- PBT: propiedades del veredicto (approve ⇒ ci.lower≥0 ∧ reg_crit=0).

## Context
- `functional-design/business-logic-model.md` BL-4 · `business-rules.md` BR-3x
- `nfr-design/nfr-design.md` ADR-U1-02

## Definition of Ready
TASK-003 hecho (EvalResult.per_item con critical disponible). BL-4 aprobado (✅).
