# Plan de Application Design — Ratchet

> Identifica componentes, interfaces y capa de servicio (NO lógica de negocio detallada — eso es Functional Design).
> Insumos: `requirements.md`, `stories.md`, `arquitectura.md` (ya define módulos M1-M7).
> Responde las preguntas (letra tras `[Answer]:`) y dime "listo". Cada una tiene opción **Recomendada**.

## Preguntas de Diseño

### Question 1 — Frontera y organización de componentes
¿Cómo delimitamos los componentes?

A) **Un componente por módulo de la arquitectura** (M1 Adapter, M2 GoldenSet&Registry, M3 Evaluator, M4 Investigator/Localizer, M5 Decision/Gate, M6 Monitor, M7 Report) + API/CLI + JobRunner + Persistence — traza limpia arquitectura→componente **(Recomendada)**
B) Componentes más gruesos (agrupar en 3-4: Ingesta/Eval, Diagnóstico/Fix, Orquestación/UI)
C) Componentes más finos (separar cada sub-responsabilidad)
X) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 2 — Patrón del Adaptador al RAG (config + datos)
El adaptador debe aplicar/revertir **config** Y **parches de datos + re-index**. ¿Cómo lo estructuramos?

A) **Puerto hexagonal único `RagPatientPort`** con operaciones de config y de datos (una interfaz, implementaciones intercambiables por paciente) — agnóstico al modelo (P5), fácil de mockear/testear **(Recomendada)**
B) Dos adaptadores separados (ConfigAdapter + DataAdapter) — más granular, más piezas
C) Adaptador acoplado al paciente del demo (sin interfaz) — más rápido, rompe P5 y el 2º paciente
X) Other (please describe after [Answer]: tag below)

[Answer]: A  — con guardrail G1: las ops de DATOS del puerto son **capability-flagged/opcionales** (un paciente puede no soportar re-index limpio; empareja con el fallback de Q1 y el TBD "validar re-index")

### Question 3 — Patrón de orquestación del loop
¿Cómo se coordinan los módulos en el loop medir→localizar→arreglar→gate?

A) **Un servicio orquestador explícito `LoopOrchestrator`** con control de flujo determinista (llama a cada módulo en orden, decide ramas) — coherente con "cerca del gate = determinista"; fácil de auditar **(Recomendada)**
B) Coreografía por eventos (cada módulo reacciona a eventos) — desacoplado, pero flujo implícito y más difícil de auditar en 11 días
C) Orquestación dentro del JobRunner (sin servicio dedicado)
X) Other (please describe after [Answer]: tag below)

[Answer]: A  — con guardrail G2: el `LoopOrchestrator` **NO llama al LLM**; rutea solo sobre resultados deterministas (scores, veredicto del gate). Toda agencia LLM vive río arriba y le devuelve datos estructurados

### Question 4 — Estructura interna del Investigador/Localizador (M4)
Es el corazón agéntico. ¿Cómo separamos lo determinista de lo razonado?

A) **`ProbeToolkit` determinista** (sondas de lineage: ¿span en top-k?, ¿span indexado?, ¿fronteras de chunk?, ¿span vigente en corpus?) **+ `Localizer` (LLM) delgado** que decide la capa a partir de los resultados de las sondas y escribe el writeup — agencia acotada por herramientas verificables **(Recomendada)**
B) El LLM hace todo (recorre y decide sin sondas deterministas) — más "agente", menos verificable
C) Solo sondas deterministas + reglas if/else (sin LLM) — determinista total, pero pierde la agencia real (lo que el panel 2 quería evitar)
X) Other (please describe after [Answer]: tag below)

[Answer]: A  — con guardrail G3: la salida del `Localizer` es un **claim verificable** `{capa, evidencia: probe#N}` (no una acción ni texto libre), re-verificable por la capa determinista; read-only (CU-4); writeup separado de toda acción. Mismo patrón para la propuesta de variantes de config.

## Guardrails aprobados para Part 2 (blindan las decisiones, no las cambian)
- **G1 (Q2):** ops de datos del `RagPatientPort` = capability-flagged/opcionales → no rompe P5 para el 2º paciente sin re-index.
- **G2 (Q3):** el `LoopOrchestrator` no contiene `LLM.call()`; rutea solo sobre datos deterministas. Cualquier LLM en el control de flujo = violación.
- **G3 (Q4):** el `Localizer` (y el proponente de config) emiten claims/candidatos estructurados verificables; la matemática (experimento + gate) dispone. Read-only + writeup desacoplado de la acción.

## Plan de Ejecución (tras aprobación)
- [ ] `components.md` — componentes, propósito, responsabilidades, interfaces.
- [ ] `component-methods.md` — firmas de métodos (I/O), propósito de alto nivel (reglas detalladas → Functional Design).
- [ ] `services.md` — servicios (LoopOrchestrator + soporte), responsabilidades, orquestación.
- [ ] `component-dependency.md` — matriz de dependencias + patrones de comunicación + flujo de datos.
- [ ] `application-design.md` — consolidado.
- [ ] Validar completitud y consistencia (cobertura de FR/historias).
