# NFR Requirements — U1 · Camino NIIF

> **Ligero por diseño.** `specs/arquitectura.md` Seg 3 fijó el top-3 (Confiabilidad, Reproducibilidad, Extensibilidad) y Seg 4 los SPOF. Este documento los **acota a U1** como criterios **testeables** y consolida las decisiones del plan. No re-decide arquitectura.
> Cada NFR se enuncia como criterio verificable (columna "Verificación"). Los que ya están cubiertos por `business-rules.md` se **referencian**, no se duplican.
> Extensión **Security Baseline = No** → sin NFR de seguridad más allá de higiene de secrets.

## Conformidad con los 6 atributos de calidad (runbook E5)
Cada uno de los 6 atributos canónicos tiene un NFR con **valor numérico/verificable**:
| Atributo (runbook) | NFR-U1 | Valor numérico / criterio |
|---|---|---|
| **Desempeño** | NFR-U1-4 | Una corrida completa del loop (gs≥50, secuencial) **< 5 min**; `B=1000` bootstrap |
| **Seguridad** | NFR-U1-8 | Keys solo por `.env` no versionado; sin authn (operador único). Security Baseline = No |
| **Confiabilidad** | NFR-U1-1, NFR-U1-5 | Gate aprueba solo si `CI.lower(delta)≥0`; **0** regresiones críticas no detectadas; fallo ⇒ `inconclusa` |
| **Usabilidad** | **NFR-U1-10** | El operador completa "disparar → leer reporte" en **≤ 3 comandos** CLI; reporte antes/después legible sin recomputar a mano |
| **Mantenibilidad** | NFR-U1-3 | Un cambio en un módulo impacta **≤ 1** paquete vecino (costuras por puerto); frontera G2 verificable por import-linter |
| **Escalabilidad** | **NFR-U1-11** | 1 RAG (concurrencia = NFR-U1-9); golden set escala **de ≥50 (piso significancia) hasta donde una corrida siga < 5 min** (ligado a NFR-U1-4, eval secuencial O(n)); multiplicar carga = endurecer |

## NFR-U1-1 · Confiabilidad / Corrección *(NFR estrella #1)*
| Requisito | Criterio de aceptación (U1) | Verificación |
|---|---|---|
| El sistema nunca despliega algo peor | El gate aprueba **solo si** `CI.lower(delta_pareado) ≥ 0` (BR-32) | test de regresión inyectada → revert |
| 0 regresiones críticas no detectadas | Toda regresión en clase crítica ⇒ revert inmediato (BR-34, guardrail 🔒) | inyectar regresión crítica que no baja el agregado |
| Revert es automático y seguro | `revert` no requiere aprobación humana; restaura estado previo exacto (BR-35, BR-64) | apply→revert = estado previo, sin approval |
| No decidir con datos incompletos | Fallo de RAG/LLM/reindex ⇒ corrida `inconclusa`, baseline intacto (BR-16, BR-65) | inyectar `RagError`/`ReindexError` |
| La decisión se ancla en lo determinista | El gate no importa el cliente LLM (BR-31, G2) | grep estático: `gate/` y `orchestrator/` sin import de LLM |

## NFR-U1-2 · Reproducibilidad / Auditabilidad *(NFR estrella #2)*

> **Dueño de la clave de estado = NFR Design.** La composición canónica de la clave (qué se hashea y cómo: `config_hash`, `corpus_hash`, `patch_hash`, ubicación de `k/τ`, `seed`) se **define una sola vez** en `nfr-design/nfr-design-patterns.md` ("hashing de estado / idempotencia"). Lo que sigue en esta tabla es el **requisito** (qué debe cumplir), no la especificación literal; los literales del Functional Design se bajan a referencia en esa etapa (erratum registrado). Principio ratchet: forward-only, dueño único.
| Requisito | Criterio de aceptación (U1) | Verificación |
|---|---|---|
| **Alcance de la garantía (decisión Q3=A)** | **Solo lo determinista es bit-exacto**: `recall_span`, `per_item`, `ci` (seed fijo). Lo que depende del LLM (generación) **se excluye explícitamente** de la garantía | test: misma clave de reproducibilidad → recall+CI idénticos bit a bit |
| **Precondición del retrieve (explícita)** | La garantía bit-exacta del recall aplica **siempre que el `retrieve()` del RAG sea determinista para un estado de índice fijo** (capturado por `corpus_hash`+`config_hash`). El `seed` fijo controla el **bootstrap de Ratchet**, NO el retrieve del paciente. Si el vector store usa ANN no-determinista (Chroma/FAISS, TBD), Ratchet fija el índice/orden o documenta la tolerancia; sin esta precondición el NFR sería infalsificable | test de determinismo del adaptador: `retrieve` 2× sobre índice fijo → mismo resultado |
| Recompute determinista | El `Report` se recomputa desde datos versionados; la métrica no se persiste como verdad independiente de sus insumos (BR-74) | recomputar report y comparar |
| **Clave de reproducibilidad/idempotencia** | Recall bit-exacto y `record_run` idempotente por la **clave de estado** (composición y `seed`: **dueño único** `nfr-design/nfr-design-patterns.md §P-1`; BR-73). No se re-enumera aquí (evita re-drift del erratum) | doble record → 1 run; distintos componentes de la clave de estado (§P-1) → 2 runs |
| Inmutabilidad versionada | golden set y baseline inmutables por versión (BR-21, BR-22) | intento de mutación → error |
| Audit trail | Se persisten writeup, verdict, approvals y decisiones por `run_id` | inspección del RunRecord persistido |
| Bootstrap determinista | `B=1000`, **seed fijo** por corrida guardado en RunRecord (BR-36) | mismo input+seed → mismo CI |

## NFR-U1-3 · Extensibilidad / Mantenibilidad *(NFR estrella #3)*
| Requisito | Criterio de aceptación (U1) | Verificación |
|---|---|---|
| Adaptador por interfaz (P5) | El core habla con RAG/LLM/store solo por `RagPatientPort` y puertos; ningún proveedor hardcodeado en el core | grep: core sin SDK de proveedor |
| Módulos con costuras | Código en `src/ratchet/<módulo>/`; `gate/` y `orchestrator/` no importan el cliente LLM (frontera de agencia) | estructura de paquetes + import-linter opcional |
| Testabilidad | Núcleo determinista con **PBT** (hypothesis) en recall-por-span, gate y localizador; e2e del escenario NIIF; factories, no hardcode (testing.md) | suite pytest + PBT verde |

## NFR-U1-4 · Performance *(blando — decisión Q2)*
| Requisito | Criterio de aceptación (U1) | Verificación |
|---|---|---|
| Presupuesto de una corrida | **< 5 min** para una corrida completa del loop sobre golden set ≥50, **secuencial** (sin optimización prematura) | cronometrar e2e del escenario NIIF |
| Sin SLA duro | No hay objetivo de throughput ni latencia de API; sistema de fondo (arquitectura Seg 3) | — |
| Optimización opcional | Paralelizar `retrieve` sobre el golden set solo si sobra presupuesto; no bloquea U1 | — |

## NFR-U1-5 · Disponibilidad / Tolerancia a fallos
| Requisito | Criterio de aceptación (U1) | Verificación |
|---|---|---|
| Degradación segura | Caída de RAG/LLM ⇒ corrida `inconclusa`, baseline se mantiene (P1); el fallo es **visible** en el skeleton síncrono y se re-corre (SPOF Job Runner) | inyección de fallo |
| Aplicación atómica | Deploy de parche + reindex atómico con verificación post; revert si falla a medias (Q8/BR-65; SPOF "deploy a medias") | `ReindexError` → revert |
| Sin alta disponibilidad en MVP | Proceso único stateless (estado en Postgres); HA (múltiples instancias + LB) = endurecer | — |

## NFR-U1-6 · Persistencia / Durabilidad *(decisión Q1)*
| Requisito | Criterio de aceptación (U1) | Verificación |
|---|---|---|
| Motor de datos | **PostgreSQL desde el arranque** (docker-compose), no SQLite | app arranca contra Postgres |
| Frontera de persistencia | Acceso vía **puerto/repo**; tests unitarios contra *fake* in-memory, integración/e2e contra Postgres real | dos suites (unit rápida / integración) |
| Migraciones | Esquema versionado por migraciones (SPOF Postgres) | migración aplica limpia desde cero |
| Integridad del baseline | El baseline vigente es la fuente de verdad; no se corrompe por corridas concurrentes (en U1 no hay concurrencia — Q5) | constraint + test |

## NFR-U1-7 · Observabilidad *(mínima — Q6)*
| Requisito | Criterio de aceptación (U1) | Verificación |
|---|---|---|
| Trazabilidad de la corrida | Log estructurado por **transición de estado** del RunRecord (ver máquina de estados) | inspección de logs de un e2e |
| Persistencia de evidencia | writeup, verdict, approvals y decisión quedan persistidos y consultables por `run_id` | `GET /runs/{id}/report` |
| Sin observabilidad externa | Métricas/tracing (LangFuse) = fase endurecer, fuera de U1 | — |

## NFR-U1-8 · Seguridad *(mínima — Security Baseline off, Q7)*
| Requisito | Criterio de aceptación (U1) | Verificación |
|---|---|---|
| Higiene de secrets | Keys LLM por variable de entorno / `.env` **no versionado**; nunca en código ni repo | grep: sin keys en el árbol; `.env` en `.gitignore` |
| Sin authn/authz en MVP | La CLI/API es de un solo operador local; sin control de acceso (roles = roadmap) | — |

## NFR-U1-9 · Concurrencia *(Q5)*
| Requisito | Criterio de aceptación (U1) | Verificación |
|---|---|---|
| Una corrida a la vez | Loop síncrono in-process; sin ejecución paralela de corridas en U1 | — |
| Job Runner real | Cola (RQ+Redis) + retry/DLQ = fase endurecer, no U1 | — |

## NFR-U1-10 · Usabilidad *(atributo runbook; operador CLI/API)*
| Requisito | Criterio de aceptación (U1) | Verificación |
|---|---|---|
| Flujo mínimo de comandos | El operador completa "disparar corrida → aprobar → leer reporte" en **≤ 3 comandos** (`ratchet run` · `ratchet approve <id>` · `ratchet report <id>`) | e2e por CLI cuenta los comandos |
| Reporte auto-explicativo | El reporte antes/después es legible **sin recomputar a mano**: recall before/after con CI, delta, decisión y writeup en una vista | inspección del `GET /runs/{id}/report` |
| Confirmaciones claras | Los dos gates humanos (US-13/US-16) presentan qué se aplicará y su evidencia antes de pedir decisión | revisión de la salida de aprobación |

## NFR-U1-11 · Escalabilidad *(atributo runbook; acotado en U1)*
| Requisito | Criterio de aceptación (U1) | Verificación |
|---|---|---|
| Carga de U1 | **1 RAG paciente**; concurrencia de corridas = **NFR-U1-9** (1 a la vez, síncrono). Sin objetivo de throughput | — (ver NFR-U1-9) |
| Golden set | Escala **de ≥50 (piso de significancia) hasta donde una corrida siga cumpliendo NFR-U1-4 (< 5 min)** — evaluación secuencial O(n) en nº de ítems, sin cambio de arquitectura. Techo exacto = **TBD** (depende de la latencia del RAG paciente) | eval con gs grande < 5 min |
| Crecimiento futuro | Multiplicar carga (varias corridas/pacientes en paralelo) = **fase endurecer** (cola real RQ+Redis, workers); documentado, no U1 | — (roadmap) |

---

## Trazabilidad a NFR de arquitectura
| Arquitectura (Seg 3/4) | NFR-U1 |
|---|---|
| Confiabilidad/Corrección | NFR-U1-1, NFR-U1-5 |
| Reproducibilidad/Auditabilidad | NFR-U1-2, NFR-U1-7 |
| Extensibilidad/Mantenibilidad | NFR-U1-3, NFR-U1-6 |
| Escala/latencia/costo (fuera del top-3) | NFR-U1-4, NFR-U1-9 (acotados, sin SLA) |
| SPOF (RAG, LLM, Postgres, Worker, deploy a medias) | NFR-U1-5, NFR-U1-6 |
