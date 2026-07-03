# CLAUDE.md

Guía para Claude Code al trabajar en este repositorio.

## Qué es este workspace

Repo del proyecto **Ratchet** (nombre elegido 2026-07-02: un trinquete solo avanza, nunca retrocede = mejora o revierte, nunca empeora) — proyecto de Mauricio para el curso **Hardcore AI 30X (Cohorte 3)** **y** pieza de portafolio para roles **Senior AI Engineer / AI Data Engineer** (target: **Caseware** y similares). Demo Day: **lun 13 jul 2026**.

**Qué es el producto:** el **SRE de guardia del conocimiento de un RAG**. Cuando la confiabilidad cae, un **investigador read-only** recorre el lineage (documento→chunk→retrieve→genera), **localiza en qué capa está el defecto —datos o config—**, escribe el diagnóstico y lo arregla en la capa correcta: **config** solo si un gate determinista confirma que no empeora; **datos** solo si un humano confirma el parche. NO es "un agente que prueba agentes" (eso es solo medir); es un **sistema que MEJORA un asistente RAG**: medir + localizar + arreglar + re-evaluar. Loop tipo Ng: *deploy → observe → evaluate → improve → deploy*. Principio agéntico (panel 2): *"cuanto más lejos del gate, más agente; cuanto más cerca, más determinista"* — *"el razonamiento propone, la matemática dispone"*.

**Estrella polar / definición completa:** `docs/definicion.md` (léela primero).

## Contexto durable (memoria, no solo aquí)

Decisiones que cruzan sesiones viven en la memoria de Claude:
`/Users/mauricio/.claude/projects/-Users-mauricio-dev-hardcoreIA/memory/` (índice en `MEMORY.md`).
Bitácora de cómo se llegó a esta idea (evaluación de ~10 candidatos + 42 del showcase): `/Users/mauricio/dev/hardcoreIA/bitacora-ideas-proyecto.md`.

## Layout del repo (convención AI-DLC del curso)

| Path | Qué es |
|---|---|
| `docs/definicion.md` | Estrella polar: qué es, problema, insight, JTBD, qué validamos. Semilla del PRD. |
| `docs/pvb.md` | Product Vision Board (formato curso). TBD. |
| `docs/overview.md`, `docs/icp.md` | Insumos del PRD (formato curso). TBD. |
| `docs/mercado.md` | Insumo del PRD — aún delgado (tamaño de mercado, JDs y cita Gartner = `TBD`). |
| `docs/critica.md` | Auditoría de los dos paneles de expertos — sustancialmente completo. |
| `specs/prd.md` | **Salida** del Prompt 1 — ✅ **COMPLETO** (13 segmentos, 2026-07-02). |
| `specs/arquitectura.md` | **Salida** del Prompt 2 (AJIT + C4) — ✅ **COMPLETO** (4 segmentos, 2026-07-02). |
| `specs/backlog.md` | Salida del Prompt 3 — pendiente. |
| `aidlc-docs/` | **Estación 4 — Inception (aidlc-workflows) COMPLETA:** requirements, user-stories, application-design, units. `aidlc-state.md` = estado; siguiente fase = **Construction por unidad (U1 Camino NIIF)**. |
| `.aidlc-rule-details/` | Reglas de steering del framework AWS aidlc-workflows v0.1.8 (referencia). |

## Pipeline AI-DLC (cómo se construye)

Human-in-the-loop, **segmento por segmento** — nunca generar un artefacto entero de un tiro.

```
docs/ (definicion, pvb, overview, icp, mercado, critica)
  → Prompt 1 → specs/prd.md          (13 segmentos del curso) ✅
  → Prompt 2 → specs/arquitectura.md (AJIT — Architecture Just-in-Time + C4) ✅
  → Estación 4 → aidlc-docs/ (Inception: requirements, user-stories, application-design, units) ✅
  → Construction por unidad (U1 Camino NIIF → U2 → U3): código en src/ratchet/<módulo>/
```

Convenciones: Markdown sobre PDF; marcar lo desconocido como **`TBD`**, no inventar; una entrevista/dato = hipótesis, no verdad.

## Stack (ver `specs/arquitectura.md`) — código aún NO scaffoldeado

**MVP (lo que se construye en Construction):** monolito modular **Python**.
- **Backend:** **FastAPI** (API + CLI) + **PostgreSQL** (golden set, baseline, historial, decisiones) + **Job Runner async** (experimentos; skeleton síncrono/in-process, endurecer = cola real RQ+Redis).
- **AI/Data:** RAG de muestra sobre normas contables públicas (**NIIF/NIA**) como **sistema externo vía adaptador** (el vector store es del RAG, NO de Ratchet); LLM (Claude / AWS Bedrock) para juez (faithfulness) + generación del RAG. Regla de oro: recall = código determinista, faithfulness = LLM-judge, **nunca al revés**.
- **Regla #1 de arquitectura:** simplicidad sobre complejidad (monolito modular con costuras, no microservicios).

**Escalado enterprise (documentado, NO MVP — alineado a los JD de Caseware):** gateway **NestJS** (fast-follow, días 31-60) delante del core Python; cola → SQS/EventBridge; worker → Lambda/EKS; IaC (Terraform/CDK); observabilidad LangFuse. *Ojo: NestJS es el escalado, no el backend del MVP.*

Cuando se scaffoldee el código, actualizar este CLAUDE.md con comandos reales (build/test/lint) y arquitectura definitiva.
