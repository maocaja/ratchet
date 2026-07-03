# Application Design (Consolidado) — Ratchet

> Consolida `components.md`, `component-methods.md`, `services.md`, `component-dependency.md`.
> Decisiones: Q1=A (componente por módulo), Q2=A (`RagPatientPort` hexagonal), Q3=A (`LoopOrchestrator` determinista), Q4=A (`ProbeToolkit` + `Localizer` LLM delgado).
> Guardrails aprobados: **G1** datos capability-flagged · **G2** orquestador sin LLM · **G3** claims verificables, no acciones.

## 1. Visión de diseño
Monolito modular Python con **12 componentes** que calcan los módulos M1-M7 de la arquitectura + interfaz, worker y persistencia. La forma del sistema materializa un principio: **la agencia (LLM) vive río arriba del gate; el ruteo y el gate son código determinista.**

## 2. Componentes (resumen)
C1 RagAdapter · C2 GoldenSetRegistry · C3 Evaluator · C4 Investigator · C5 Experimenter · C6 Gate · C7 Monitor · C8 Reporter · C9 LoopOrchestrator · C10 ApiCli · C11 JobRunner · C12 Persistence. *(Detalle en `components.md`.)*

## 3. Interfaz clave: `RagPatientPort` (P5)
Puerto hexagonal único, implementaciones por paciente. Ops de **config** (siempre) + ops de **datos capability-flagged** (`supports_data_ops`, **G1**). Habilita el 2º paciente y su fallback sin romper P5.

## 4. Orquestación (determinista)
`LoopOrchestrator` ejecuta Monitor→Investigator→(Experimenter|DataPatch)→Gate→Reporter y rutea **solo sobre datos deterministas** (**G2**). Dos puntos de control humano (P2): confirmar parche de datos y aprobar deploy. *(Secuencia en `services.md`.)*

## 5. Fronteras de agencia (el diseño hecho restricción)
| Río arriba del gate — LLM permitido | Río abajo — solo determinista |
|---|---|
| `Localizer.localize`, `write_incident` (C4) | `verify_claim` (C4), `recall_por_span` (C3) |
| `Experimenter.propose_variants` (C5) | `Gate.*` (C6), routing de `LoopOrchestrator` (C9) |

**G3:** las salidas LLM son **claims/candidatos verificables** (`{capa, evidencia}` / lista de variantes), nunca acciones ni texto libre que dispare cambios.

## 6. Trazabilidad y cobertura
Todos los FR Must tienen componente dueño (ver `component-dependency.md` §Cobertura). El **Camino NIIF (héroe)** cruza C7→C9→C4→C8→C1→C6→C8→C2, con los dos gates humanos y el gate técnico intactos.

## 7. Diferido a Functional Design (per-unit)
Reglas de negocio detalladas: fórmula exacta de `recall_por_span` y del CI; umbral del gate; lógica precisa de poda de variantes; formato del writeup; esquema de datos concreto. *(Este documento fija QUÉ y las interfaces; el CÓMO detallado es Construction.)*
