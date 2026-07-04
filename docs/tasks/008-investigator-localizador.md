---
id: TASK-008
title: Investigator — ProbeToolkit + Localizer + verify_claim (read-only, G3)
milestone: "M2: Datos y loop"
priority: 2
estimate: 4
blockedBy: [TASK-002, TASK-007]
blocks: [TASK-011]
parent: null
---

## Summary
Implementar el investigador read-only: `ProbeToolkit` (sondas deterministas del lineage), `Localizer` (reglas deterministas de capa; LLM solo desambigua) y `verify_claim` (recomprobación determinista). En el camino NIIF localiza "fuente-vieja" **sin invocar el LLM**.

## Scope
- `src/ratchet/investigator/`: `ProbeToolkit` (span_indexado, span_en_topk, fronteras_de_chunk, span_vigente_en_corpus, respuesta_usa_span), `localize_rules`, `Localizer`, `verify_claim`, `write_incident`.
- **Reservado (G3):** el investigador NO aplica cambios; solo emite `Diagnosis` + `Writeup`.

## Deliverables
- `localize_rules` con orden de prioridad; NIIF ⇒ `span_vigente_en_corpus=False` ⇒ "fuente-vieja"/datos, **sin LLM**.
- `verify_claim` recomprueba la evidencia citada.
- `write_incident` produce writeup read-only con conclusión "→ datos".

## Acceptance Criteria
- BR-51: investigador no llama `apply_*`.
- BR-52: capa determinista donde las sondas son concluyentes; LLM no inventa capa fuera del enum.
- BR-54: `verified=False` ⇒ no habilita acción.
- BR-55: "fuente-vieja" ⇔ `span_vigente_en_corpus=False`.
- BR-57: `respuesta_usa_span` = containment textual, no faithfulness.

## Test Plan
- Escenario NIIF: probes → `Diagnosis(capa=fuente-vieja, verified=True)` **sin red**.
- PBT sobre `localize_rules` (cada combinación de sondas → capa esperada).
- Claim falso → `verify_claim` lo rechaza.

## Context
- `functional-design/business-logic-model.md` BL-6, BL-7 · `business-rules.md` BR-5x
- `nfr-design/nfr-design-patterns.md` §P-3 (frontera de agencia)

## Definition of Ready
TASK-002, TASK-007 hechos (tipos + adapter con sondas).
