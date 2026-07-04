# ADR-002: Recall = código determinista · Faithfulness = LLM-juez (nunca al revés)

*Fecha: 2026-07-04*

## Contexto
La decisión de Ratchet (¿este cambio mejora o empeora el RAG?) debe ser **confiable, reproducible y auditable**. Un LLM-juez como único árbitro es un punto único de falla: no es reproducible bit a bit y puede equivocarse en silencio. Pero existe una **verdad determinable**: si el span de fuente dorado fue recuperado. La confiabilidad de recuperación se puede *verificar por código*; la fidelidad semántica de la respuesta, no del todo.

## Decisión
**El razonamiento propone, la matemática dispone.** El `recall-por-span` se computa con **código determinista** y es la **métrica ancla** de toda decisión (gate, monitor, baseline). El `faithfulness` se computa con **LLM-juez** y es una **métrica secundaria** (señal para el diagnóstico), que **nunca decide el gate**. Nunca al revés: donde hay verificación determinista, no se decide con el juez.

## Alternativas consideradas
- **El juez decide todo (recall y faithfulness vía LLM)** — descartada: convierte al juez en SPOF de la decisión principal, no reproducible, no auditable.
- **Faithfulness por match de keywords determinista** — descartada: la fidelidad semántica genuinamente requiere juicio; forzarla a código daría falsos veredictos.

## Consecuencias
- ✅ La decisión principal es reproducible y el juez **no** es SPOF (mitigación de diseño).
- ✅ Recall comparable entre chunkings (se mide por span, no por chunk).
- ⚠️ Faithfulness se difiere a U3 (post walking-skeleton); U1 decide solo con recall.
- ⚠️ Exige un golden set etiquetado **por span de fuente**, con clase crítica marcada.

## Estado
Aceptado
