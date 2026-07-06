# AI-DLC Audit Log — Ratchet

## Workflow Start
**Timestamp**: 2026-07-03T01:21:55Z
**User Input**: "ok, procede con la implemtacion de ai-dlc"
**AI Response**: Montó el framework AI-DLC v0.1.8 en `ratchet/` (`.aidlc-rule-details/` + `aidlc-docs/`). Ejecutó Workspace Detection.
**Context**: Estación 4 — arranque del pipeline AI-DLC Inception. Insumos: `specs/prd.md` y `specs/arquitectura.md` ya existentes.

---

## Workspace Detection
**Timestamp**: 2026-07-03T01:21:55Z
**AI Response**: Escaneo del workspace: sin código fuente ni build files → **Greenfield**. Reverse Engineering N/A. Siguiente fase: Requirements Analysis. Creó `aidlc-state.md`.
**Context**: INCEPTION - Workspace Detection (sin aprobación requerida, informativo).

---

## Requirements Analysis — Clarifying Questions
**Timestamp**: 2026-07-03T01:21:55Z
**AI Response**: Generó `inception/requirements/requirement-verification-questions.md` (8 preguntas + 2 opt-in de extensiones). Insumo principal: PRD ya existente. Profundidad: Comprehensive (dominio regulado, alto riesgo, pieza de portafolio). GATE: esperando respuestas del usuario.
**Context**: INCEPTION - Requirements Analysis - Step 6.

---

## Requirements Analysis — Respuestas y Generación
**Timestamp**: 2026-07-03T01:21:55Z
**User Input**: "listo, usé tus sugerencias" — (usuario refinó primero las preguntas: reencuadró Q1 a 'cuál 2º paciente + fallback', convirtió Q2/Q5/Q6/Q8 en confirmaciones). Respuestas: Q1=A, Q2=A, Q3=A (fallback B), Q4=A, Q5=A, Q6=A, Q7=A, Q8=A, Seguridad=B, PBT=B.
**AI Response**: Sin contradicciones detectadas. Registró extensiones (Security=No, PBT=Yes/Partial). Generó `inception/requirements/requirements.md` (11 FR, 6 NFR, escenarios, métricas, restricciones, out-of-scope). Actualizó estado. GATE: esperando aprobación.
**Context**: INCEPTION - Requirements Analysis - Steps 7-9.

---

## Requirements Analysis — Aprobación
**Timestamp**: 2026-07-03T01:21:55Z
**User Input**: "seguimos"
**AI Response**: Requirements aprobado. Marcó Requirements Analysis [x]. Procede a User Stories (Part 1 - Planning).
**Context**: INCEPTION - Requirements Analysis aprobada → User Stories.

---

## User Stories — Part 1 (Planning)
**Timestamp**: 2026-07-03T01:21:55Z
**AI Response**: Assessment = Execute (multi-persona, lógica compleja). Generó `plans/user-stories-assessment.md` y `plans/story-generation-plan.md` con 4 preguntas de planeación (breakdown, formato AC, granularidad, priorización). GATE: esperando respuestas + aprobación del plan.
**Context**: INCEPTION - User Stories - Steps 1-13.

---

## User Stories — Plan aprobado + Part 2 (Generación)
**Timestamp**: 2026-07-03T01:21:55Z
**User Input**: (respuestas de planeación) "1→D (Híbrido), 2→A (Gherkin + ejemplos con datos concretos en núcleo determinista), 3→A, 4→A" — con justificación de que el camino NIIF debe ser una épica-journey visible, no fragmentada en 5 épicas.
**AI Response**: Registró respuestas en el plan. Generó `user-stories/personas.md` (2 personas) y `user-stories/stories.md` (18 historias US-01..US-18 en 8 épicas por capacidad + Épica-Journey "Camino NIIF no-negociable", Gherkin con datos concretos en US-06/US-14, prioridades Must/Should + marca 🎯, matriz de trazabilidad FR→historia). GATE: esperando aprobación.
**Context**: INCEPTION - User Stories - Steps 15-20.

---

## User Stories — Aprobación
**Timestamp**: 2026-07-03T01:21:55Z
**User Input**: "apruebo"
**AI Response**: User Stories aprobado. Marcó [x]. Procede a Workflow Planning.
**Context**: INCEPTION - User Stories aprobada → Workflow Planning.

---

## Workflow Planning
**Timestamp**: 2026-07-03T01:21:55Z
**AI Response**: Riesgo=Medium (greenfield, alta exigencia de corrección). Generó `plans/execution-plan.md` con visualización Mermaid. Recomienda EXECUTE: Application Design, Units Generation, Functional Design, NFR Requirements (ligero), NFR Design, Infrastructure Design (mínimo), Code Generation, Build&Test. SKIP: Reverse Engineering. Estrategia walking-skeleton-first (unidad NIIF primero). GATE: esperando aprobación.
**Context**: INCEPTION - Workflow Planning - Steps 1-9.

---

## Workflow Planning — Aprobación
**Timestamp**: 2026-07-03T01:21:55Z
**User Input**: "si"
**AI Response**: Plan aprobado (incl. Infrastructure Design EXECUTE-mínimo). Marcó Workflow Planning [x]. Procede a Application Design.
**Context**: INCEPTION - Workflow Planning aprobada → Application Design.

---

## Application Design — Plan + Preguntas
**Timestamp**: 2026-07-03T01:21:55Z
**AI Response**: Generó `plans/application-design-plan.md` con 4 preguntas de diseño (frontera de componentes, patrón de adaptador config+datos, patrón de orquestación, estructura interna del Investigador). Insumo: arquitectura ya define M1-M7. GATE: esperando respuestas + aprobación.
**Context**: INCEPTION - Application Design - Steps 1-6.

---

## Application Design — Respuestas + Generación
**Timestamp**: 2026-07-03T01:21:55Z
**User Input**: "A en todas" (verificado contra arquitectura y principio panel 2) + 3 guardrails: G1 (ops de datos del puerto capability-flagged/opcionales), G2 (LoopOrchestrator no llama al LLM, rutea sobre datos deterministas), G3 (salida del Localizer/proponente = claim/candidato verificable, no acción; read-only; writeup desacoplado).
**AI Response**: Registró Q1-Q4=A + guardrails en el plan. Generó 5 artefactos en `application-design/`: components.md (12 componentes C1-C12), component-methods.md (firmas), services.md (LoopOrchestrator + soporte), component-dependency.md (matriz + flujo NIIF), application-design.md (consolidado). Guardrails G1/G2/G3 incrustados. GATE: esperando aprobación.
**Context**: INCEPTION - Application Design - Steps 8-12.

---

## Application Design — Aprobación
**Timestamp**: 2026-07-03T01:21:55Z
**User Input**: "si proceder"
**AI Response**: Application Design aprobado. Marcó [x]. Procede a Units Generation.
**Context**: INCEPTION - Application Design aprobada → Units Generation.

---

## Units Generation — Part 1 (Planning)
**Timestamp**: 2026-07-03T01:21:55Z
**AI Response**: Generó `plans/unit-of-work-plan.md` con descomposición propuesta en 3 unidades verticales (U1 Camino NIIF walking-skeleton / U2 Config+Experimentación / U3 Credibilidad+Robustez) + 4 preguntas (estrategia de rebanado, cantidad, modelo de despliegue, organización de código). GATE: esperando respuestas + aprobación.
**Context**: INCEPTION - Units Generation - Steps 1-9.

---

## Units Generation — Respuestas + Generación
**Timestamp**: 2026-07-03T01:21:55Z
**User Input**: "listo, A en todas" (Q1-Q4 = A).
**AI Response**: Registró Q1-Q4=A. Generó 3 artefactos en `application-design/`: unit-of-work.md (U1 NIIF / U2 Config+Exp / U3 Credibilidad+Robustez + estrategia de código src/ratchet/<módulo>/), unit-of-work-dependency.md (orden U1→U2→U3), unit-of-work-story-map.md (18/18 historias asignadas, 0 huérfanas). GATE: esperando aprobación. Aprobar cierra la fase INCEPTION.
**Context**: INCEPTION - Units Generation - Steps 12-16.

---

## Units Generation — Revisión del usuario + Correcciones
**Timestamp**: 2026-07-03T01:21:55Z
**User Input**: Revisión: (1) HIGH — US-06 mete faithfulness en el walking skeleton, contradice PRD Seg 8 #8 (faithfulness = endurecer, post-skeleton) y viola INVEST → partir en US-06a/US-06b. (2-5) cosméticos: US-08 "programada"→disparada; US-01 marca 🎯 inconsistente; ApprovalService no listado en U1; ejemplo de US-14 usa datos de config (vive en U2).
**AI Response**: Partió US-06 → US-06a (recall, U1) / US-06b (faithfulness, Must post-skeleton, movido a U3). Cosméticos: US-08 "disparada (manual en MVP; programada=Should)"; US-01 header marcado 🎯; U1 componentes ahora listan C8(+ApprovalService); ejemplo de US-14 reencuadrado a rama de datos + nota de que config se ejercita en U2. Actualizó stories.md, unit-of-work.md, story-map (total 19 historias, 0 huérfanas). GATE: esperando aprobación final.
**Context**: INCEPTION - Units Generation - correcciones post-review.

---

## Units Generation — Aprobación / Cierre de INCEPTION
**Timestamp**: 2026-07-03T01:21:55Z
**User Input**: "cierra y dejemos hasta ahi por hoy"
**AI Response**: Units Generation aprobada. **FASE INCEPTION COMPLETA** (Workspace Detection → Requirements → User Stories → Workflow Planning → Application Design → Units Generation). Sesión pausada. Reanudar en CONSTRUCTION por U1 · Camino NIIF (Functional Design → NFR Requirements → NFR Design → Infrastructure Design → Code Generation → Build & Test).
**Context**: Fin de INCEPTION; siguiente sesión = CONSTRUCTION.

---

## CONSTRUCTION · U1 — Functional Design (Aprobado)
**Timestamp**: 2026-07-03T00:00:00Z (fecha lógica: 2026-07-03)
**User Input**: "si. que sigue, lo apruebo, pero antes dime cual sigue"
**AI Response**: Functional Design de U1 · Camino NIIF generado y **aprobado** tras review del usuario. Artefactos: `construction/u1-camino-niif/functional-design/{domain-entities,business-logic-model,business-rules}.md` + plan con respuestas en `construction/plans/u1-camino-niif-functional-design-plan.md`. Decisiones: recall-por-span τ=0.8 sobre offsets, gate por CI inferior del delta ≥0 (bootstrap pareado), monitor δ=0.05, k=5, dos gates humanos (US-13/US-16), reindex-falla⇒revert+inconclusa, idempotencia por (golden_set_version, config_hash, corpus_hash, patch_hash). Se aplicaron 6 correcciones del review: (1)🔴 per_item lleva `critical` para que el guardrail 🔒 sea computable en el gate; (2)🟡 respuesta_usa_span = containment textual, no faithfulness; (3)🟡 corpus_hash añadido a la clave de estado; (4)🟢 mapeo approve→deploy; (5)🟢 cobertura.fix_layer underspecified→U2; (6)🟢 símbolos ligados en pseudocódigo.
**Context**: CONSTRUCTION — Functional Design ✅. Siguiente etapa: NFR Requirements (ligero) de U1.

---

## CONSTRUCTION · U1 — NFR Requirements (Aprobado, con delegación)
**Timestamp**: 2026-07-03T00:00:00Z (fecha lógica: 2026-07-03)
**User Input**: (aprobación) "aprobá el NFR Requirements ahora, y entramos a NFR Design arrastrando estos tres carry-overs".
**AI Response**: NFR Requirements (ligero) de U1 generado y **aprobado** tras dos rondas de review del usuario. Artefactos: `construction/u1-camino-niif/nfr-requirements/{nfr-requirements,tech-stack-decisions}.md`. Decisiones: Postgres desde el arranque (tras puerto/repo), reproducibilidad bit-exacta solo determinista, latencia <5min secuencial, B=1000 seed fijo, una corrida a la vez, secrets por env. Se añadió nota de **delegación**: la composición canónica de la clave de estado es propiedad de NFR Design, no del Functional Design.
**Context**: CONSTRUCTION — NFR Requirements ✅. Siguiente etapa: NFR Design.

## ERRATUM — Nivel de propiedad de la clave de estado (root cause del drift corpus_hash)
**Timestamp**: 2026-07-03T00:00:00Z
**Hallazgo (review del usuario):** la tupla literal de la clave de estado `(gs_version, config_hash, corpus_hash, patch_hash, eval_params)` se fijó en el **nivel equivocado** — quedó hardcodeada en el Functional Design (BR-73, `RunRecord.run_id`, glosario `StateRef`) cuando su dueño legítimo es **NFR Design** ("hashing de estado / idempotencia"). Esto causó drift entre artefactos al ascender la clave de 3→4→5 componentes.
**Decisión (forward-only, ratchet-legal):** NO se reabre el Functional Design ahora. En la etapa **NFR Design** que sigue: (1) la clave se define UNA vez en `nfr-design-patterns.md`; (2) en el mismo diff se **bajan a referencia** los 3 literales del Functional Design (BR-73, `RunRecord.run_id`, `StateRef`) → "clave de estado (ver nfr-design-patterns)". Es quitar duplicación, no rediseñar. Se registrará su cierre al aprobar NFR Design.
**Carry-overs arrastrados a NFR Design:** (1) tupla canónica de la clave + cómputo de `corpus_hash` (corpus externo → `RagPatientPort.corpus_fingerprint()`); (2) precondición "retrieve determinista para índice fijo"; (3) ubicación de `k/τ` (tensión: `config_hash`=config del RAG vs. knobs de Ratchet → resolver renombrando o dejando `eval_params` explícito).
**Retirada de recomendación previa:** se descarta "propagar corpus_hash a los tres sitios del Functional Design" — duplicaría el dato en el nivel equivocado, contra el framework.

---

## CONSTRUCTION · U1 — NFR Design (Aprobado)
**Timestamp**: 2026-07-03T00:00:00Z (fecha lógica: 2026-07-03)
**User Input**: (aprobación) "si" — tras review, "aprobar, arrastrando tres carry-overs".
**AI Response**: NFR Design de U1 generado y **aprobado**. Artefactos: `construction/u1-camino-niif/nfr-design/{nfr-design-patterns,logical-components}.md`. 5 patrones (P-1 Estado&Idempotencia [dueño único de la clave], P-2 Reproducibilidad, P-3 Frontera de agencia, P-4 Resiliencia, P-5 Gate humano) + componentes lógicos (StateHasher, BootstrapEstimator, RetryPolicy, RunRepository idempotente, AgencyBoundary). Decisiones: eval_params explícito, retry+backoff, UNIQUE(StateKey) en DB, import-linter en CI, fingerprint por doc. **Erratum de la clave de estado CERRADO**: BR-73, RunRecord.run_id, StateRef glosario y BL-10 bajados a referencia a §P-1 (0 literales restantes, verificado por grep).
**Fixes del review aplicados ahora:** (1)🟡 RetryPolicy SOLO sobre lecturas; mutaciones (apply_data_patch/reindex) → revert+inconclusa, no retry (P-4 corregido); (2)🟡 hueco de inyección en frontera de agencia: import-linter es necesario-no-suficiente, regla de que constructores de gate/orchestrator no aceptan LlmPort (P-3); (3)🟡 firma de corpus_fingerprint alineada en los 3 docs → devuelve contenido crudo, Ratchet normaliza+hashea con el mismo normalize() de BL-1 (dueño único de normalización). Menores 🟢: glosario StateRef sin lista inline (solo puntero), P-5 pending = waiting seguro (no terminal), nota patch_hash redundante en rama datos.
**Carry-overs abiertos → Code Generation:** CG-1 (RetryPolicy solo reads — verificar en impl.), CG-2 (test que verifica que gate/orchestrator no reciben LlmPort por constructor).
**Context**: CONSTRUCTION — NFR Design ✅. Siguiente etapa: Infrastructure Design (mínimo).

---

## CONSTRUCTION · U1 — Infrastructure Design (mínimo) (Aprobado) — CIERRE DE FASE DE DISEÑO
**Timestamp**: 2026-07-03T00:00:00Z (fecha lógica: 2026-07-03)
**User Input**: (aprobación) tras review: "aprobar la infra... aplique el #1 ahora... resuelva #2/#3 con nota explícita (U1 libre-de-LLM + generate() stub)".
**AI Response**: Infrastructure Design mínimo de U1 generado y **aprobado**. Artefactos: `construction/u1-camino-niif/infrastructure-design/{infrastructure-design,deployment-architecture}.md`. Topología: `app` (monolito FastAPI+CLI+RAG in-process+Job Runner síncrono) + `db` (Postgres 16); RAG de muestra in-process tras RagPatientPort (Q1); migraciones Alembic al arranque (Q2); CI GitHub Actions (ruff+import-linter+pytest). **Con esto la FASE DE DISEÑO de U1 queda COMPLETA** (Functional + NFR Req + NFR Design + Infra).
**Fixes del review aplicados:** (1)🔴 corrección factual — el GOLDEN SET no es recomputable (es la verdad humana, BR-76); se separó de baseline/runs (esos sí recomputables) y se siembra desde fuente versionada en repo → CG-4. (2)/(3)🟡 se declaró el CAMINO NIIF de U1 como LIBRE-DE-LLM y hermético (recall=código, localizador determinista por span_vigente_en_corpus antes del LLM, gate=código, generate() stubbeado) → e2e NIIF corre en CI sin ANTHROPIC_API_KEY, sin red, reproducible. generate() real usaría cliente LLM propio del RAG (P5), diferido a U3 → CG-3. ANTHROPIC_API_KEY marcada condicional (solo ramo ambiguo del localizador / U3).
**Carry-overs → Code Generation:** CG-1 (retry solo reads), CG-2 (test no-inyección LlmPort), CG-3 (RAG stubbea generate()), CG-4 (golden set sembrado desde repo).
**Context**: CONSTRUCTION — Infrastructure Design ✅. **Fase de diseño de U1 COMPLETA.** Siguiente etapa: Code Generation (primer código en src/ratchet/).

---

## Cierre de sesión — Fase de diseño de U1 COMPLETA, código sin empezar
**Timestamp**: 2026-07-03T00:00:00Z (fecha lógica: 2026-07-03)
**User Input**: "cerremos hasta ahí".
**AI Response**: Sesión pausada en un punto limpio. **Estado:** CONSTRUCTION · U1 — diseño COMPLETO y aprobado (Functional ✅ · NFR Requirements ✅ · NFR Design ✅ · Infrastructure Design mínimo ✅). **Código: NADA implementado** — `src/` vacío, sin `pyproject.toml` (se revirtió un intento de scaffold; el usuario pidió no implementar). Alcance de infraestructura confirmado **mínimo** (walking-skeleton-first; enterprise documentado como roadmap, no construido). Siguiente etapa: **Code Generation**, empezando por CG-0 (scaffold + import-linter fail-closed), luego bucle test-alongside (test-writer + code-reviewer) módulo por módulo desde el núcleo determinista. Carry-overs abiertos para Code Generation: CG-1 (retry solo reads), CG-2 (test no-inyección LlmPort), CG-3 (RAG stubbea generate()), CG-4 (golden set sembrado desde repo). Reanudar requiere luz verde explícita del usuario.
**Context**: Fin de sesión. Diseño de U1 cerrado; implementación pendiente de aprobación.

---

## Estación 4 — Cierre de checklist (validación contra runbook oficial)
**Timestamp**: 2026-07-04 (fecha lógica)
**User Input**: "hazlo!" — cerrar la brecha del checklist de la Estación 4 tras validar contra `hardcoreIA/c3/Estación 4/estacion4-runbook.md`.
**AI Response**: Validado el repo contra el runbook. Los 6 artefactos de Inception + C4(L1/L2 Mermaid) + NFRs→tácticas ya estaban cubiertos (nombres distintos por v0.1.8). Brecha real = ADRs (0). Acciones: (1) creados 6 ADRs en `docs/adr/` (ADR-001 adaptador P5, ADR-002 recall=código/faithfulness=juez, ADR-003 gate determinista+revert, ADR-004 monolito modular, ADR-005 clave de estado/idempotencia, ADR-006 walking-skeleton-first) + índice `docs/adr/README.md`; (2) índice-alias `aidlc-docs/inception/README.md` mapeando los 6 nombres canónicos del runbook a los archivos reales; (3) corregida nota de estación en `user-stories-assessment.md` (Estación 5 = Construction, no backlog — manda el runbook). Solo documentación, cero código. Los ADRs destilan decisiones ya tomadas, no introducen nuevas.
**Context**: Checklist de Estación 4 cerrado. Fase actual sigue siendo Estación 5 (Construction), diseño de U1 completo, Code Generation pendiente.

---

## Estación 5 — Conformación de specs de Construction al runbook (Actividades 1-4)
**Timestamp**: 2026-07-04 (fecha lógica)
**User Input**: "nada de solo lo barato, sigamos al pie de la letra lo que nos piden ! y hacerlo".
**AI Response**: Validado U1 contra `hardcoreIA/c3/Estación 5/estacion5-runbook.md` y conformadas las 4 actividades de specs a su estructura/checklist (sin perder contenido; alias donde había cross-refs):
- **Act 1 · Diseño funcional:** `domain-entities.md` reescrito a DDD táctico (Bounded Context · Entities con Identidad/Atributos/Comportamientos · Value Objects con Validación · Aggregates). `business-logic-model.md` reestructurado con Flujos E2E (Descripción·Pasos·Reglas·Estados) + algoritmos de soporte + máquina de estados. `business-rules.md` a formato RULE (Descripción·Condición·Consecuencia·Fuente·Test), conservando IDs BR-xx (alias, no refactor — no romper cross-refs de nfr-design).
- **Act 2 · NFR Requirements:** añadido mapeo a los **6 atributos canónicos** con valor numérico + 2 NFR nuevos (NFR-U1-10 Usabilidad ≤3 comandos, NFR-U1-11 Escalabilidad 1 RAG/1 corrida).
- **Act 3 · NFR Design:** creado `nfr-design/nfr-design.md` con **7 ADR-U1-xx por NFR** (campo "NFR relacionado" + ⚠️ en Consecuencias), como proyección de los patrones P-1…P-5 y los ADRs de proyecto.
- **Act 4 · Infrastructure Design:** diagrama de despliegue convertido ASCII → **Mermaid** (2 diagramas); infra reestructurada a las **3 capas** (mapa de servicios · config por servicio · transversales).
**Pendiente (por decisión del usuario, gate aparte):** Act 5 (Code Generation) y Act 6 (Tests) — levantan la pausa de código.
**Context**: Estación 5 — specs (Act 1-4) conformes al runbook. Falta decisión sobre Act 5-6 (código).

---

## Estación 5 — Fixes de review (reincidencias del erratum)
**Timestamp**: 2026-07-04 (fecha lógica)
**AI Response**: Tras review de la conformación E5:
- 🟡#1 (reincidencia erratum): `nfr-requirements.md` L35 volvía a re-deletrear la tupla de la clave de estado (contradecía L29 "dueño = §P-1"). Corregido a referencia pura a §P-1. Verificado: 0 tuplas literales en specs vivos; la composición vive solo en §P-1 (dueño) + ADR-U1-03 (congelado, forma abreviada).
- 🟡#2: NFR-U1-11 usaba "≥ N ítems" (placeholder = TBD disfrazado, contra "no inventar"). Corregido a bound real ligado a NFR-U1-4 (≥50 piso hasta que una corrida siga < 5 min; techo exacto = TBD honesto) + referencia a NFR-U1-9 en vez de repetir la concurrencia.
- 🟢#3 aclarado: BR-57/BR-58 NO son nuevas del reformateo — preexistían de rondas anteriores (respuesta_usa_span / cobertura); el reformateo solo las reordenó. Sin scope creep.
**Context**: Specs E5 conformes y sin re-drift. Code Generation (Act 5-6) sigue en pausa.

---

## Estación 6 — Scaffolding operativo (agentic engineering, fuera de AI-DLC)
**Timestamp**: 2026-07-04 (fecha lógica)
**User Input**: "de acuerdo al plan, hazlo!"
**Contexto validado:** el material de la E6 define explícitamente que la implementación NO es parte de AI-DLC ("más allá de AI-DLC"; "queda como ejercicio de aplicación"; los artefactos AI-DLC son el "contrato de entrada"; E7 los convierte en trabajo concreto). Confirma que dejar E5 en specs completas + código en pausa es el handoff correcto.
**AI Response:** creados 3 artefactos de scaffolding (solo Markdown, cero código, pausa intacta):
- `AGENTS.md` (raíz) — manual operativo portable para arneses no-Claude (runbook §5): propósito, stack/comandos, dónde vive qué, reglas de edición (regla de oro, G1/G2/G3), comandos obligatorios, evidencia, áreas sensibles (clave §P-1, frontera G2, golden set), subagentes/hooks, estado.
- `docs/harness-ficha.md` — ficha de arnés (Claude Code) + modelo + características de inferencia (cifras apuntando a skill claude-api / Artificial Analysis, sin inventar) + benchmarks como señal.
- `docs/validaciones-y-orquestacion.md` — validaciones disponibles (ruff, import-linter, pytest/PBT, e2e NIIF, subagentes, hooks) con qué bloquea entrega + nota de orquestación para E7.
**Decisiones de alcance:** `DESIGN.md` NO creado (N/A — sin UI); `PRODUCT.md` NO creado (memoria de producto ya en definicion.md/pvb.md, referenciada desde AGENTS.md).
**Context:** Checklist E6 (scaffolding) cerrado. Implementación (código) sigue en pausa, lista para E7.

---

## Estación 7 — Fase A: Planning wave (docs, sin código, sin herramientas externas)
**Timestamp**: 2026-07-04 (fecha lógica)
**User Input**: "vamos con la Fase A".
**AI Response**: Generado el planning wave de U1 en `docs/tasks/` (contrato OpenSymphony), descomponiendo las specs de U1 en cola ejecutable. NADA de código, no levanta la pausa, no toca src/.
- `orchestration-map.md` — mapa de orquestación (intención/contexto/scope/deps/ejecución/validación/review/memoria) + DAG.
- `task-package.yaml` — manifiesto (planningWave u1-camino-niif-implementation, 3 milestones, 13 tasks).
- `milestones.md` — M1 núcleo determinista · M2 datos y loop · M3 superficie y demo.
- `001-*.md`..`013-*.md` — 13 task files con contrato OpenSymphony (frontmatter id/milestone/priority/estimate/blockedBy/blocks/parent + Summary/Scope/Deliverables/Acceptance/Test Plan/Context/Definition of Ready), atados a BR-xx/NFR-U1-xx/CG-x.
- `validation.md` — validación manual (dry-run equivalente): 13/13 archivos, milestones cuadran, DAG sin ciclos, 9 olas de despacho.
**Pendiente (fuera de Fase A):** Fase B (publicar a Linear, AI PR review, memoria — requiere cuentas/herramientas externas) y Fase C (ejecución = levanta la pausa de código).
**Context**: E7 Fase A completa. Cola lista para publicar/ejecutar cuando se decidan Fase B/C.

---

## Estación 7 — Fase A: fixes de review (insumos humanos + CG-2)
**Timestamp**: 2026-07-04 (fecha lógica)
**AI Response**: Tras review del planning wave:
- 🔴 Los insumos humanos (golden set ≥50 + corpus NIIF par vieja/nueva) estaban como nota, no como tarea. Elevados a **TASK-000 (M0: Datos, owner=humano, estimate 8, blocks TASK-006/007)** — ruta crítica, arranca en paralelo con M1, bloquea el demo si no arranca ya. Enlazado en blockedBy de 006/007 + DoR actualizados.
- 🟡 CG-2 (constructor no acepta LlmPort — inyección runtime que import-linter no atrapa): ahora acceptance explícito en **TASK-004 (gate)** además de TASK-011 (orchestrator).
- 🟢 dataviz: nota en TASK-012 (invocar skill dataviz antes del chart del reporte HTML). Calendario/ruta crítica añadido a validation.md (Wave 0, riesgo #1 = TASK-000).
Re-validado: 14/14 tareas, 4 milestones, DAG acíclico, CG-2 en 004+011.
**Context**: E7 Fase A robustecida. Cola completa y honesta (incluye el trabajo humano de datos).

---

## Estación 7 — Decisión de arnés (ejecución)
**Timestamp**: 2026-07-04 (fecha lógica)
**User Input**: elección de suscripción/arnés = "ChatGPT Pro + Codex CLI".
**Decisión (regla limpia, no proveedor congelado):** el arnés = el de la suscripción que se paga. Elegido **ChatGPT Pro + Codex CLI** por costo para code-gen orquestado (+ Codex Code Review tier gratis). Patrón **híbrido**: 1 tarea autónoma con OpenSymphony (aprender el patrón E7) + 13 tareas **semi-manuales** despachadas en Codex con el task-package como checklist. Cap de gasto obligatorio. **Palanca real de ahorro = Ratchet hermético** (núcleo/CI se testean sin tokens), no la elección de proveedor.
**Correcciones de review incorporadas:** "orquestar con Claude → API por token" era falso en general (solo aplica a orquestadores terceros como OpenSymphony); Claude Code orquesta sobre Max a costo plano. Datos de costo del WhatsApp = señales con margen de error → **re-verificar precios al ejecutar**.
**Setup pendiente (lo hace el usuario):** suscribir ChatGPT Pro, instalar/auth Codex CLI, cap de gasto, arrancar TASK-000 (curación datos, humano, ruta crítica) en paralelo. OpenSymphony/Linear solo para la 1 tarea autónoma.
**Nota de rol:** a partir de aquí el código lo escribe Codex (arnés elegido); rol de este asistente (Claude Code) = apoyo (review con subagentes, config puntual, specs/bitácora).
**Context**: E7 — arnés decidido. Ejecución en manos del usuario + Codex.

---

## CONSTRUCTION · U1 — Code Generation + Build&Test COMPLETO (registro retroactivo)
**Timestamp**: 2026-07-05 (fecha lógica; construido entre 2026-07-04 y 07-05)
**AI Response**: Se levantó la pausa de código y se construyó **U1 · Camino NIIF end-to-end**, tarea por tarea (RAT-5…18, 14 tareas), con bucle test-alongside + subagente `code-reviewer` y los 4 gates (ruff · import-linter G2 · pytest unit/PBT · pytest integración+e2e). Resultado: **184 tests**, e2e NIIF hermético (sin `ANTHROPIC_API_KEY`, sin red), CI verde, **G2 KEPT**. Carry-overs CG-1…CG-4 resueltos en implementación. **Hallazgo del review de RAT-18 corregido:** `cubre()` daba un falso positivo del recall (comparaba solo offsets) → ahora exige que el texto del span esté en el chunk (🔒 BR-34, `fix ff63bfa`). El log de audit no había registrado esta fase; se registra ahora para que el estado no mienta ("Code Generation ← siguiente" era falso). Detalle: memoria `u1-completo.md`.
**Context**: CONSTRUCTION — U1 COMPLETO. Restaura la verdad #1 (U1 se construyó).

---

## Re-scope de unidades v2 — pivote agéntico (decisión deliberada, forward-only)
**Timestamp**: 2026-07-06 (fecha lógica)
**User Input**: Tras 2º panel de expertos (agéntico) + investigación de mercado (jul 2026): el demo de U1 (*fuente-vieja*) se resuelve con una regla → no demostraba agencia. Reencuadre a "Knowledge Reliability Agent" (`definicion.md` v2). Refinamiento del usuario: respetar **1-propósito-por-unidad**; no enterrar scope diferido en una unidad "agendada".
**Decisión (forward-only, ratchet-legal — NO se reabre Inception):** loop-back deliberado en la cascada (el framework lo permite, HITL). Re-scope de unidades: **U1** = sustrato determinista (intacto); **U2** = Investigador Agéntico (contradictorios + loop + RAG externo propio [ADR-008] + eval del agente + *definir* política de autonomía); **U3** = Credibilidad (2º paciente AnythingLLM + faithfulness + robustez); **U4/backlog** = rama config + Experimenter + *demostrar* auto-config (diferido explícito, no oculto). El viejo "U2 = rama config" baja a U4/backlog. Las historias de U2 son nuevas → se generan en Requirements de U2 (Fase B); las viejas quedan como registro. `unit-of-work.md` lleva la nota de reconciliación (no reescritura); las unidades de Inception quedan como registro histórico.
**Context**: Restaura la verdad #2 (pivote + re-scope). Siguiente: sub-cascada de Construction de U2.

---
