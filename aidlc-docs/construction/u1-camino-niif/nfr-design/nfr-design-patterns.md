# NFR Design — Patrones — U1 · Camino NIIF

> Cómo se satisfacen los NFR de U1 mediante **patrones de diseño**, tecnología-agnóstico. Esta etapa es la **casa legítima de la clave de estado** (hashing/idempotencia) — se define aquí UNA vez y el resto la referencia.
> Insumos: `nfr-requirements/`, `functional-design/`, erratum de `audit.md`. Decisiones: Q1 `eval_params` explícito · Q2 retry+backoff · Q3 UNIQUE en DB · Q4 import-linter · Q5 fingerprint por doc.

---

## P-1 · Patrón de Estado & Idempotencia *(dueño único de la clave — NFR-U1-2)*

### Clave de estado canónica (definición única)
```text
StateKey = (
    golden_set_version,     # versión inmutable del golden set
    config_hash,            # hash de la config del RAG (get_config()) — SOLO del paciente
    corpus_hash,            # hash del contenido del corpus (externo, ver cómputo)
    patch_hash,             # identidad del parche aplicado (null si no hay)
    eval_params,            # knobs de evaluación de Ratchet: (k, tau) — NO van en config_hash
)
ReproKey = StateKey + seed  # + seed del bootstrap → reproducibilidad bit-exacta del CI
```
- **Decisión Q1:** `eval_params=(k,τ)` es un componente **explícito**, no se pliega en `config_hash`. Razón: `config_hash` describe al *paciente* (RAG); `k/τ` son de *Ratchet*. Cada hash conserva un solo dueño semántico.
- **`RunRecord` es idempotente por `StateKey`.** El recall es **bit-exacto** por `ReproKey` (bajo la precondición P-2).

### Cómputo de cada hash (determinista)
```text
config_hash  = sha256(canonical_json(rag.get_config()))
corpus_hash  = sha256(canonical_json( sorted(
                   (doc_id, sha256(normalize(doc_content)))     # Ratchet.normalize() — el MISMO de BL-1
                   for (doc_id, doc_content) in rag.corpus_fingerprint() ) ))   # Q5
patch_hash   = sha256(canonical_json(patch))  ||  null
eval_params  = (k, tau)                                          # valores, no hash

# Nota (patch_hash vs corpus_hash): en la RAMA DE DATOS un parche cambia un Document ⇒ cambia
# también corpus_hash, por lo que patch_hash es parcialmente redundante aquí. NO es bug: patch_hash
# gana su rol propio en la RAMA CONFIG (U2), donde un cambio de config no toca el corpus. Se conserva
# para que la clave sea uniforme entre ramas.
```
- **`corpus_hash` — corpus externo:** lo computa **Ratchet**, no el RAG. El corpus vive tras el adaptador ⇒ `RagPatientPort` expone `corpus_fingerprint() -> list[(doc_id, doc_content: str)]` (**contenido crudo**, no pre-hasheado) y Ratchet aplica **su** `normalize()` + `sha256`. Ratchet **no** se acopla al vector store interno del paciente.
  - **Dueño único de la normalización (fix review):** el `normalize()` que se aplica aquí es **el mismo** que usa el recall para los offsets del span (BL-1). Si el RAG pre-hasheara, Ratchet perdería control de la normalización y `corpus_hash` miraría un texto normalizado distinto al del cálculo de recall — inconsistencia silenciosa. Por eso el puerto devuelve contenido, no hash.
- `canonical_json` = serialización con claves ordenadas y separadores fijos ⇒ hash estable e independiente del orden.
- Un parche que reemplaza un `Document` cambia su `doc_content_hash` ⇒ cambia `corpus_hash` ⇒ la corrida post-parche es un estado distinto (no deduplica con la previa).

### Enforcement de idempotencia (Q3)
- **Constraint `UNIQUE(StateKey)` a nivel DB** + upsert idempotente en `RunRepository`. La DB es la última línea: aunque la app falle o se re-dispare, no hay duplicados.
- El repositorio **fake in-memory** (tests) replica la unicidad para paridad de comportamiento.

### Reconciliación del Functional Design *(cierre del erratum — mismo diff)*
Los 3 literales que fijaban la tupla en el nivel equivocado se **bajan a referencia** a este documento:
| Artefacto (FD) | Antes | Después |
|---|---|---|
| `business-rules.md` BR-73 | tupla literal | "idempotente por su **clave de estado** (ver `nfr-design-patterns.md` §P-1)" |
| `domain-entities.md` `RunRecord.run_id` | tupla literal | "idempotente por la **clave de estado** (§P-1)" |
| `domain-entities.md` glosario `StateRef` | tupla literal | "= la **clave de estado** canónica (§P-1)" |
> No es rediseño: es eliminar duplicación y apuntar al dueño único. Registrado en `audit.md`.

---

## P-2 · Patrón de Reproducibilidad *(NFR-U1-2)*

- **Bootstrap determinista:** `BootstrapEstimator(seed)` usa `numpy.default_rng(seed)`; `B=1000`. Mismo `ReproKey` ⇒ mismo `recall_span`, `per_item`, `ci` bit a bit.
- **Precondición de determinismo del `retrieve` (carry-over #2, enunciada como patrón):**
  > La garantía bit-exacta del recall vale **siempre que `retrieve()` del RAG sea determinista para un estado de índice fijo** (capturado por `corpus_hash`+`config_hash`). El `seed` controla el **bootstrap de Ratchet**, NO el `retrieve` del paciente.
  - **Táctica:** el adaptador del paciente propio garantiza `retrieve` determinista (orden estable, sin ANN aleatorio); si un store usa ANN no-determinista, se fija índice/orden o se documenta la tolerancia. Test de determinismo del adaptador: `retrieve` 2× sobre índice fijo → idéntico.
- **Recompute, no caché-como-verdad:** el `Report` se recomputa desde datos versionados; la métrica persistida es un registro, no la fuente de verdad (BR-74).

---

## P-3 · Patrón de Frontera de Agencia *(G2/G3 — NFR-U1-1/3)*

- **Regla:** `gate/` y `orchestrator/` **no importan** el cliente LLM ni `adapter/llm`. Toda agencia LLM vive río arriba (`investigator/`, y en U3 `experimenter/`) y devuelve datos estructurados ya verificados.
- **Enforcement (Q4): `import-linter` en CI** — contrato declarativo de capas prohibidas; el build **falla** si se viola.
- **Límite de `import-linter` y cómo se cierra (fix review):** el linter atrapa **imports estáticos**, pero G2 es *"el orquestador no LLAMA al LLM"*. Si a `gate/`/`orchestrator/` se les **inyectara** un `LlmPort` como dependencia, no habría import propio y el linter pasaría — falso hermético. Regla adicional: **los constructores/firmas de `gate/` y `orchestrator/` no aceptan `LlmPort`** (ni ningún cliente LLM) como parámetro. Verificación: (a) test que inspecciona las firmas de construcción de esos módulos; (b) segunda red = subagente `code-reviewer` (guardrails G1/G2/G3). `import-linter` es **necesario, no suficiente**.
- **G3 en el flujo:** el `Localizer` (LLM) emite `Diagnosis{capa, evidencia}`; `verify_claim` (determinista) la recomprueba antes de habilitar cualquier acción. El orquestador rutea sobre el claim **ya verificado**, no re-razona.

---

## P-4 · Patrones de Resiliencia *(NFR-U1-1/5 — P1)*

- **Fallo de RAG/LLM (Q2): retry acotado + backoff — SOLO sobre lecturas.** `RetryPolicy(max=3, backoff=exponencial)` envuelve **únicamente operaciones de lectura idempotentes** (`retrieve`, `generate`, `get_config`, `corpus_fingerprint`). Si persiste ⇒ corrida **`inconclusa`**, baseline intacto (P1). Sin circuit-breaker (endurecer).
- **Mutaciones NO se reintentan a ciegas (fix review):** `apply_data_patch` y `reindex` son operaciones que **mutan**; reintentarlas arriesga doble-aplicar el parche o dejar el índice inconsistente. Regla: fallo de una mutación ⇒ **`revert` vía `PatchHandle` + corrida `inconclusa`** (BR-65), nunca retry ciego. (Se arrastra a Code Gen como **CG-1** para que la implementación no envuelva estas ops en `RetryPolicy`.)
- **Atomicidad del deploy de datos + revert:** `apply_data_patch` + `reindex` es atómico con verificación post; si `reindex` falla ⇒ **revert automático** del parche + corrida `inconclusa` (BR-65). `PatchHandle` restaura doc + índice previos.
- **Degradación segura:** ninguna decisión se toma con datos incompletos; el fallo es **visible** en el skeleton síncrono y la corrida se re-ejecuta (idempotente por `StateKey`).
- **No-decidir-con-el-juez:** el gate se ancla en recall determinista; una caída del LLM nunca vuelve al juez un SPOF de la decisión (mitigación de diseño, SPOF arquitectura).

---

## P-5 · Patrón de Gate Humano *(P2 — NFR-U1-1)*

- **Dos aprobaciones desacopladas** (US-13 confirmar parche, US-16 aprobar deploy) como transiciones explícitas de la máquina de estados; ambas modeladas como `ApprovalRequest{kind}`.
- **`pending` no bloquea el sistema:** sin aprobador, la corrida queda en un **waiting seguro** (`ESPERANDO_CONFIRMACION`/`ESPERANDO_APROBACION` — estados **no terminales** que esperan approve/reject) y **el baseline se mantiene**. Solo al **rechazar o expirar** pasa a un terminal seguro (`DETENIDA_HUMANO`/`RECHAZADA`). Cuello deliberado, no fragilidad (arquitectura Seg 4).

---

## No-metas de U1 (patrones diferidos a "endurecer")
- Circuit-breaker, cola real (RQ+Redis) + DLQ, caché de salidas LLM, alta disponibilidad (multi-instancia + LB), tracing externo (LangFuse), authn/authz. Todos documentados como fast-follow, ninguno fingido como hecho.

## Trazabilidad NFR → patrón
| NFR-U1 | Patrón |
|---|---|
| NFR-U1-1 Confiabilidad | P-3, P-4, P-5 |
| NFR-U1-2 Reproducibilidad | **P-1**, P-2 |
| NFR-U1-3 Extensibilidad | P-3 (frontera por imports) |
| NFR-U1-5 Disponibilidad | P-4 |
