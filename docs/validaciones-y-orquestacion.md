# Validaciones y orquestación — Ratchet

> Estación 6, checklist ítem 4 + runbook §6. Qué validaciones existen, qué evidencia produce cada una, cuál **bloquea entrega**, y cómo se orquestará la implementación (puente a Estación 7).

## Validaciones disponibles

| Validación | Qué verifica | Evidencia | ¿Bloquea entrega? |
|---|---|---|---|
| `ruff check` + `ruff format --check` | Lint y formato | Salida ruff (0 errores) | ✅ Sí |
| `lint-imports` (import-linter) | **Frontera de agencia G2**: `gate/`/`orchestrator/` sin cliente LLM | Build falla si se viola | ✅ Sí (fail-closed desde CG-0) |
| `pytest tests/unit` (+ `hypothesis`) | Núcleo determinista: recall-por-span, gate, localizador; **regresiones inyectadas** | Reporte pytest; recall **recomputado**, no "creído" | ✅ Sí |
| `pytest tests/integration tests/e2e` | Escenario NIIF end-to-end contra Postgres real | Reporte e2e — **hermético** (sin `ANTHROPIC_API_KEY`, sin red) | ✅ Sí |
| Subagente `test-writer` | Genera tests (happy/error/edge, PBT, factories, regresión inyectada) | Tests nuevos con cobertura | 🟡 Cierre de módulo |
| Subagente `code-reviewer` | Guardrails G1/G2/G3, recall=código/faithfulness=juez, anti-agentwashing | Findings por severidad | 🟡 Cierre de módulo |
| Subagente `spec-reviewer` | Contradicciones/sobre-afirmaciones/TBDs en specs | Findings | 🟡 Antes de cerrar un spec |
| Hook `guard-bash` (PreToolUse) | Intercepta comandos bash sensibles | Feedback al agente | ✅ Preventivo |
| Hook `post-edit` | Chequeo tras editar | Feedback al agente | 🟡 Preventivo |

**Regla:** un módulo se cierra solo cuando `test-writer` lo cubre **y** `code-reviewer` lo aprueba **y** `ruff`/`import-linter`/`pytest` están verdes (bucle **test-alongside**, ver `aidlc-docs/construction/plans/u1-camino-niif-code-generation-plan.md`).

## Nota de orquestación (puente a Estación 7)

La orquestación aparece cuando se coordina más que una conversación. Para la implementación de Ratchet:

| Pregunta (runbook §6) | Respuesta para Ratchet |
|---|---|
| **1. Qué arnés** | Claude Code (ver `docs/harness-ficha.md`); portable a otros vía `AGENTS.md`. |
| **2. Qué lee el agente** | `AGENTS.md`/`CLAUDE.md`, `.claude/rules/`, las specs de `aidlc-docs/construction/u1-camino-niif/`, los ADRs. |
| **3. Qué permisos** | Editar `src/`, correr tests/lint; confirmación humana para acciones externas y para los dos gates de dominio (US-13/US-16). |
| **4. Qué validación bloquea** | `import-linter` (G2), `pytest` (unit/PBT + e2e NIIF), `ruff`. Ninguna entrega sin ellas verdes. |
| **5. Qué evidencia devuelve** | Reporte antes/después reproducible + salida de la suite + findings de `code-reviewer`. |
| **6. Qué estudiar para orquestación posterior** | Convertir el bucle test-alongside en un **workflow multi-agente** (fan-out por módulo, verify adversarial) — E7. |

### Forma de orquestación ya diseñada
El **bucle test-alongside por módulo** (generar → `test-writer` cubre → `code-reviewer` aprueba → CI verde) es orquestación embrionaria: coordina 3 agentes con una validación que bloquea el avance. En E7 se formaliza como pipeline (un módulo por etapa, verificación adversarial antes de cerrar). El orden de construcción (núcleo determinista primero, libre-de-LLM) ya está fijado.
