# Crítica (stub — requiere análisis adversarial)

> Auto-crítica honesta del proyecto. Completar. Marcar dudas como `TBD`.

## Riesgos / objeciones conocidas
1. **Espacio de tooling poblado** (LangSmith et al.) → mitigación: es PORTAFOLIO, la competencia prueba que la skill está en demanda; el diferencial es el loop de auto-mejora completo.
2. **"¿Un chat no hace esto?"** → No: requiere pipeline + estado + experimentación + evaluación repetible sobre datos reales. El LLM es un componente reemplazable.
3. **Riesgo de scope** (querer construir toda la plataforma) → mitigación: MVP = el loop sobre UNA dimensión (retrieval), un corpus.
4. **Cold-start de datos** → resuelto: corpus público (NIIF/NIA) + RAG de muestra construido por Mauricio; acceso total.
5. **Validez de la "auto-mejora"** → la seguridad de revert (nunca empeorar) es clave para que sea creíble. TBD: definir criterio de decisión.

## Preguntas abiertas
- ¿Cuál es el criterio exacto de "deploy vs revert" (métrica + umbral + tradeoff costo/latencia)?
- ¿Qué tan realista es el golden set contable? TBD.

## Auditoría de panel de expertos (2026-07-02)
5 expertos (RAG/evals, arquitectura agéntica, MLOps/data-centric, producto, escéptico) auditaron el proyecto. Ataques principales y respuestas:

1. **Paciente amañado (circularidad):** Mauricio construye el RAG *y* calibra el bug que una perilla arregla → la demo prueba la plomería, no la tesis. → **Fix: segundo paciente real (RAG open-source de terceros).**
2. **N=15 sin poder estadístico:** recall se mueve en escalones de ~0.067; "0 regresiones" es promesa sobre ruido. → **Fix: golden set ≥50 + significancia (bootstrap CI / McNemar).**
3. **Bug de medición (silencioso):** `recall@k` no es comparable entre chunkings (cambia la unidad). → **Fix: medir por span de fuente.**
4. **Trinquete tautológico + claim inflado:** no puedes empeorar en la métrica que optimizas; la deriva real vive fuera del golden set. → **Fix: angostar el claim** a "previene regresiones y diagnostica la causa", no "nada se degrada en silencio".
5. **Deriva del juez:** el LLM-judge se valida una vez; self-preference si generador y juez son el mismo modelo. → re-validar el juez en eventos de deriva; anclar decisión en recall.

**Única mejora agéntica que vale (unánime):** diagnóstico causal ligero (el modelo agrupa fallas por causa y dirige qué perilla probar). Promovido al MVP (CU-4 core).

**Anti-agentwashing — lo que NO hacemos, a propósito** (saber cuándo NO usar agentes = señal senior):
- ❌ Multi-agente / debate de agentes (teatro + no-determinismo).
- ❌ Planificador sofisticado (Bayesian/bandit) — el espacio es chico; el diagnóstico que poda el barrido basta.
- ❌ Deploy sin humano (contradice P2; pasivo en dominio regulado).
- ❌ Curación autónoma del golden set (uróboros: el LLM escribe, juzga y elige → sin verdad externa). Solo drafting human-in-the-loop.

**Regla rectora:** *"el razonamiento propone, la matemática dispone"* — agencia en diagnosticar/planear; juez y gate en código determinista.

## Reencuadre del core (panel 2, 2026-07-02)
Un 2º panel encontró una **incoherencia de identidad**: el loop invocaba "Data-Centric AI" pero su única palanca era **config** (perillas de retrieval), y el escenario bandera (cambio de NIIF) **no lo puede arreglar** girando perillas — necesita un fix de **datos**. Además, el "corazón agéntico" (una sola clasificación LLM) era **decorativo** (un if/else lo replica).

**Reencuadre adoptado (opción A):** de *"afinador de config"* → **"SRE del conocimiento del RAG"**: un **investigador read-only** con herramientas recorre el lineage (documento→chunk→retrieve→genera), **localiza la capa del defecto**, escribe un **writeup de incidente**, y prescribe el fix en la capa correcta — **config** (loop gateado) o **datos** (parche propuesto → **humano confirma**). Esto hace al LLM *load-bearing* (agencia real), arregla la incoherencia, y da un demo memorable.
- **Principio afinado:** *"cuanto más lejos del gate, más agente; cuanto más cerca, más determinista"* — el verificador fuerte **permite** soltar al proponente.
- **Roadmap (no MVP):** curación autónoma de datos, memoria que compone (con pocos ciclos = sobreajuste), pipeline completo con OCR, espacio de acciones amplio.
- **Alcance día 11:** investigador + localización + writeup + rama config (buildable, seguro) + palanca de datos **delgada** (reemplazar doc viejo → re-index). La curación rica = después.

## Escenario de borde: versiones contradictorias que conviven en el corpus (2026-07-03)
**Pregunta que lo destapa:** se sube un documento A; después se sube B porque la política cambió, pero A **no se borra** y contradice a B. La búsqueda puede traer los dos trozos → el asistente responde **inconsistente** (a veces A, a veces B, a veces mezclado). ¿Qué pasa?

**Clasificación:** es una falla de **datos** (higiene/vigencia del corpus), misma familia que el escenario NIIF pero en su variante difícil: el viejo sigue vivo compitiendo con el nuevo. Ninguna perilla de config lo arregla.

**Quién decide cuál es la verdad (principio load-bearing):** **NO Ratchet, NO la IA — el golden set** (verdad mantenida por un humano). La cadena: la política cambia → un humano actualiza el golden set (la respuesta correcta ahora es la de B) → el asistente sigue respondiendo por A → **recall cae** → el investigador localiza el modo de falla *"fuente vieja A contradice el span dorado vigente B, ambas indexadas"* → propone retirar/expirar A → **humano confirma** → re-index → recall recupera. Ratchet **enforcea coincidir con la verdad vigente, no la inventa** — deliberado: dejar que la IA decida qué norma aplica sería un pasivo en dominio regulado.

**Matiz — no siempre es contradicción, a veces es verdad condicional:** A y B pueden ser **ambos correctos bajo condiciones distintas** (ej. "para el ejercicio 2023 aplica A; desde 2025, B"). Ahí el fix NO es borrar A sino **metadatos de vigencia (desde/hasta) + retrieval temporal** que filtra según el contexto (año) de la pregunta. Es exactamente lo que un sistema tipo Caseware debe hacer bien.

**Límite honesto:** este escenario aterriza en el **SPOF #1** (golden set/baseline) — si el examen no se mantiene al día, Ratchet queda ciego a que B es la nueva verdad.

**Alcance:**
- **MVP:** versión delgada — detectar la fuente reemplazada → sustituir/re-index. Un solo dueño de la verdad, sin fechas de vigencia.
- **Roadmap:** corpus versionado con metadatos de vigencia + retrieval temporal (la variante "ambos válidos según la fecha").
