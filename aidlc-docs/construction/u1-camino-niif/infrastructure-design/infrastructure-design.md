# Infrastructure Design (mínimo) — U1 · Camino NIIF

> Topología **mínima** del walking skeleton: un desplegable + Postgres, RAG de muestra in-process. Todo lo enterprise queda documentado como *escalado*, NO se construye en U1.
> Decisiones: Q1 RAG in-process · Q2 migraciones al arranque · Q3 CI (ruff+import-linter+pytest) · Q4 `app`+`db`.

> Estructura en **3 capas** (runbook E5, Act 4): mapa de servicios · configuración por servicio · definiciones transversales.

## Capa 1 — Mapa de servicios
| Componente (`application-design`) | Servicio (local/nube) | Configuración base |
|---|---|---|
| API Entry Point + CLI (C10) | Contenedor `app` (FastAPI + uvicorn + Typer) | Python 3.12 · entrypoint `alembic upgrade head → uvicorn` · stateless |
| Core + Job Runner (C3–C9) | **In-process** dentro de `app` | Job Runner **síncrono in-process** (cola real = endurecer) |
| RAG de muestra (C1 paciente) | **In-process** tras `RagPatientPort` | corpus NIIF/NIA + vector store embebido (TBD Chroma/FAISS); `generate()` stub (CG-3) |
| LLM (C4 Localizer / juez U3) | Anthropic API (externo, red) | `LlmPort`; **dormido** en camino NIIF |
| Persistencia (C12) | Contenedor `db` PostgreSQL 16 | golden set, baseline, RunRecords, writeups, approvals; `UNIQUE(StateKey)` (P-1) |
| CI | GitHub Actions | `ruff` + `import-linter` (G2) + `pytest` (unit/PBT + integración/e2e) |

- **RAG in-process (Q1):** impl. Python del RAG aislada por `RagPatientPort`; la costura P5 se respeta **por interfaz**, no por red. Migrar a "contenedor por HTTP" (U3) = cambiar la impl. del puerto, no el core. Vector store concreto = TBD (Code Gen), debe cumplir `retrieve` determinista (P-2).

## Capa 2 — Configuración por servicio
- **`app`:** un solo contenedor; entrypoint corre migraciones y luego sirve; stateless (todo el estado en `db`).
- **`db` (PostgreSQL 16):** migraciones **Alembic** al arranque (Q2); una sola instancia ⇒ sin carrera de migración. `UNIQUE(StateKey)` enforcea idempotencia (P-1).
- **Config/secrets:** `pydantic-settings` + `.env` **no versionado** (`.gitignore`); falla rápido si falta `DATABASE_URL`. `ANTHROPIC_API_KEY` **condicional** (ver §Determinismo): el e2e NIIF corre **sin ella**; solo se requiere para el ramo ambiguo del localizador y U3.
- **CI:** ver §CI mínima.

## Determinismo del camino NIIF — libre-de-LLM *(propiedad de diseño)*
> El escenario no-negociable de U1 es **determinista end-to-end y hermético** (sin red, sin API key, sin flakiness, gratis en CI). Esto NO es un accidente: es consecuencia directa de la regla de oro y los guardrails.

**Por qué es libre-de-LLM:**
- **Recall = código** (BL-1) — sin LLM.
- **Localizador:** en el camino NIIF, `span_vigente_en_corpus=False` es la regla determinista de **mayor prioridad** y es concluyente ⇒ el `Localizer` (LLM) **no se invoca**. El LLM solo actúa en el ramo `AMBIGUO`, que este camino no toca.
- **Gate = código** (G2) — sin LLM.
- **`generate()` del RAG:** el único consumidor es el probe `respuesta_usa_span` (capa "generación"), que el camino NIIF **nunca alcanza**. Además, en U1 el **RAG de muestra stubbea `generate()`** (determinista, sin red).

**Consecuencias:**
- **CI/e2e NIIF corre hermético:** sin `ANTHROPIC_API_KEY`, sin red, reproducible, sin costo. Ventaja fuerte de testeo — declarada como propiedad, no como suerte.
- **`generate()` real (P5):** un `generate()` real necesitaría el **cliente LLM propio del RAG** (el paciente NO usa el `LlmPort` de Ratchet). Se difiere a **U3** (con faithfulness/generación). En U1 = stub → **carry-over CG-3**.
- **La única salida de red viva en U1** (Anthropic vía `LlmPort` desde `investigator/`) queda **dormida en el camino NIIF**; se ejercita solo si el diagnóstico es ambiguo.

## Capa 3 — Definiciones transversales
- **Seguridad:** secrets solo por `.env` no versionado (Security Baseline = No); sin authn/authz (operador único local); sin IAM/VPC (un solo host local; en nube = endurecer). Frontera de agencia G2 por `import-linter`.
- **Observabilidad:** log estructurado por **transición de estado** del `RunRecord`; evidencia (writeup, verdict, approvals, decisión) persistida y consultable por `run_id`. Métricas/tracing externos (LangFuse) + alarmas = fase endurecer.
- **Redes:** todo en `docker-compose` local (`app` ↔ `db`); única salida a internet = Anthropic vía `LlmPort` (**dormida** en camino NIIF). Sin multi-AZ / LB (endurecer).
- **Migraciones:** Alembic al arranque (detallado en Capa 2).

## CI mínima (Q3)
```text
GitHub Actions (push / PR):
  1. ruff check + ruff format --check      # lint/formato
  2. import-linter                          # frontera de agencia G2 (gate/orchestrator sin LLM)
  3. pytest tests/unit  (+ hypothesis)      # núcleo determinista, fake in-memory
  4. pytest tests/integration tests/e2e     # contra Postgres de servicio (escenario NIIF)
                                             # HERMÉTICO: sin ANTHROPIC_API_KEY, sin red (ver §Determinismo)
```
- **Sin deploy automatizado** en U1. El pipeline valida, no despliega.
- **El e2e NIIF no requiere secretos de red** ⇒ la CI no necesita `ANTHROPIC_API_KEY` para el camino no-negociable.
- CG-2 (test de no-inyección de `LlmPort` en gate/orchestrator) corre dentro de (3).

## Trazabilidad a NFR / SPOF
| NFR / SPOF (arquitectura) | Cómo lo cubre U1 |
|---|---|
| Postgres SPOF — **runs/reportes/baseline** | **recomputables** desde (golden set + estado del RAG); backups = endurecer |
| Postgres SPOF — **golden set** *(la verdad, NO recomputable)* | El golden set son ≥50 ítems etiquetados por un humano (BR-76: "la verdad es el golden set que definió un humano") ⇒ **NO se recomputa**. Se **siembra desde una fuente versionada en el repo** (archivo/seed de migración) ⇒ reconstruible desde control de versiones aunque se pierda Postgres. Así "backups = endurecer" es válido sin arriesgar la verdad |
| App proceso único SPOF | stateless → reinicio rápido; multi-instancia+LB = endurecer |
| Reproducibilidad (NFR-2) | Postgres real desde el arranque prueba `UNIQUE(StateKey)` e idempotencia |
| Frontera de agencia (G2) | `import-linter` en CI |

## No-metas de U1 (diferido a "endurecer" — documentado, no construido)
- IaC (Terraform/CDK) · orquestador (K8s/EKS) · load balancer + health checks + multi-AZ · cola gestionada (SQS/EventBridge) o RQ+Redis · Lambda workers · gateway NestJS · observabilidad (LangFuse) · secrets manager · deploy automatizado. Todo en `arquitectura.md` Seg 2 como escalado enterprise.
