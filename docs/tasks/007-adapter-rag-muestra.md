---
id: TASK-007
title: Adapter — RagPatientPort + RAG de muestra (generate() stub) + RetryPolicy
milestone: "M2: Datos y loop"
priority: 2
estimate: 5
blockedBy: [TASK-000, TASK-002]
blocks: [TASK-008, TASK-011]
parent: null
---

## Summary
Implementar el puerto `RagPatientPort` y una impl. de **RAG de muestra in-process** (corpus NIIF/NIA, con NIIF 16 "vieja" como regresión sembrada), con `generate()` **stub** (CG-3), `corpus_fingerprint()`, y `RetryPolicy` **solo sobre lecturas** (CG-1).

## Scope
- `src/ratchet/adapter/`: `RagPatientPort` (retrieve/generate/get_config/apply_config/revert_config/supports_data_ops/apply_data_patch/reindex/revert_data_patch/corpus_fingerprint), impl. RAG de muestra, `RetryPolicy`, `LlmPort` (aislado).
- **Reservado (CG-1):** `RetryPolicy` NO envuelve `apply_data_patch`/`reindex`.

## Deliverables
- RAG de muestra con `retrieve()` **determinista** para índice fijo (precondición P-2).
- `generate()` stub determinista (sin red — CG-3).
- `corpus_fingerprint() -> list[(doc_id, doc_content)]` (contenido crudo; Ratchet hashea).
- `supports_data_ops()=True`; parche + reindex reversibles.

## Acceptance Criteria
- BR-63 (G1): capability-flag funciona.
- BR-64: `apply_data_patch` atómico; `apply→revert` = estado previo.
- CG-1: mutaciones no envueltas en retry; fallo → revert + inconclusa.
- CG-3: `generate()` stub, sin `ANTHROPIC_API_KEY`, determinista.
- BR-57: sondas/adapter sin LLM-judge.

## Test Plan
- `retrieve()` 2× sobre índice fijo → idéntico (determinismo).
- `apply_data_patch → revert` restaura doc + índice.
- Inyectar `ReindexError` → revert + señal inconclusa (verificado en orchestrator).
- Test: `RetryPolicy` NO envuelve mutaciones (inspección de firmas).

## Context
- `functional-design/domain-entities.md` (Document/Chunk externos) · `business-logic-model.md` BL-6, BL-8
- `nfr-design/nfr-design-patterns.md` §P-4 (retry), §P-1 (corpus_fingerprint) · Carry-overs CG-1, CG-3

## Definition of Ready
**TASK-000 (corpus NIIF de muestra, par vieja/nueva)**, TASK-002 hechos.
