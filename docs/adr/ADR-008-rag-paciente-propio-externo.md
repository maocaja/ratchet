# ADR-008: RAG paciente — propio externo (BM25, HTTP) ahora; AnythingLLM → U3; MCP → enterprise

*Fecha: 2026-07-05*

## Contexto
La estrella polar v2 (agéntica) exige un **paciente externo**: un RAG real que corra como su propio servicio, al que Ratchet se conecte por afuera (mata la crítica del "paciente amañado" por acoplamiento). Hoy el paciente es un **stub in-process** (`SampleRagPatient`, con `generate()` stubbeado). Hay que decidir la primera implementación del `RagPatientPort` externo. Opciones: **(A) RAG propio** como servicio aparte, o **(B) integrar un producto de terceros** (AnythingLLM). Transporte: **HTTP** vs **MCP** (estándar 2026). Restricción dura: Demo Day y la garantía estrella de **reproducibilidad bit-exacta** (P-1/P-2, StateKey, gate reproducible).

## Decisión
**RAG propio, como servicio externo (proceso aparte, HTTP, retrieval BM25 determinista).** AnythingLLM se difiere a **U3** como **2º paciente independiente** (la prueba anti-circularidad). **MCP** se difiere como dirección **enterprise/fast-follow** (AJIT), no MVP. La costura `RagPatientPort` (P5) mantiene todo swappable: es "qué implementación del puerto va primero", no una decisión irreversible.

## Alternativas consideradas
- **(B) AnythingLLM como paciente primario ahora** — descartada para el MVP:
  1. **Golden set ya curado para BM25** (las preguntas comparten vocabulario con el span, `seeds/README.md`); el retrieval por embeddings de AnythingLLM invalidaría parcialmente los 50 ítems → re-curación.
  2. **Retrieve determinista (P-2):** embeddings+ANN pueden no ser bit-reproducibles → romperían la garantía estrella (StateKey/gate reproducible). BM25 es determinista por construcción. **El criterio de más peso.**
  3. **G1 (parche de datos):** el corazón del demo NIIF es `apply_data_patch`+`reindex`; con RAG propio lo exponés exactamente como el gate lo necesita, sin depender de una API de terceros bajo presión de Demo Day.
  4. **"Externo" ≠ "de terceros":** un proceso aparte detrás del `RagPatientPort` ya mata la crítica de **acoplamiento**; la de **circularidad** (armaste el RAG y calibraste el bug) se responde de verdad con el **2º paciente independiente en U3**.
  5. **Regla #1 (simplicidad) + Demo Day:** un BM25 chico que controlás < pelear con el stack de AnythingLLM contra reloj.
- **MCP como transporte del MVP** — descartada: no está en el camino crítico para probar agencia; HTTP es universal y simple. MCP = relato enterprise, decidido cuando duela (ADR futuro).

## Consecuencias
- ✅ **No es un build desde cero:** se **externaliza** la lógica ya existente de `SampleRagPatient` (BM25, `apply_data_patch`, `reindex`, `revert`) envolviéndola en un servicio FastAPI (`/query`, `/ingest`, `/retrieve`, `/patch`, `/reindex`) + una UI de chat simple; el adaptador de Ratchet pasa de in-process a HTTP. ~80% ya está.
- ✅ **Cero re-curación** del golden set; la reproducibilidad estrella se mantiene.
- ✅ **Superficie de evidencia controlada:** al ser propio, exponemos las señales que el agente necesita para el escenario de contradictorios (fecha de publicación/vigencia, cláusula de derogación) en metadata/texto.
- ✅ **Generación real opcional:** el chatbot puede contestar con Claude (demo visceral del "responde mal") **sin tocar el determinismo de Ratchet** — el LLM vive en el paciente, la medición (BM25 + recall-por-span) sigue en código.
- ⚠️ Se pierde ahora la señal de portafolio "integré AnythingLLM, un producto real" → se recupera en **U3** con el 2º paciente.
- ⚠️ El transporte MCP y el 2º paciente quedan como **fast-follow** documentado (ADR enterprise futuro).

## Estado
Aceptado
