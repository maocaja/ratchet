# Ficha de arnés y modelo — Ratchet

> Estación 6, checklist ítem 1. Caracteriza el arnés y modelo con que se ejecutará (y validará) la implementación de Ratchet. Los specs de AI-DLC son el **contrato de entrada**; esta ficha describe el **terreno operativo**.

## Arnés principal: Claude Code

| Característica | Cómo aplica a Ratchet |
|---|---|
| **Superficie** | CLI en terminal (local); también IDE (VS Code/JetBrains) y web. Repo-local. |
| **Modelo** | Claude (familia Opus/Sonnet/Haiku). Permite elegir modelo; *fast mode* disponible en Opus. El proveedor de inferencia (Anthropic API / AWS Bedrock) es intercambiable — coherente con `LlmPort` (P5). |
| **Contexto** | Lee todo el repo: `CLAUDE.md`/`AGENTS.md`, `.claude/rules/`, `aidlc-docs/`, `specs/`, `docs/adr/`. Ventana amplia (contexto extendido en Opus). |
| **Ejecución** | Edita archivos, corre comandos (bash), crea ramas/commits, usa subagentes en paralelo. |
| **Permisos** | Modo de permisos configurable (`.claude/settings.json`); hook `guard-bash` (PreToolUse) intercepta comandos sensibles; acciones externas/irreversibles piden confirmación. |
| **Validación** | Corre `ruff`, `import-linter`, `pytest`/PBT, e2e; subagentes `test-writer`/`code-reviewer`/`spec-reviewer` como segunda red. |
| **Evidencia** | Salida real de tests/lint; reporte antes/después reproducible; transcripción de tool calls auditable. |

## Portabilidad a otros arneses
Los mismos specs corren en **Codex, OpenHands, Factory, OpenCode, Cursor** vía `AGENTS.md` (manual operativo portable). Cambia el arnés, no el contrato: las specs de `aidlc-docs/` y las reglas de `.claude/rules/` son la fuente de verdad.

## Características de inferencia relevantes
> ⚠️ Las cifras exactas (ventana de contexto, precio por token, latencia) **cambian por versión de modelo** — no se hardcodean aquí. Consultar la **skill `claude-api`** (referencia de modelos/precios/límites Anthropic) y **Artificial Analysis** para valores vigentes. Abajo, qué mirar y por qué importa en Ratchet:

| Característica | Por qué importa en Ratchet |
|---|---|
| **Ventana de contexto** | Cargar specs + reglas + código en una sesión sin fragmentar. |
| **Cache de prompt** | El loop llama al juez (U3) repetidamente → cachear el prefijo baja costo/latencia. |
| **Tool calling** | Núcleo del arnés: leer/editar/correr. Calidad del tool-use = calidad del agente. |
| **Multimodalidad** | Poco relevante en U1 (sin imágenes); sí para diagramas/slides. |
| **Latencia** | El e2e NIIF es hermético (sin LLM) ⇒ rápido; la latencia solo pesa en el juez (U3). |
| **Costo operativo** | Acotado por diseño: el camino NIIF no llama al LLM; la política limita nº de variantes (U2). |
| **Calidad en código/razonamiento** | Determina cuánto revisar la salida; se valida siempre contra la evidencia (tests). |

## Benchmarks como señal (no verdad)
- **Terminal Bench** — capacidad del arnés en tareas de terminal reales.
- **Artificial Analysis** — comparación de modelos por costo/velocidad/calidad.
- Se leen como **señales parciales con margen de error** (mismo principio que el golden set de Ratchet: una medición ≠ verdad). Complementar con pruebas reales sobre este repo.
