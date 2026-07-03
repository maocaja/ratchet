# User Stories — Ratchet

> Enfoque: **híbrido (D)** — épicas por capacidad (traza a FR) + **Épica-Journey "Camino NIIF (no-negociable)"** como hilo curado del walking skeleton.
> Formato: **INVEST** + criterios **Gherkin**; en historias del **núcleo determinista** se añaden ejemplos con datos concretos.
> Prioridad: **Must / Should / Could**. 🎯 = parte del **camino no-negociable** (escenario NIIF, Q7).
> Personas: **A** = Andrés (Engineer), **C** = Carolina (Operador/Admin).

---

## Épica E1 — Conectar (Adaptador)  ·  FR-1, FR-11

### US-01 · Conectar Ratchet a un RAG objetivo — **Must** 🎯 *(prerrequisito del camino no-negociable)*
**Como** Andrés, **quiero** conectar Ratchet a un RAG vía adaptador **para** medirlo y experimentarlo sin reescribir su código.
```gherkin
Given un RAG objetivo con endpoints de retrieval y generación
When configuro el adaptador con sus credenciales/endpoints
Then Ratchet puede leer su lineage (documento→chunk→retrieve→genera)
And no modifica el código del RAG (solo config y datos vía contrato del adaptador)
```

### US-02 · Aplicar/revertir config vía adaptador — **Must**
**Como** Andrés, **quiero** que Ratchet aplique y revierta cambios de config del RAG **para** experimentar de forma segura.
```gherkin
Given un cambio de config propuesto (p.ej. chunk_size, retrieval híbrido, reranker)
When Ratchet lo aplica vía adaptador
Then el cambio queda activo y es reversible atómicamente
And un revert restaura exactamente el estado anterior
```

### US-03 · Aplicar/revertir parche de datos + re-index — **Must** 🎯
**Como** Andrés, **quiero** que Ratchet aplique/revierta un parche de datos y re-indexe **para** corregir defectos de la capa de datos.
```gherkin
Given un parche de datos confirmado (reemplazar/actualizar un documento del corpus)
When Ratchet lo aplica vía adaptador
Then el corpus se actualiza y se dispara el re-index
And la operación es reversible (revert restaura el documento y el índice previos)
```

### US-04 · Validar sobre un 2º RAG open-source real — **Must (con fallback)**
**Como** Andrés, **quiero** validar Ratchet contra un RAG de terceros **para** que la mejora no salga de un "paciente amañado".
```gherkin
Given un RAG open-source real elegido el día 1
When Ratchet corre el loop sobre él con fallas orgánicas
Then la mejora se mide sobre un sistema que Ratchet no construyó
And si la integración/re-index no está lista ~día 7
  Then se degrada a un slice held-out del corpus con fallas orgánicas
  And se documenta el gap explícitamente
```

---

## Épica E2 — Medir / Evaluar  ·  FR-2, FR-3

### US-05 · Curar y versionar el golden set — **Must**
**Como** Carolina, **quiero** curar y versionar el golden set (≥50, etiquetado por span de fuente) **para** tener una base de evaluación representativa y auditable.
```gherkin
Given preguntas del dominio contable con su respuesta y su span de fuente
When registro el golden set en el sistema
Then queda versionado e inmutable por versión (recomputable)
And el sistema rechaza cerrar el baseline si hay < 50 ítems
  # dato concreto: umbral de significancia = golden set ≥ 50
```

### US-06a · Evaluar el RAG — recall-por-span — **Must** 🎯 *(núcleo determinista)*
**Como** Andrés, **quiero** evaluar el RAG contra el golden set con recall-por-span **para** obtener una métrica objetiva y comparable.
```gherkin
Given un golden set versionado y un RAG conectado
When ejecuto una evaluación
Then obtengo recall por SPAN de fuente (determinista, comparable entre chunkings)
And la decisión se ancla en esta métrica determinista

# Ejemplo con datos concretos:
Given baseline recall-por-span = 0.70 sobre 50 ítems
When una corrida alcanza recall-por-span = 0.88
Then el delta reportado = +0.18 con su intervalo de confianza (bootstrap)
```

### US-06b · Evaluar el RAG — faithfulness (LLM-judge) — **Must (post-skeleton, endurecer)**
**Como** Andrés, **quiero** añadir faithfulness como métrica secundaria **para** enriquecer el diagnóstico sin que decida el gate.
```gherkin
Given recall-por-span ya funcionando (US-06a)
When añado faithfulness vía LLM-judge
Then obtengo faithfulness como métrica SECUNDARIA (señal, no juez de la decisión)
And la decisión sigue anclada en el recall determinista
```
> Secuenciación (PRD Seg 8 #8): faithfulness se construye **después** del walking skeleton → asignada a U3.

### US-07 · Fijar/actualizar el baseline — **Must**
**Como** Andrés, **quiero** fijar el baseline versionado **para** medir siempre contra una referencia estable.
```gherkin
Given una evaluación completa sobre el golden set vigente
When la fijo como baseline
Then queda versionada junto a la config y la versión del golden set
And toda corrida futura se compara contra ella
```

---

## Épica E3 — Monitorear  ·  FR-4

### US-08 · Detectar caídas y disparar el loop — **Must** 🎯
**Como** Andrés, **quiero** que Ratchet detecte caídas de confiabilidad vs. baseline **para** no enterarme tarde de una degradación silenciosa.
```gherkin
Given un baseline vigente
When una evaluación disparada (manual en MVP; programada = Should) cae por debajo del umbral vs. baseline
Then Ratchet marca una degradación y dispara el loop (investigación)
And notifica a Andrés con el delta detectado
```

### US-09 · Distinguir regresión propia vs. deriva del entorno — **Should**
**Como** Andrés, **quiero** distinguir si la caída viene de un deploy propio o de deriva externa **para** aplicar la respuesta correcta (revert vs. re-experimentar).
```gherkin
Given una degradación detectada
When Ratchet analiza el origen
Then clasifica la causa como "deploy propio" (→ revert disponible) o "deriva del entorno" (→ re-experimentar)
```

---

## Épica E4 — Investigar & Localizar  ·  FR-5

### US-10 · Investigador read-only localiza la capa del defecto — **Must** 🎯
**Como** Andrés, **quiero** que un investigador recorra el lineage y localice la capa del defecto **para** arreglar en el lugar correcto, no a ciegas.
```gherkin
Given una degradación disparada y acceso read-only al lineage
When el investigador sonda el lineage
Then localiza la capa entre: retrieval-miss | chunking | fuente-vieja | cobertura | generación
And lo hace de forma determinista donde es posible:
  | retrieval-miss | el span dorado NO está en top-k pero SÍ está indexado |
  | chunking       | el span quedó partido entre dos chunks                 |
  | fuente-vieja   | el span dorado ya no está / difiere en el corpus       |
  | cobertura      | ningún chunk cubre el tema                              |
  | generación     | el span se recuperó pero la respuesta lo ignora        |
```

### US-11 · Writeup de incidente — **Must** 🎯
**Como** Andrés, **quiero** un writeup de incidente con la capa localizada y la evidencia **para** entender y auditar el diagnóstico.
```gherkin
Given una localización completada
When el investigador cierra la investigación
Then produce un writeup con: síntoma, capa localizada, evidencia, y capa de fix prescrita
And concluye explícitamente cuándo "ninguna perilla lo arregla → es capa de datos"
```

---

## Épica E5 — Arreglar: rama CONFIG  ·  FR-6

### US-12 · Proponer y experimentar variantes de config dirigidas — **Must**
**Como** Andrés, **quiero** que el sistema proponga variantes de config dirigidas por el diagnóstico y las experimente **para** mejorar sin barrido ciego.
```gherkin
Given un writeup que prescribe la capa "config"
When el sistema genera variantes dirigidas (el diagnóstico poda el espacio)
Then experimenta cada variante contra el golden set (pocas variantes, no producto cartesiano)
And entrega la variante ganadora al gate (E6)
```

---

## Épica E6 — Arreglar: rama DATOS  ·  FR-7

### US-13 · Parche de datos propuesto + confirmación humana — **Must** 🎯
**Como** Andrés, **quiero** recibir un parche de datos propuesto y confirmarlo antes de aplicar **para** mantener control sobre cambios al corpus.
```gherkin
Given un writeup que prescribe la capa "datos" (p.ej. doc viejo tras cambio de NIIF 16)
When el sistema propone el parche (reemplazar el doc por su versión vigente)
Then NO se aplica hasta que Andrés lo confirma explícitamente
And al confirmar, dispara la aplicación + re-index (US-03)
```

---

## Épica E7 — Decidir / Gate (revert-safety)  ·  FR-8

### US-14 · Gate de no-regresión con revert automático — **Must** 🎯 *(núcleo determinista)*
**Como** Andrés, **quiero** un gate que impida desplegar algo peor **para** que la calidad nunca retroceda por un cambio propio.
```gherkin
Given una variante (config) o un parche (datos) aplicado
When el gate re-evalúa contra el golden set
Then aprueba solo si NO empeora la métrica anclada (recall-por-span)
And si empeora, ejecuta revert automático (aplica a AMBAS ramas)

# Ejemplo con datos concretos (rama de datos, U1):
Given baseline = 0.70
When tras aplicar el parche de datos la re-evaluación mide 0.68 (peor)
Then el gate revierte el parche automáticamente
When la re-evaluación mide 0.88 (mejor, con CI que excluye el ruido)
Then el gate habilita (sujeto a aprobación humana)
# Nota: el gate es agnóstico a la rama; el caso equivalente para CONFIG se ejercita en U2.
```

### US-15 · Revert asimétrico — **Should**
**Como** Andrés, **quiero** revert asimétrico **para** responder distinto a una regresión propia vs. deriva del entorno.
```gherkin
Given una regresión de un deploy propio
When el gate actúa
Then revierte al estado anterior
Given una caída por deriva del entorno
When el gate actúa
Then no revierte a ciegas: re-experimenta para recuperar
```

---

## Épica E8 — Reportar & Aprobar  ·  FR-9, FR-10

### US-16 · Aprobar/rechazar deploy o parche (gate humano) — **Must** 🎯
**Como** Andrés, **quiero** aprobar o rechazar cada deploy/parche vía CLI/API **para** que nada avance sin decisión humana (P2).
```gherkin
Given una variante o parche que pasó el gate técnico
When reviso la propuesta en la CLI/API
Then puedo aprobar (se aplica) o rechazar (no se aplica)
And si no hay aprobador, nada avanza pero nada se rompe (el baseline se mantiene)
```

### US-17 · Reporte antes/después con evidencia — **Must** 🎯
**Como** Andrés, **quiero** un reporte antes/después con la decisión **para** tener evidencia auditable.
```gherkin
Given un ciclo del loop completado
When abro el reporte
Then veo métrica antes vs. después, la variante/parche, el writeup y la decisión (deploy/revert/pendiente)
And el reporte es reproducible (recomputable desde datos versionados)
```

### US-18 · Definir la política de autonomía — **Should**
**Como** Carolina, **quiero** definir la política (nº de variantes, umbrales del gate) **para** controlar cuánta autonomía tiene el loop.
```gherkin
Given permisos de Operador/Admin
When configuro nº máximo de variantes y el umbral de no-regresión
Then el loop respeta esos límites en cada corrida
And los cambios de política quedan en el audit trail
```

---

## 🎯 Épica-Journey — Camino NIIF (NO-NEGOCIABLE)

> **No duplica historias** — es el hilo curado del walking skeleton (Q7=A): la rebanada vertical end-to-end que DEBE funcionar para Demo Day, en orden.

**Secuencia:**
`US-05` (golden set) → `US-06a` (medir baseline) → `US-08` (detectar caída) → `US-10` (localizar "fuente-vieja") → `US-11` (writeup) → `US-13` (parche + confirmación humana) → `US-03` (aplicar + re-index) → `US-14` (gate re-evalúa / revert si empeora) → `US-16` (aprobación humana) → `US-17` (reporte antes/después).

**Depende de:** `US-01` (adaptador conectado).

```gherkin
Scenario: El asistente cita una NIIF derogada y Ratchet lo corrige de punta a punta
Given un RAG conectado con baseline medido sobre un golden set ≥50
And cambia la NIIF 16 (el corpus quedó con la versión vieja)
When el monitor detecta la caída de recall-por-span
Then el investigador localiza "fuente-vieja" (ninguna perilla lo arregla)
And produce un writeup que propone reemplazar el documento
And Andrés confirma el parche
And Ratchet aplica el reemplazo + re-index
And el gate re-evalúa: si recall recupera, habilita; si empeora, revierte
And Andrés aprueba y obtiene un reporte antes/después auditable
```

---

## Trazabilidad y Cobertura

| FR | Historias |
|---|---|
| FR-1 Adaptador (config+datos) | US-01, US-02, US-03 |
| FR-2 Golden set & registro | US-05, US-07 |
| FR-3 Evaluación | US-06a, US-06b |
| FR-4 Monitor | US-08, US-09 |
| FR-5 Investigador/Localizador | US-10, US-11 |
| FR-6 Rama config | US-12 |
| FR-7 Rama datos | US-13 |
| FR-8 Decisión/Gate | US-14, US-15 |
| FR-9 Reportes & Aprobación | US-16, US-17 |
| FR-10 Interfaz CLI+API | US-16, US-17 (superficie) |
| FR-11 2º paciente | US-04 |

**Cobertura:** todos los FR Must tienen ≥1 historia. ✅
**Camino no-negociable (🎯):** US-01, US-03, US-05, US-06a, US-08, US-10, US-11, US-13, US-14, US-16, US-17.
