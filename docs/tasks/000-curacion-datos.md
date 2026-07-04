---
id: TASK-000
title: Curación de datos — golden set NIIF ≥50 + corpus de muestra (par NIIF 16 vieja/nueva)
milestone: "M0: Datos (curación humana)"
owner: "humano (Mauricio) — NO delegable a un agente de código"
priority: 1
estimate: 8
blockedBy: []
blocks: [TASK-006, TASK-007]
parent: null
---

## Summary
Producir los **dos insumos humanos** de U1, que un agente de código **no puede inventar** (BR-76: el golden set es la verdad). Es el deliverable no-código más difícil y está en la **ruta crítica** del Demo Day. Arranca **ya**, en paralelo con M1 (que no lo necesita — se testea con factories); debe estar **Done antes de la Wave 3/5**.

## Scope
- Curar el golden set NIIF y el corpus de muestra. **Reservado:** no es trabajo de agente; es curación experta humana. Los agentes de código consumen estos archivos como seed, no los generan.

## Deliverables
1. **Golden set NIIF** (`data/golden_set_niif.yaml` o similar): **≥50 ítems**, cada uno con `{question, answer, gold_span=(doc_id, start, end, text), critical}`, dimensionado por rebanada (≥50 por rebanada de la que se afirme algo). Incluye la **clase crítica** marcada y al menos un ítem que dependa de NIIF 16.
2. **Corpus NIIF/NIA de muestra** (`data/corpus/`): documentos fuente, con el **par NIIF 16 "vieja" (derogada) y "nueva" (vigente)** — la vieja es la regresión sembrada que hace `span_vigente_en_corpus=False` y dispara "fuente-vieja".

## Acceptance Criteria
- Golden set con **≥50** ítems válidos (offsets de carácter reales sobre el corpus, `len>0`), clase crítica marcada.
- El corpus contiene la versión **vieja** de NIIF 16 (estado inicial) y la **vigente** (el parche que Ratchet aplicará).
- Con el corpus en estado inicial, ≥1 ítem del golden set tiene su `gold_span` **ausente/diferente** → dispara el escenario NIIF.
- Ambos versionados en el repo (reconstruibles desde control de versiones — CG-4).

## Test Plan
- Validación de esquema: cada ítem tiene los campos requeridos; offsets dentro del rango del doc.
- Smoke: con el corpus inicial, el par NIIF 16 produce `span_vigente_en_corpus=False` para el ítem afectado (verificable una vez exista TASK-007).
- Conteo: ≥50 ítems; ≥1 crítico; ≥1 ligado a NIIF 16.

## Context
- `functional-design/business-rules.md` BR-24, BR-76 · `.claude/rules/evaluacion.md` (golden set por span, clase crítica, ≥50 por rebanada)
- `user-stories/stories.md` (escenario NIIF) · Carry-over CG-4
- **⚠️ Guía de curación (retriever léxico BM25 — decidido 2026-07-04):** las **preguntas deben compartir vocabulario con el texto del span dorado** (BM25 recupera por coincidencia de palabras). Preguntas con sinónimos ausentes en la fuente → recall artificialmente bajo. Ver `tech-stack-decisions.md`.

## Definition of Ready
Ninguna dependencia de código. Requiere criterio de dominio contable (NIIF/NIA). **Empezar de inmediato.**
