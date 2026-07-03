# Componentes — Ratchet

> Nivel: identificación de componentes, responsabilidades e interfaces. La lógica de negocio detallada va en Functional Design (per-unit).
> Traza: arquitectura.md Seg 2 (módulos M1-M7) → componente → FR.
> **Principio rector:** agencia (LLM) río arriba del gate; ruteo y gate deterministas río abajo. Guardrails **G1/G2/G3** aplicados.

## Mapa de componentes

| # | Componente | Módulo | Responsabilidad (una línea) | FR |
|---|---|---|---|---|
| C1 | **RagAdapter** | M1 | Implementa `RagPatientPort`: aplica/revierte **config** y (opcional) **parches de datos + re-index** sobre el RAG externo | FR-1, FR-11 |
| C2 | **GoldenSetRegistry** | M2 | Versiona golden set (span de fuente), baseline, historial y decisiones (respaldado en PostgreSQL) | FR-2 |
| C3 | **Evaluator** | M3 | Calcula **recall-por-span** (determinista) y **faithfulness** (LLM-judge); ancla la decisión en la métrica determinista | FR-3 |
| C4 | **Investigator** | M4 | `ProbeToolkit` (sondas deterministas del lineage) + `Localizer` (LLM delgado) → **claim verificable** de la capa + writeup (read-only) | FR-5 |
| C5 | **Experimenter** | (Exp) | Propone variantes de config **dirigidas** (LLM río arriba) y las corre contra el golden set vía Evaluator | FR-6 |
| C6 | **Gate** | M5 | Gate de no-regresión **determinista** + revert-safety asimétrico; decide deploy/revert para ambas ramas | FR-8 |
| C7 | **Monitor** | M6 | Detecta caídas vs. baseline, dispara el loop, clasifica origen (deploy propio vs. deriva) | FR-4 |
| C8 | **Reporter** | M7 | Writeup de incidente + reporte antes/después; gestiona el gate humano (aprobación/rechazo) | FR-9 |
| C9 | **LoopOrchestrator** | (svc) | Control de flujo **determinista** del loop medir→localizar→arreglar→gate→reportar. **No llama al LLM (G2)** | (orquesta) |
| C10 | **ApiCli** | API/CLI | Superficie FastAPI + CLI: disparar, ver reportes, aprobar | FR-10 |
| C11 | **JobRunner** | Worker | Ejecuta experimentos/corridas (skeleton: síncrono in-process; endurecer: cola real) | (soporte) |
| C12 | **Persistence** | (DB) | Acceso a PostgreSQL (repos, migraciones, idempotencia) | NFR-2 |

## Detalle por componente

### C1 · RagAdapter  *(implementa `RagPatientPort`)*
- **Interfaz (puerto hexagonal, P5):** `RagPatientPort` — una interfaz, implementaciones intercambiables por paciente (propio, open-source).
- **Capacidades:** `retrieve/generate` (lectura del lineage); **config**: `get_config / apply_config / revert_config`; **datos (G1: capability-flagged)**: `supports_data_ops()`, `apply_data_patch / revert_data_patch / reindex`.
- **G1:** si `supports_data_ops()` es falso (p. ej. 2º paciente sin re-index limpio), la rama de datos se marca no-disponible para ese paciente y aplica el fallback (Q1) — **no rompe P5**.

### C2 · GoldenSetRegistry
- **Responsabilidad:** CRUD versionado del golden set (ítem = {pregunta, respuesta, **span de fuente**}), baseline, historial de corridas, decisiones y writeups.
- **Invariante:** rechaza fijar baseline con golden set < 50 (barra de significancia). Todo versionado e inmutable por versión (recomputable, NFR-2).

### C3 · Evaluator
- **Responsabilidad:** dado (golden set vN, RAG/config), computar `recall_por_span` (determinista) + `faithfulness` (LLM-judge, secundaria).
- **Regla de frontera:** la **decisión** se ancla en recall determinista; faithfulness es señal, no juez de la decisión (mitiga SPOF del juez).

### C4 · Investigator  *(corazón agéntico, read-only)*
- **`ProbeToolkit` (determinista):** `span_en_topk?`, `span_indexado?`, `fronteras_de_chunk`, `span_vigente_en_corpus?`, `respuesta_usa_span?`.
- **`Localizer` (LLM delgado):** consume resultados de sondas → emite **claim verificable** `{capa ∈ {retrieval-miss, chunking, fuente-vieja, cobertura, generación}, evidencia: [probe_ids]}` + writeup.
- **G3:** la salida es un **claim re-verificable**, no una acción ni texto libre; read-only (CU-4); el writeup se desacopla de cualquier cambio.

### C5 · Experimenter
- **Responsabilidad:** ante prescripción "config", proponer variantes **dirigidas** por el diagnóstico (LLM propone candidatos río arriba) y correrlas vía Evaluator; entregar resultados estructurados al Gate.
- **G3 (variante):** el LLM **propone** perillas candidatas; el experimento + gate **disponen**.

### C6 · Gate  *(determinista)*
- **Responsabilidad:** comparar variante/parche vs. baseline sobre la métrica anclada; aprobar solo si no empeora (con CI que excluya ruido); **revert automático** si empeora. Revert-safety asimétrico (deploy propio → revert; deriva → re-experimentar).
- **Sin LLM.** Es "la matemática dispone".

### C7 · Monitor
- **Responsabilidad:** correr evaluaciones periódicas, detectar caída vs. baseline por umbral, disparar el loop; clasificar origen (deploy propio vs. deriva del entorno).

### C8 · Reporter
- **Responsabilidad:** ensamblar writeup + reporte antes/después (reproducible); orquestar el **gate humano** (P2): presentar propuesta, registrar aprobación/rechazo; si no hay aprobador, mantiene baseline.

### C9 · LoopOrchestrator  *(servicio)*
- **Responsabilidad:** secuencia determinista: Monitor→Investigator→(Experimenter|DataPatch)→Gate→Reporter→(deploy/revert). Rutea **solo sobre datos deterministas** (scores, veredicto del gate, claim ya verificado).
- **G2:** **no contiene `LLM.call()`**. Toda agencia LLM vive en C4/C5 y le devuelve datos estructurados.

### C10 · ApiCli / C11 · JobRunner / C12 · Persistence
- **ApiCli:** endpoints/comandos para disparar corridas, listar/leer reportes y **aprobar/rechazar** (FR-10).
- **JobRunner:** ejecuta corridas largas; skeleton síncrono in-process, endurecer a cola (RQ+Redis) después.
- **Persistence:** repositorios sobre PostgreSQL; migraciones versionadas; corridas idempotentes (NFR-2).
