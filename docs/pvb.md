# Product Vision Board (PVB) — Ratchet

> Formato del curso Hardcore AI (Estación 1). **E1 COMPLETA (2026-07-02).** Insumos: `definicion.md`, `specs/prd.md`.

## PRODUCTO
- **Nombre:** Ratchet
- **Una línea:** El **SRE de guardia del conocimiento de un RAG** — cuando la confiabilidad cae, **localiza el defecto (datos o config)** y lo arregla en la capa correcta (config con gate, datos con confirmación humana), **sin dejarlo nunca peor**.

## 1. PROBLEMA
Los RAG en producción **se degradan en silencio** (cambian documentos/modelos); se prueban **una vez y a mano**; los equipos **miden pero no auto-mejoran** → IA no confiable, gasto sin retorno.
- ¿Sobrevive a GPT-5/Claude-5? **[x] Sí — problema de WORKFLOW/INTEGRACIÓN** (loop + estado + integraciones), no de output.
- **Durability Score: 4/5.**

## 2. SEGMENTO TARGET
Equipos de IA/plataforma con un RAG en producción sobre **corpus cambiante y de alto riesgo** (auditoría/contabilidad, banca, fintech, legal). *(Audiencia real del portafolio: empresas que contratan Senior AI Eng.)*
- **Veto de confianza:** Head of AI / CTO que responde por la confiabilidad — mata la adopción si no confía en el revert-safety.

## 3. MOAT PRIMARIO
**[x] Trust Moat** — reliability/safety: **gate de no-regresión** (nunca despliega algo peor) + **re-experimentación** ante deriva del entorno + evidencia medible auditable, anclada en métricas deterministas. *(Nota portafolio: el foso importa menos; el valor es demostrar la skill.)*

## 4. ARENA COMPETITIVA
**[x] Disruptor (AI-Disrupted)** — reimagina el mantenimiento del RAG: de "prueba manual de una vez" a **"mejora continua automática"**.
- **vs. gigantes:** no compites con quien construye agentes (MS/OpenAI); eres la **capa neutral de mejora** sobre cualquier RAG. Los tools (LangSmith) miden; tú **cierras el loop**.

## 5. UX PARADIGM
**[x] Agent** — ejecuta autónomo (evalúa, experimenta, decide) **dentro de límites**, con humano aprobando el avance a producción (P2). Agente con gate humano.

## 6. AI DECISION TRIANGLE
**[x] Capability** — lo más preciso; un falso negativo (regresión no detectada) = incidente → la corrección manda.
- **Trade-offs:** acepto **más costo/latencia** (correr N variantes + juez) por decisiones correctas y seguras; el loop es de fondo → sacrifico **Speed**.

## 7. MODELO ECONÓMICO
*Portafolio → sin pricing real.* Si se comercializara: **[x] Hybrid Tiered** (tiers por nº de RAGs/evaluaciones) o Usage-Based.
- ¿Escala 10x? **[x] Necesita ajuste** (el costo de experimentos escala → topar variantes).
- Costo/Revenue/Margin: **N/A (portafolio) / TBD.**

## 8. MÉTRICAS DE ÉXITO
- **Usuario:** (1) puntos de recall que el loop gana solo; (2) tiempo de setup <30 min / primer ciclo <1 día.
- **AI:** (1) **0 regresiones no detectadas** *(dentro de la cobertura del golden set / clase crítica)* (guardrail); (2) acuerdo LLM-judge vs humano (accuracy/kappa).

## 9. RIESGOS CRÍTICOS
1. **¿Commoditización en 12 meses?** La *medición* se commoditiza (ya hay tools); el *loop con revert-safety continuo* no. Para portafolio, demuestra skill igual.
2. **¿Competidor replica en <6 semanas?** La capa de eval sí; lo difícil es el loop seguro decidir→desplegar→revertir + la disciplina de datos (golden set/baseline). Para portafolio, no importa.
3. **¿Cómo se rompe la confianza a escala?** Una **regresión no detectada** que llega a prod → por eso el guardrail "0 regresiones" + anclar en métricas deterministas.

---
> **Nota:** secciones pensadas para "producto/startup" (modelo económico, algunos riesgos) llenadas con **N/A/portafolio** donde no aplican del todo (regla del curso: no inventar).
