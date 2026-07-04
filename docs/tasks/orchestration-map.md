# Mapa de orquestación — U1 · Camino NIIF (E7, paso 1)

> El sistema de orquestación antes de ejecutar comandos. Define qué entra al flujo, qué lee el agente, qué puede cambiar, qué bloquea qué, quién ejecuta, qué valida y qué se recuerda.

| Dimensión | Definición para U1 |
|---|---|
| **Intención** | Implementar el walking skeleton de U1 (rama de datos, escenario NIIF) end-to-end, hasta el demo CLI + reporte HTML. |
| **Contexto** (qué lee el agente) | `AGENTS.md`, `.claude/rules/`, `aidlc-docs/construction/u1-camino-niif/**` (functional-design, nfr-*, infrastructure-design), `docs/adr/`, el task file. Fuente de verdad de reglas = `.claude/rules/`; de la clave de estado = `nfr-design-patterns.md §P-1`. |
| **Scope** | Puede cambiar: `src/ratchet/**`, `tests/**`, `pyproject.toml`, `docker-compose.yml`, `.github/workflows/`. **Reservado (no tocar sin permiso):** specs de `aidlc-docs/`, `docs/adr/`, la composición de la clave de estado (§P-1). |
| **Dependencias** | DAG explícito en el frontmatter (`blockedBy`/`blocks`) de cada task. Wave 1 = TASK-001 (sin blockers). |
| **Ejecución** | Arnés: Claude Code (portable a otros vía `AGENTS.md`). Una tarea = una sesión ejecutable. Bucle **test-alongside**: `test-writer` cubre + `code-reviewer` aprueba. |
| **Validación** (bloquea avance) | `ruff` · `import-linter` (G2) · `pytest` (unit/PBT + e2e NIIF hermético). Acceptance criteria del task file. **El e2e NIIF no requiere `ANTHROPIC_API_KEY`.** |
| **Review** (antes del merge) | `code-reviewer` (guardrails G1/G2/G3, recall=código/faithfulness=juez, anti-agentwashing) como capa advisory; **aprobación humana = gate de merge**. |
| **Memoria** (aprendizaje reusable) | Cada task completada actualiza `audit.md` (decisiones), y los ADRs si aparece una decisión no reversible. Invariants del núcleo → `.claude/rules/`. |

## Dependencias (DAG)
```text
000 (DATOS, humano) ──────────────▶ 006, 007      ← ruta crítica, corre en paralelo con M1

001 ─▶ 002 ─┬▶ 003 ─┬▶ 004 ─────────────┐
            │       ├▶ 005 ─▶ 006 ──┐    │
            │       └▶ 009 ◀────────┘    │
            ├▶ 007 ─▶ 008 ───────────────┤
            └▶ 010 ◀──────────(004)──────┤
                                          ▼
   004,005,006,007,008,009,010 ─▶ 011 ─▶ 012 ─▶ 013
```
- **TASK-000 (datos)** no tiene dependencia de código → arranca **ya**, en paralelo con M1. Bloquea 006 (golden set) y 007 (corpus). Owner = **humano**, no delegable a un agente.
- **Wave 1:** 001. **Wave 2:** 002. **Wave 3:** 003, 007 (007 requiere 000). Luego 004/005/010 y 008, etc.
- 011 (orchestrator) es el punto de convergencia; 012/013 son superficie/demo.
- **Riesgo #1 de la fecha:** si TASK-000 no arranca ya, el demo no corre aunque el código esté 100%.

## Señales trazables (para coordinar agentes)
- Estado por tarea (Todo → In Progress → Human Review → Done) en el tablero.
- PR por tarea con **Evidence** (comandos corridos + output + tests).
- Acceptance criteria verificables por comando.
- Guardrails G1/G2/G3 verificables mecánicamente (import-linter + tests).
