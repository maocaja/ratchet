---
name: review-specs
description: Revisa la coherencia de los specs de Ratchet (docs/ y specs/, luego aidlc-docs/) contra los principios y el MVP scope, y reporta contradicciones/sobre-afirmaciones/TBDs. Skill propio del dominio (Estación 3).
---

# review-specs

Skill de dominio para mantener los specs de Ratchet coherentes durante todo el pipeline AI-DLC.

## Cuándo usarlo
Antes de cerrar cualquier artefacto (segmento del PRD, arquitectura, o fase AI-DLC), o cuando se hayan editado varios `.md`.

## Qué hace
1. Lee `docs/definicion.md`, `specs/prd.md`, `specs/arquitectura.md`, `docs/pvb.md` (y `aidlc-docs/` si existe).
2. Verifica contra los **principios** (P1-P5) y el **MVP Scope** (PRD Seg. 8).
3. Reporta, ordenado por severidad:
   - Contradicciones entre documentos.
   - Sobre-afirmaciones vs. lo que el MVP realmente hará.
   - Rupturas de la tesis ("nunca empeorar").
   - TBDs críticos sin resolver.
4. NO edita — solo reporta. Para arreglar, el humano decide.

## Referencia rápida (la tesis)
Ratchet = medir → diagnosticar → experimentar → decidir/revertir. **El trinquete: mejora o revierte, nunca empeora.** North Star = puntos de recall ganados + guardrail 0 regresiones.
