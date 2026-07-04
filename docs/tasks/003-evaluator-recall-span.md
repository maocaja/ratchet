---
id: TASK-003
title: Evaluator — recall-por-span + StateHasher + BootstrapEstimator
milestone: "M1: Núcleo determinista (libre-de-LLM)"
priority: 1
estimate: 5
blockedBy: [TASK-002]
blocks: [TASK-004, TASK-005, TASK-006, TASK-009]
parent: null
---

## Summary
Implementar el corazón determinista: `recall-por-span` (cobertura por intersección de offsets, τ=0.8), el `BootstrapEstimator(seed)` para el CI, y el `StateHasher` que compone la clave de estado.

## Scope
- `src/ratchet/evaluator/`: `evaluate(rag, gs, k, τ)`, `recall_por_span`, `cubre(chunk, span)`, `BootstrapEstimator(seed)`, `StateHasher` (`corpus_hash` vía `corpus_fingerprint`, `config_hash`, `patch_hash`, `eval_params`).
- `normalize()` compartido (mismo para recall y corpus_hash).
- **Reservado:** no llamar al LLM (evaluator es determinista).

## Deliverables
- `recall_span` recomputable, comparable entre chunkings.
- CI bootstrap con **seed fijo** (`numpy.default_rng(seed)`, B=1000).
- `StateKey` según `nfr-design-patterns.md §P-1` (dueño único; no re-deletrear la tupla en otros lados).

## Acceptance Criteria
- BR-11..BR-14: recall recomputado; `hit ⇔ max cobertura ≥ τ`; overlap solo mismo doc; intersección de intervalos.
- BR-36: mismo `(inputs, seed)` → mismo CI **bit a bit**.
- `corpus_hash` estable e independiente del orden (canonical json de fingerprint ordenado).
- Corrida con fallo de `retrieve` → `EvalResult(status="inconclusa")` (BR-16).

## Test Plan
- PBT: `recall_span ∈ [0,1]`; monotonía de cobertura.
- Test determinista: golden set fijo → recall exacto recomputado (no hardcode).
- Test: mismo input+seed dos veces → CI idéntico.
- Regresión inyectada: cambio de τ cambia el resultado (eval_params en la clave).

## Context
- `functional-design/business-logic-model.md` BL-1, BL-2 · `business-rules.md` BR-1x, BR-36
- `nfr-design/nfr-design-patterns.md` §P-1 (clave de estado), §P-2 (reproducibilidad)

## Definition of Ready
TASK-002 hecho (tipos existen). BL-1/BL-2 y §P-1 aprobados (✅).
