# AGENTS.md — Ratchet

> Manual operativo **portable** para cualquier arnés agencial (Claude Code, Codex, OpenHands, Factory, Cursor…). Complementa `CLAUDE.md` (específico de Claude Code) — no lo reemplaza. Si tu arnés lee `CLAUDE.md`, úsalo; si lee `AGENTS.md`, este es el equivalente.

## Propósito del repo
**Ratchet** = el *SRE de guardia del conocimiento de un RAG*: cuando la confiabilidad cae, un investigador read-only recorre el lineage (documento→chunk→retrieve→genera), **localiza en qué capa está el defecto (datos o config)**, lo diagnostica y lo arregla en la capa correcta — config solo si un gate determinista confirma que no empeora; datos solo con confirmación humana. Loop: *deploy → observe → evaluate → improve → deploy*. Estrella polar: `docs/definicion.md`.

## Stack y comandos
- **Lenguaje:** Python 3.12+ · **Deps:** `uv` (versiones fijadas) · **Lint/formato:** `ruff` · **Tests:** `pytest` + `hypothesis` (PBT) · **Frontera de agencia:** `import-linter`.
- **Backend:** FastAPI (API) + Typer (CLI) · PostgreSQL 16 + SQLAlchemy 2 + Alembic · Job Runner síncrono in-process.
- **Comandos** *(cuando exista código — hoy `src/` está vacío; ver estado más abajo):*
  ```
  uv sync                       # instalar deps
  ruff check . && ruff format --check .
  lint-imports                  # contrato G2 (gate/orchestrator sin LLM)
  pytest tests/unit             # núcleo determinista + PBT (fake in-memory)
  pytest tests/integration tests/e2e   # contra Postgres (escenario NIIF, hermético)
  ```

## Dónde vive qué
| Qué | Dónde |
|---|---|
| Estrella polar / visión | `docs/definicion.md`, `docs/pvb.md` |
| Specs del curso (PRD, arquitectura C4/NFR) | `specs/` |
| **Specs AI-DLC (Inception + Construction)** | `aidlc-docs/` (índice: `aidlc-docs/inception/README.md`) |
| Estado del pipeline | `aidlc-docs/aidlc-state.md` |
| Decisiones arquitectónicas | `docs/adr/` (7 ADRs) |
| **Código de aplicación** | `src/ratchet/<módulo>/` *(aún NO scaffoldeado)* |
| Tests | `tests/` (unit · integration · e2e) |
| Reglas de dominio para el agente | `.claude/rules/` (`evaluacion`, `python`, `testing`) |

## Reglas de edición (no negociables)
> **Fuente canónica del detalle** (dueño único): `.claude/rules/evaluacion.md` (regla de oro + gate + localizador), `.claude/rules/python.md` (guardrails G1/G2/G3, costuras), `.claude/rules/testing.md` (PBT, regresiones). Son Markdown portable — cualquier arnés los lee. Lo de abajo es **resumen operativo**, no la especificación; ante duda o cambio de matiz, manda `.claude/rules/`.
- **Código en la raíz (`src/`); documentación en `aidlc-docs/`.** Nunca mezclar.
- **Regla de oro** *(detalle: `evaluacion.md`)*: `recall` = código determinista; `faithfulness` = LLM-juez. Nunca al revés.
- **Guardrails** *(detalle: `python.md`)*: **G1** data-ops capability-flagged · **G2** gate/orquestador **NO** llaman al LLM (enforced por `import-linter`) · **G3** investigador read-only con claim verificable.
- **Simplicidad sobre complejidad** (monolito modular con costuras, no microservicios).
- El LLM vive en `investigator/` (y `experimenter/` en U2+), nunca en `gate/`/`orchestrator/`.

## Comandos obligatorios antes de entregar
**Gates requeridos** (aplican **cuando exista código** — desde CG-0; hoy `src/` está vacío y aún no corren): `ruff check` · `lint-imports` (G2) · `pytest` (unit/PBT + e2e NIIF). El **e2e NIIF corre sin `ANTHROPIC_API_KEY`** (camino determinista/hermético).

## Cómo reportar evidencia
Reportar siempre con salida real: si un test falla, mostrarlo; si un paso se saltó, decirlo. Una corrida produce un **reporte antes/después reproducible** (`GET /runs/{id}/report`). No afirmar "hecho" sin la validación que lo respalda.

## Áreas que requieren permiso / cuidado explícito
- **Clave de estado / idempotencia:** dueño único = `aidlc-docs/construction/u1-camino-niif/nfr-design/nfr-design-patterns.md §P-1`. No re-deletrear la tupla en otros docs (ver ADR-005 / erratum).
- **`gate/` y `orchestrator/`:** no introducir imports ni inyección del cliente LLM (rompe G2; el build falla).
- **Golden set:** es la verdad humana, NO recomputable — se siembra desde fuente versionada (CG-4).

## Subagentes y automatización disponibles
- **Subagentes** (`.claude/agents/`): `test-writer` (pytest+PBT, regresiones inyectadas), `code-reviewer` (guardrails G1/G2/G3, anti-agentwashing), `spec-reviewer` (contradicciones/TBDs en specs).
- **Skill** (`.claude/skills/`): `review-specs`.
- **Hooks** (`.claude/hooks/`): `guard-bash` (PreToolUse), `post-edit`.

## Producto / diseño visual
- **`PRODUCT.md`:** la memoria de producto (audiencia, propósito, tono) vive en `docs/definicion.md` + `docs/pvb.md`.
- **`DESIGN.md`:** N/A — Ratchet MVP es API + CLI, **sin interfaz visual**.

## Estado actual
CONSTRUCTION · U1 (Camino NIIF): **specs completas** (Functional · NFR · Infra, conformes al runbook AI-DLC). **Code Generation en pausa.** Al implementar, empezar por **CG-0** (scaffold + import-linter fail-closed) y el bucle test-alongside desde el núcleo determinista (`aidlc-docs/construction/plans/u1-camino-niif-code-generation-plan.md`). Carry-overs: CG-1 (retry solo reads) · CG-2 (test no-inyección LlmPort) · CG-3 (RAG stubbea generate()) · CG-4 (golden set sembrado desde repo).
