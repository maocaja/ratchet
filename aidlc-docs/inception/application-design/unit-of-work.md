# Units of Work — Ratchet

> Decisiones: Q1=A (vertical, walking-skeleton primero) · Q2=A (3 unidades) · Q3=A (monolito modular, un desplegable) · Q4=A (`src/ratchet/<módulo>/`).
> Unidades de **desarrollo** (no de despliegue). Orden de construcción: **U1 → U2 → U3**.

> **⚠️ Reconciliación v2 (2026-07-06) — leer primero.** Tras el pivote agéntico (`docs/definicion.md` v2), las unidades se **re-scopearon** (decisión deliberada, registrada en `audit.md`; no se reabre Inception). **Lo de abajo es el registro histórico de Inception (v1); para U2+ manda este re-scope:**
>
> | Unidad | Propósito único (v2) | Estado |
> |---|---|---|
> | **U1** | Sustrato determinista (Camino NIIF) | ✅ completo — intacto |
> | **U2** | **Investigador Agéntico:** contradictorios + loop de razonamiento + RAG externo propio (ADR-008) + eval del agente + *definir* política de autonomía | **siguiente** |
> | **U3** | Credibilidad: 2º paciente (AnythingLLM) + faithfulness + robustez | diferido |
> | **U4 / backlog** | Rama config + Experimenter + *demostrar* auto-config | diferido **explícito** |
>
> **Motivo:** el viejo *"U2 · Rama Config"* (abajo) no demostraba agencia; el Investigador Agéntico ocupa U2 (regla 1-propósito). El viejo U2 (config) **baja a U4/backlog** (no se entierra en U3). `unit-of-work-story-map.md` y `-dependency.md` quedan como **registro histórico v1** (superseded para U2+ por esta nota). Las historias de U2 son **nuevas** → se generan en Requirements de U2, no acá.

## U1 · Camino NIIF (walking skeleton) — Must 🎯
- **Objetivo:** rebanada vertical **end-to-end de la rama de datos** — el entregable no-negociable (Q7).
- **Alcance:** conectar adaptador (ops de datos), golden set ≥50 con span, baseline, evaluación (recall-por-span), monitor que detecta la caída, investigador que localiza "fuente-vieja" + writeup, parche con confirmación humana, aplicar+reindex, gate con revert, aprobación humana, reporte antes/después.
- **Historias:** US-01, US-05, US-06a, US-07, US-08, US-10, US-11, US-13, US-03, US-14, US-16, US-17. *(recall-por-span solamente; faithfulness = US-06b en U3)*
- **Componentes tocados (versión delgada):** C1 (datos), C2, C3 (recall), C4, C6, C7, C8 (+ ApprovalService), C9, C10, C12.
- **Criterio de "hecho":** el `Scenario` NIIF de `stories.md` corre end-to-end; gate revierte si empeora; reporte reproducible.

## U2 · Rama Config + Experimentación — Must
- **Objetivo:** completar la tesis con la rama de **config** (variantes dirigidas + gate).
- **Alcance:** ops de config del adaptador; Experimenter propone variantes dirigidas por el diagnóstico; corre experimentos vía Evaluator; reusa el **Gate/Orchestrator de U1**.
- **Historias:** US-02, US-12.
- **Componentes:** C1 (config), C5 (nuevo), + reuso C3/C6/C9.
- **Criterio de "hecho":** demo config recall 0.70→0.88 vía gate; caza una degradación introducida.

## U3 · Credibilidad + Robustez — Must/Should
- **Objetivo:** matar el "paciente amañado" y endurecer el loop.
- **Alcance:** 2º paciente open-source real + fallback (G1/supports_data_ops); **faithfulness (LLM-judge, métrica secundaria — endurecer)**; clasificar deriva vs. deploy propio; revert asimétrico; política de autonomía.
- **Historias:** US-04 (Must), US-06b (Must, post-skeleton: faithfulness), US-09 (Should), US-15 (Should), US-18 (Should).
- **Componentes:** AdapterRegistry (2ª impl. de C1), C3 (faithfulness), C7 (clasificación), C6 (revert asimétrico), C8/política.
- **Criterio de "hecho":** mejora demostrada sobre un RAG que Ratchet no construyó (o fallback documentado).

## Estrategia de organización de código (greenfield, Q4=A)
```text
ratchet/
├── src/ratchet/
│   ├── adapter/          # C1 RagPatientPort + impls (propio, oss)
│   ├── registry/         # C2 GoldenSetRegistry
│   ├── evaluator/        # C3 recall-por-span + faithfulness
│   ├── investigator/     # C4 ProbeToolkit + Localizer
│   ├── experimenter/     # C5
│   ├── gate/             # C6 (determinista)
│   ├── monitor/          # C7
│   ├── reporter/         # C8 + ApprovalService
│   ├── orchestrator/     # C9 LoopOrchestrator (sin LLM — G2)
│   ├── api/              # C10 FastAPI + CLI
│   ├── persistence/      # C12 repos + migraciones
│   └── domain/           # tipos: EvalResult, Diagnosis, GateVerdict, ...
├── tests/                # unit + PBT (núcleo) + e2e (escenario NIIF)
├── docker-compose.yml    # app + PostgreSQL (+ worker)
└── pyproject.toml
```
- **Un solo desplegable** (monolito modular); los módulos son paquetes internos con fronteras claras (costuras para separar en servicios después).
- **Fronteras de agencia por diseño:** `gate/` y `orchestrator/` no importan el cliente LLM; `investigator/` y `experimenter/` sí (río arriba).
