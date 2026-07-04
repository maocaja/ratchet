# NFR Design (ADRs por NFR) — U1 · Camino NIIF

> Vista **ADR-por-NFR** que pide el runbook E5 (Act 3). Complementa `nfr-design-patterns.md` (patrones P-1…P-5, salida de aidlc-workflows v0.1.8) presentando cada decisión atada a **su NFR** con el formato ADR completo (**⚠️ obligatorio en Consecuencias**).
> Estos ADR-U1-xx son la **proyección por NFR** de los patrones y de los ADRs de proyecto (`docs/adr/`); no introducen decisiones nuevas.

---

## ADR-U1-01: Recall-por-span determinista (offsets, τ=0.8)
**NFR relacionado:** NFR-U1-1 (Confiabilidad) · NFR-U1-2 (Reproducibilidad)
**Contexto:** La decisión de mejora/empeora debe ser confiable y reproducible; un LLM-juez como árbitro es SPOF y no reproducible. Existe verdad determinable: si el span dorado fue recuperado.
**Decisión:** Anclar la métrica en `recall-por-span` computado por **código determinista** (cobertura del span por intersección de offsets, τ=0.8). Faithfulness (LLM) queda como secundaria y **fuera de U1**.
**Alternativas consideradas:**
- LLM-juez decide el recall — descartada: SPOF, no reproducible (ver ADR-002).
- Cobertura por chunk (no por span) — descartada: no comparable entre chunkings.
**Consecuencias:**
- ✅ Métrica reproducible y comparable; el juez no es SPOF de la decisión.
- ⚠️ Exige golden set etiquetado por span de fuente (costo de curación humana).
- ⚠️ Faithfulness se difiere a U3.
**Estado:** Aceptado

## ADR-U1-02: Gate de no-regresión con CI pareado + guardrail crítico
**NFR relacionado:** NFR-U1-1 (Confiabilidad)
**Contexto:** El guardrail es 0 regresiones no detectadas; un falso negativo crítico es incidente. El gate no puede depender de un LLM ni de un delta ruidoso.
**Decisión:** Gate **determinista** (G2): aprueba solo si `CI.lower(delta_pareado) ≥ 0` (bootstrap 95%); cualquier regresión en clase crítica ⇒ revert forzado; revert **automático** si empeora.
**Alternativas consideradas:**
- Delta puntual ≥ 0 sin CI — descartada: un golden set chico haría pasar ruido como mejora.
- LLM decide deploy/revert — descartada: viola G2, no reproducible.
**Consecuencias:**
- ✅ La calidad nunca retrocede por un cambio propio; verificable mecánicamente.
- ⚠️ Golden set chico ⇒ CI ancho ⇒ cuesta *probar* mejora (barra honesta, no bug).
- ⚠️ Revert asimétrico (deriva vs. deploy propio) se difiere a U3.
**Estado:** Aceptado

## ADR-U1-03: Clave de estado canónica + idempotencia + seed fijo
**NFR relacionado:** NFR-U1-2 (Reproducibilidad/Auditabilidad)
**Contexto:** La reproducibilidad exige recomputar y que las corridas sean idempotentes; el disparador de U1 es la deriva del corpus. La composición de la clave debe tener un solo dueño (ver erratum).
**Decisión:** `StateKey=(gs_version, config_hash, corpus_hash, patch_hash, eval_params)` + `seed` para bit-exactitud; **dueño único** en `nfr-design-patterns.md §P-1`; enforced por `UNIQUE(StateKey)` en Postgres.
**Alternativas consideradas:**
- Tupla sin `corpus_hash` — descartada: colisionaría señales antes/después de la deriva.
- `k/τ` dentro de `config_hash` — descartada: mezcla knobs de Ratchet con config del RAG.
**Consecuencias:**
- ✅ Idempotencia y recompute reales; sin drift (dueño único).
- ⚠️ Requiere que el puerto exponga `corpus_fingerprint()`.
- ⚠️ La bit-exactitud exige `retrieve()` determinista para índice fijo (precondición P-2).
**Estado:** Aceptado

## ADR-U1-04: PostgreSQL desde el arranque, tras puerto/repositorio
**NFR relacionado:** NFR-U1-2 (Reproducibilidad) · NFR-U1-6 (Persistencia)
**Contexto:** `UNIQUE(StateKey)` e inmutabilidad versionada sostienen NFR-2; SQLite no ejercita esa mecánica.
**Decisión:** Postgres 16 desde el arranque (docker-compose), acceso tras puerto/repo; unit tests contra fake in-memory, integración/e2e contra Postgres real.
**Alternativas consideradas:**
- SQLite-first, migrar luego — descartada: no prueba la idempotencia real; riesgo "funciona en SQLite, falla en Postgres".
- ORM sin puerto — descartada: acopla el core, sin fake rápido.
**Consecuencias:**
- ✅ NFR-2 probado en el motor real desde el día 1.
- ⚠️ Más fricción local (Docker) y dos suites de test.
**Estado:** Aceptado

## ADR-U1-05: Frontera de agencia por import-linter (G2)
**NFR relacionado:** NFR-U1-3 (Mantenibilidad) · NFR-U1-1 (Confiabilidad)
**Contexto:** El gate/orquestador no deben llamar al LLM; "el razonamiento propone, la matemática dispone". Necesita enforcement mecánico.
**Decisión:** Contrato `import-linter` en CI que **prohíbe** a `gate/` y `orchestrator/` importar el cliente LLM (`ratchet.adapter.llm`/`anthropic`); complemento: test de que sus constructores no aceptan `LlmPort`. Fail-closed desde CG-0.
**Alternativas consideradas:**
- Solo convención + code review — descartada: no es mecánico, se viola por descuido.
- Solo import-linter — insuficiente: no atrapa inyección por constructor (por eso el test extra).
**Consecuencias:**
- ✅ G2 imposible de violar por accidente; el build falla.
- ⚠️ `import-linter` atrapa imports, no llamadas en runtime → requiere el test de no-inyección (CG-2).
**Estado:** Aceptado

## ADR-U1-06: Resiliencia — retry solo sobre lecturas, revert en mutaciones
**NFR relacionado:** NFR-U1-5 (Disponibilidad/Tolerancia a fallos)
**Contexto:** Fallos transitorios de RAG/LLM no deben tumbar la corrida; pero reintentar una mutación no idempotente es peligroso.
**Decisión:** `RetryPolicy(max=3, backoff)` envuelve **solo lecturas** (`retrieve/generate/get_config/corpus_fingerprint`); las **mutaciones** (`apply_data_patch/reindex`) **no** se reintentan — fallo ⇒ revert vía `PatchHandle` + `inconclusa`.
**Alternativas consideradas:**
- Retry genérico sobre todo — descartada: doble-aplicar el parche o dejar el índice inconsistente.
- Fail-fast sin retry — descartada: frágil ante hipos transitorios.
**Consecuencias:**
- ✅ Absorbe fallos transitorios sin arriesgar consistencia de datos.
- ⚠️ Sin circuit-breaker en U1 (endurecer); el revert añade una ruta más a testear (CG-1).
**Estado:** Aceptado

## ADR-U1-07: Dos gates humanos desacoplados (P2)
**NFR relacionado:** NFR-U1-1 (Confiabilidad) · NFR-U1-10 (Usabilidad)
**Contexto:** Nada debe avanzar sin decisión humana, pero revertir a lo seguro debe ser automático; confirmar un parche y aprobar un deploy son decisiones distintas.
**Decisión:** Dos `ApprovalRequest` distintos — US-13 (confirmar parche antes de aplicar) y US-16 (aprobar deploy tras el gate técnico). `pending` es waiting seguro; sin aprobador nada se rompe.
**Alternativas consideradas:**
- Una sola confirmación — descartada: colapsa dos decisiones con riesgos distintos.
- Aprobación también para revertir — descartada: revertir a lo seguro no debe esperar a un humano.
**Consecuencias:**
- ✅ Control humano sobre lo que AVANZA; el baseline se mantiene si no hay aprobador.
- ⚠️ Cuello de botella humano deliberado (latencia de decisión), aceptado como seguridad.
**Estado:** Aceptado

---

## Trazabilidad ADR-U1 → NFR → patrón
| ADR-U1 | NFR | Patrón (`nfr-design-patterns.md`) | ADR de proyecto (`docs/adr/`) |
|---|---|---|---|
| 01 | NFR-U1-1/2 | — (métrica, functional-design BL-1) | ADR-002 |
| 02 | NFR-U1-1 | P-3 (gate)… | ADR-003 |
| 03 | NFR-U1-2 | P-1, P-2 | ADR-005 |
| 04 | NFR-U1-2/6 | P-1 | ADR-007 |
| 05 | NFR-U1-3 | P-3 | ADR-001 (P5) |
| 06 | NFR-U1-5 | P-4 | — |
| 07 | NFR-U1-1/10 | P-5 | ADR-003 |
