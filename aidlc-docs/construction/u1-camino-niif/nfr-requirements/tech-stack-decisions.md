# Tech Stack Decisions — U1 · Camino NIIF

> Consolidación de tecnologías concretas para **construir U1**. Coherente con `specs/arquitectura.md`, `.claude/rules/python.md` y las decisiones NFR. Versiones fijadas (reproducibilidad).
> Principio rector: **simplicidad sobre complejidad** (Regla #1 de arquitectura) — walking skeleton, monolito modular.

## Lenguaje y runtime
| Decisión | Elección | Razón |
|---|---|---|
| Lenguaje | **Python 3.12+** | stack del PRD; type hints modernos |
| Gestor de dependencias | **uv** (fallback `pip`), versiones fijadas | reproducibilidad; rápido |
| Lint + formato | **ruff** (lint y formato; sin black/isort aparte) | regla `python.md` |
| Type hints | obligatorios en funciones públicas; `mypy` opcional en núcleo determinista | mantenibilidad |

## Backend / API
| Decisión | Elección | Razón |
|---|---|---|
| Framework API | **FastAPI** | PRD; C10 |
| CLI | **Typer** (espeja los verbos `ratchet run|report|approve`) | ergonomía; misma superficie que la API (C10) |
| Servidor ASGI | **uvicorn** | estándar FastAPI |
| Modelos/validación | **Pydantic v2** | tipa entidades de dominio; serialización del Report |
| Job Runner (U1) | **síncrono in-process** (función/servicio), detrás de una interfaz `JobRunner` | walking skeleton; cola real (RQ+Redis) = endurecer |

## Persistencia *(decisión Q1 = Postgres desde el arranque)*
| Decisión | Elección | Razón |
|---|---|---|
| Motor | **PostgreSQL 16** (docker-compose) | NFR-2 real (idempotencia, versionado); destino de arquitectura |
| Acceso a datos | **SQLAlchemy 2.x (core/ORM)** tras **puerto/repositorio** | costura P5; tests contra fake in-memory |
| Migraciones | **Alembic** | esquema versionado (SPOF Postgres) |
| Test doble | repos con implementación **in-memory** para unit tests | velocidad; integración/e2e usan Postgres |

## Evaluación / Estadística *(núcleo determinista)*
| Decisión | Elección | Razón |
|---|---|---|
| Cálculo de recall-por-span | **Python puro** (intersección de intervalos de offsets) | determinista, sin dependencias pesadas |
| Bootstrap CI | **NumPy** con **seed fijo** (`default_rng(seed)`), B=1000 | reproducible (NFR-2); evita dependencia de scipy si no hace falta |
| Test pareado (opcional, reporte) | McNemar vía `statsmodels` **solo si** se decide reportarlo (Q3 gate = CI) | el gate usa CI; McNemar es evidencia opcional |
| PBT | **hypothesis** | invariantes de recall/gate/localizador (testing.md) |

## AI / LLM *(río arriba del gate — G2)*
| Decisión | Elección | Razón |
|---|---|---|
| Cliente LLM | **Anthropic (Claude)** vía SDK oficial, tras un **puerto `LlmPort`** | juez (U3) + generación del RAG de muestra; nunca en `gate/`/`orchestrator/` |
| Uso en U1 | **mínimo**: el Localizer es LLM "delgado" y solo desambigua; las sondas y el gate son deterministas | frontera de agencia; en el escenario NIIF el LLM casi no decide |
| Faithfulness / juez | **NO en U1** (llega en U3) | regla de oro; BR-15 |
| Manejo de keys | variable de entorno / `.env` no versionado | Q7; Security Baseline off |

## RAG de muestra (paciente propio) *(sistema externo vía adaptador)*
| Decisión | Elección | Razón |
|---|---|---|
| Rol | **sistema externo** detrás de `RagPatientPort`; el vector store es del RAG, NO de Ratchet | P5; costura |
| Corpus | normas contables públicas **NIIF/NIA** (incluye NIIF 16 para el escenario de deriva) | dominio del PRD |
| Vector store del RAG | **decisión diferida a Infrastructure/Code Gen** (candidato ligero: Chroma/FAISS embebido) | pertenece al RAG; se concreta al construir el paciente de muestra — **TBD** |
| **Determinismo del `retrieve` (requisito NFR-2)** | El adaptador debe garantizar `retrieve()` **determinista para un estado de índice fijo** (o Ratchet fija índice/orden). Si el store usa ANN no-determinista, se documenta la tolerancia | precondición de la garantía bit-exacta de recall |
| **Huella del corpus (requisito NFR-2)** | `RagPatientPort` expone `corpus_fingerprint() -> list[(doc_id, doc_content: str)]` (contenido crudo); Ratchet normaliza+hashea con su `normalize()` (mismo de BL-1) | habilita la clave de idempotencia/reproducibilidad |
| Data ops (G1) | el paciente propio **soporta** `supports_data_ops()` (reemplazo de doc + reindex) | habilita la rama de datos de U1 |

## Testing / Calidad
| Decisión | Elección | Razón |
|---|---|---|
| Framework | **pytest** | testing.md |
| PBT | **hypothesis** (parcial, núcleo determinista) | extensión aprobada en Requirements |
| e2e | escenario NIIF de `stories.md` end-to-end (Postgres real) | criterio de "hecho" de U1 |
| Regresiones inyectadas | tests que inyectan regresión conocida (agregada, crítica, claim falso) | 0 no detectadas dentro de cobertura |

## Empaquetado / entorno local
| Decisión | Elección | Razón |
|---|---|---|
| Orquestación local | **docker-compose**: app + PostgreSQL | arranque reproducible |
| Config | **pydantic-settings** + `.env` | 12-factor ligero |
| Estructura | `src/ratchet/<módulo>/` (adapter, registry, evaluator, investigator, gate, monitor, reporter, orchestrator, api, persistence, domain) + `tests/` | unit-of-work.md Q4=A |

## Decisiones diferidas (TBD explícitos)
- **Vector store concreto del RAG de muestra** — se fija al construir el paciente (Infrastructure/Code Gen); condicionado al requisito de determinismo del `retrieve`.
- **mypy en CI** — opcional; se decide en Build & Test.
- **McNemar en el reporte** — opcional; el gate ya decide por CI.
- *(CLI resuelto: **Typer**, ver Backend/API — ya no es TBD.)*

## Explícitamente FUERA de U1 (endurecer / unidades posteriores)
- Cola real (RQ+Redis), retry/DLQ · gateway NestJS · SQS/EventBridge · Lambda/EKS · Terraform/CDK · LangFuse · authn/authz · 2º paciente open-source (U3) · faithfulness/LLM-judge (U3) · rama config + Experimenter (U2).
