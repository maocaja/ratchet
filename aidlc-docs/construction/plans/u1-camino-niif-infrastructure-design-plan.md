# Plan de Infrastructure Design (mínimo) — U1 · Camino NIIF

> Fase: **CONSTRUCTION** · Unidad: **U1 · Camino NIIF** · Fecha: 2026-07-03
> Objetivo: topología de despliegue **mínima** del walking skeleton. Tecnología-agnóstico donde importa, concreto donde ya está decidido.
> **Mínimo por diseño:** monolito modular, un desplegable, síncrono in-process. Todo lo enterprise (SQS, Lambda, Terraform, NestJS gateway) está documentado en `arquitectura.md` como *escalado*, NO se construye aquí.
> Insumos: `nfr-design/`, `nfr-requirements/tech-stack-decisions.md` (Postgres 16, docker-compose ya decididos).
> Salidas: `infrastructure-design/infrastructure-design.md`, `infrastructure-design/deployment-architecture.md`.

## Lo ya decidido (no se re-pregunta)
- **Un desplegable:** monolito modular Python (FastAPI + CLI Typer). Estado en Postgres → app stateless.
- **PostgreSQL 16** vía docker-compose. Migraciones **Alembic**.
- **Job Runner síncrono in-process** (cola real = endurecer).
- **CI:** `import-linter` (frontera de agencia P-3) + `pytest`/PBT (Build & Test).

## Checklist de diseño
- [ ] **Topología de contenedores** — qué corre dónde (app, Postgres, RAG de muestra).
- [ ] **El RAG de muestra como sistema externo** — cómo se despliega dado que es "paciente" tras adaptador (in-process vs. contenedor aparte).
- [ ] **Config/secrets** — `.env` no versionado; variables (DB URL, LLM key).
- [ ] **Migraciones** — cuándo corren (arranque vs. manual).
- [ ] **CI mínima** — qué corre en el pipeline de U1.
- [ ] **Diagrama de despliegue** — texto/mermaid, mínimo.
- [ ] **No-metas** — enumerar lo enterprise diferido, sin fingir.

## Justificación de "mínimo" (framework)
- Sin IaC, sin orquestador (K8s), sin LB, sin multi-AZ, sin cola gestionada. Todo = fase endurecer (arquitectura Seg 2). Se documenta como roadmap, no se implementa.

---

## Preguntas de clarificación (rellenar `[Answer]:`)

### Q1 ⭐ — Despliegue del RAG de muestra (el "paciente")
El RAG es un sistema externo tras `RagPatientPort`. En el skeleton, ¿cómo corre?
- (A) **In-process, tras el adaptador** (una impl. Python del RAG dentro del mismo proceso, pero aislada por el puerto). Más simple; la costura P5 se respeta por interfaz, no por red.
- (B) **Contenedor aparte** en docker-compose (RAG con su propia API HTTP; el adaptador habla por red). Más fiel a "sistema externo"; más piezas.
- (C) Otro.
[Answer]: ✅ **(A) In-process, tras el adaptador.** Impl. Python del RAG en el mismo proceso, aislada por `RagPatientPort`. La costura P5 se respeta por interfaz; la red no entra al contrato en U1. `docker-compose`: `app` (incluye RAG in-process) + `db`.

### Q2 ⭐ — Cuándo corren las migraciones (Alembic)
- (A) **Automático al arranque** de la app (entrypoint corre `alembic upgrade head`). Cero fricción para la demo.
- (B) **Comando explícito** (`ratchet db migrate` / `make migrate`) antes de arrancar. Más control; un paso manual.
- (C) Otro.
[Answer]: ✅ **(A) Automático al arranque.** El entrypoint corre `alembic upgrade head` al iniciar. Cero fricción para la demo; en U1 hay una sola instancia ⇒ sin carrera de migración.

### Q3 — Alcance de la CI para U1 (default confirmable)
¿Qué corre el pipeline?
[Answer]: ✅ GitHub Actions: `ruff` (lint/format) + `import-linter` (frontera G2) + `pytest` (unit + PBT contra fake in-memory) + `pytest` integración/e2e (contra Postgres de servicio en CI). Sin deploy automatizado en U1.

### Q4 — Contenedores en docker-compose (default confirmable)
[Answer]: ✅ `app` (FastAPI+CLI, con RAG de muestra in-process) + `db` (Postgres 16). Sin Redis/worker (síncrono in-process).

---

## Salidas al aprobar
- `aidlc-docs/construction/u1-camino-niif/infrastructure-design/infrastructure-design.md`
- `aidlc-docs/construction/u1-camino-niif/infrastructure-design/deployment-architecture.md`
