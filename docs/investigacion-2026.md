# Investigación — diferenciación, RAG y conexión (julio 2026)

> Fecha: **2026-07-05**. Tres investigaciones con fuentes web actuales, para no decidir el pivote de memoria. Alimentó la estrella polar v2 (`definicion.md`) y **ADR-008**.
> Nota de calidad de fuentes: mucho material 2025-2026 es blog vendor/SEO; los anclajes duros son specs (MCP, OTel/OpenInference), docs de cloud (AWS/OpenAI/Google/Azure/Anthropic), releases de repos, Gartner y rondas de inversión en prensa. Los números MTEB/benchmarks son direccionales.

---

## Parte 1 — Diferenciación competitiva

**Veredicto:** la idea vive, pero el margen se estrechó y hay que **liderar el pitch con el gate determinista + significancia, no con "localizar" ni "self-heal".**

**Comoditizado (NO liderar con esto):** "medir RAG con faithfulness + LLM-juez" (Ragas, DeepEval, Galileo, Bedrock); "localizar la capa" a nivel retrieval-vs-generación (RAGEC, Doctor-RAG, Galileo chunk-attribution); "self-healing RAG" (buzzword); "gate de CI que bloquea regresión" (DeepEval, Braintrust).

**Vacante (el moat, en orden de fuerza):**
1. **Gate determinista + significancia estadística** — nadie exige bootstrap CI/McNemar antes de declarar mejora, ni revert-automático, ni protege falsos negativos en clase crítica. **El más defendible.**
2. **Regla de oro** (recall = código, faithfulness = juez) — más estricta que el mercado, que usa juez para ambos.
3. **Asimetría datos/config** (config auto, datos con humano) — nadie la tiene.
4. **Trigger por cambio de corpus** + localizador read-only sobre el lineage, apuntado a RAG de **conocimiento** (no infra).

**Prior art a diferenciar (honestidad):** **Doctor-RAG** (arXiv:2604.00865, jun 2026) diagnostica + repara RAG, pero **autónomo, sin gate determinista, sin split datos/config, sin humano** → diferenciarse por gate+significancia+asimetría. **RAGEC** (arXiv:2510.13975) atribuye la etapa pero no arregla. La categoría "AI-SRE" (Cleric, Traversal, Causely…) apunta a **infraestructura, no a conocimiento de RAG** (bobbytables.io, ago 2025). Plataformas cercanas: **Braintrust** ($80M Series B, feb 2026) gatea código/prompt, no datos; **Patronus Percival** sugiere+humano-confirma, sin gate; **Galileo** surfacea, no arregla corpus/config. Gartner formalizó **"Guardian Agents"** (jun 2025) — Ratchet encaja, con giro contrarian (determinista donde el mainstream es IA-juzga-IA).

**El whitespace clave:** casi toda la literatura de observabilidad de RAG **asume que sos dueño del pipeline**. Vigilar+localizar un RAG que **NO controlás** es whitespace defendible (experimental). Confirmación de campo: consenso 2026 de que *"el fallo casi siempre vive en retrieval/indexación, no en generación"* (Microsoft Azure, mar 2026) → valida el localizador.

---

## Parte 2 — Arquitectura RAG + conexión externa

**Stack de un RAG serio 2026** (el "naïf" PDF→vector→coseno está muerto): retrieval **híbrido** (denso + BM25 → RRF) + **reranking** cross-encoder (bge-reranker-v2-m3 / Cohere Rerank); **Contextual Retrieval** de Anthropic (−49% fallos, sep 2024); embeddings open ya alcanzaron a las APIs (bge-m3, Qwen3-Embedding, Voyage); **agentic RAG** = el cambio del año; **pgvector 0.8 HNSW** para demo local (cero infra extra).

**Conexión externa — MCP es el estándar 2026:** protocolo abierto (Anthropic, nov-2024), donado a la **Agentic AI Foundation** (Linux Foundation, dic-2025), ~97M descargas/mes; RAG-sobre-MCP establecido (retrieve = Tool, docs = Resources; transporte Streamable HTTP/stdio). **Límite crítico:** MCP estandariza el **transporte, NO el schema de respuesta** de retrieval → el shape `{chunk, score, source_location}` sigue siendo del adaptador. Observabilidad: **OpenInference** (Arize, define span RETRIEVER) + OTel GenAI (experimental); Langfuse/Phoenix consumen OTLP.

**Contrato mínimo del adaptador (modelo: par de dos llamadas de AWS Bedrock):** `retrieve → [{text, score, source_location}]` (determinista → recall por span) + `generate → {answer, citations[span]}` (juez → faithfulness) + introspección de corpus/config (para localizar capa). **Re-index = disparado por humano** (no es API estándar → encaja con "datos requieren humano").

**Validaciones para Ratchet:** el "context recall" de Ragas es **LLM-juzgado** → NO reusar; recall determinista por span. Un endpoint **answer-only bloquea el recall por span** → el contrato **debe** exigir los chunks recuperados.

---

## Parte 3 — Evaluar un RAG de terceros + candidatos a 2º paciente

**Escalera de acceso** (lo que podés medir salta en cada peldaño): (a) solo `generate` → métricas de respuesta; **(b) `retrieve` con chunks → el mínimo real** (recall por span, faithfulness, localización); (c) corpus → recall contra el corpus; (d) config → atribuir capa. **IMPOSIBLE en un RAG ajeno:** re-index, revert, cambiar config, patchear docs → tus palancas desde afuera son **medir + localizar + recomendar; el dueño ejecuta.** → Valida exactamente el modelo **read-only** de Ratchet (G3).

**Contrato de facto entre herramientas:** la "cuádrupla RAGAS" `{user_input, retrieved_contexts, response, reference}`; el trace estándar es **OpenInference RETRIEVER**. LangSmith/Braintrust llaman a un target callable; Ragas/OpenAI Evals puntúan un dataset.

**Candidatos a 2º paciente (U3):** **AnythingLLM v1.15** (el mejor: endpoint `vector-search` retrieval-only + `update-embeddings` + LanceDB `restore()` para revert real; MIT, local); **RAGFlow** (`/api/v1/retrieval`, Apache-2.0); **Dify** (hit-test desacoplado). Descartados: Verba y Cognita (**archivados** 2026). Revert de corpus: LanceDB versioning / alias-swap blue-green / LakeFS-DVC → mapea a "config swap determinista, datos branch-merge con humano".

**Riesgos de un contrato común sobre RAGs heterogéneos:** chunking heterogéneo → contexts no comparables (fix = recall por si un chunk **cubre/entail-a un span**, invariante al chunking; precedente **RAGChecker**, NeurIPS 2024 — pero "recall by span" **no es término estándar**, es sistematización propia). LLM-judge inestable (position/verbosity/self-preference bias → *"nunca uses el mismo modelo como generador y juez"*) → no delegar métricas deterministas. RAG agéntico rompe el contrato fijo `{q, contexts, a}` (gap abierto, defendible). El golden set se degrada → significancia honesta (Wilson/bootstrap/McNemar), verificar contra verdad humana.

---

## Decisiones que informó esta investigación

- **Pivote v2** → Knowledge Reliability Agent (salir de la categoría "eval tool" comoditizada; ocupar el whitespace).
- **Liderar con el gate determinista + significancia** (el moat), no con "localizar/self-heal".
- **ADR-008** → RAG propio externo BM25 (determinismo para reproducibilidad); AnythingLLM = 2º paciente U3; MCP = enterprise.
- **Read-only + humano ejecuta** = la única arquitectura compatible con un RAG que no controlás (G3).
- **"Recall by span" = contribución propia** (RAGChecker como precedente), no práctica estándar — defender con validación vs. humano.
