# Requirements — Preguntas de Clarificación (Ratchet)

> **Cómo responder:** escribe la letra elegida después de cada `[Answer]:`. Si ninguna opción encaja, usa la última (Other) y describe. Cuando termines, dime "listo".
> Estas preguntas resuelven los TBD reales del PRD antes de generar `requirements.md`. Lo que el PRD ya define no se re-pregunta.

---

## Question 1 — 2º paciente: cuál RAG open-source + fallback si no integra a tiempo
El 2º paciente open-source real es **Must** en tres documentos (`definicion.md` "Las piezas"; `prd.md` Seg 8 #1 + Riesgo #3; `arquitectura.md` Seg 1 → *"resolver antes del día 1"*): es **la** mitigación del "paciente amañado" (hallazgo unánime del panel). No se re-decide *si* va — se decide **cuál** y **cuál es el plan B** si la integración/re-index se atrasa. Así proteges Riesgo #10 (tiempo) **sin** desarmar Riesgo #3 (credibilidad).

A) **Elegir el candidato ya (día 1) + fallback definido** — si no integra para ~día 7, degradar a validación sobre un slice held-out del corpus con fallas orgánicas y **documentar el gap** (mantiene el 2º paciente como Must, con red de seguridad) **(Recomendada)**
B) **Comprometer 1 open-source ahora, sin fallback** — compromiso duro; si se atrasa, come tiempo del skeleton
C) **Fijar solo el criterio hoy, elegir el día 1** — sin candidato aún; criterio = soporta re-index + fallas orgánicas
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 2 — Escenarios de demo requeridos para Demo Day
**(Confirmación — el PRD ya fija ambos: Seg 8 héroe + Seg 13.)** Dos historias con jerarquía: **datos** (cambio de NIIF → parche → re-index) = **héroe/escenario bandera**; **config** (recall 0.70→0.88 vía gate) = **evidencia de apoyo** que prueba el gate/no-regresión. ¿Confirmas que ambos van?

A) **Ambos** (datos como héroe + config como apoyo) — la tesis completa; jerarquía del reencuadre panel 2 **(Recomendada)**
B) **Solo el de datos** (NIIF) — el más memorable y diferenciador, pero deja fuera la prueba del gate/no-regresión
C) **Solo el de config** — más fácil, pero es justo lo que el panel 2 marcó como incoherente para la tesis
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 3 — Tamaño del golden set comprometido para Demo Day
El panel exigió ≥50 (con span de fuente) para tener poder estadístico. ¿Qué comprometes?

A) **≥50 desde el inicio** — cumple la barra de significancia del PRD **(Recomendada si el corpus NIIF lo permite)**
B) **Arrancar ~30 y crecer a 50** — pragmático; se reporta el intervalo de confianza con lo que haya
C) **~20-30** — más rápido de armar a mano, pero debilita el claim estadístico (habría que angostar la promesa)
X) Other (please describe after [Answer]: tag below)

[Answer]: A  (fallback a B si armar 50 spans a mano se atrasa)

---

## Question 4 — Superficie de interacción del MVP
El PRD/arquitectura mencionan CLI + API (FastAPI). ¿Qué construimos para Demo Day?

A) **CLI + API mínima** (sin UI) — suficiente para operar y demostrar el loop **(Recomendada)**
B) **Solo CLI** — lo más rápido; la demo se ve por terminal + reportes en Markdown
C) **CLI + API + UI web mínima** (dashboard de reportes/aprobación) — más vistoso para Demo Day, más trabajo
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 5 — Destino de despliegue para Demo Day
`arquitectura.md` Seg 2 ya lo resolvió: MVP = Python-first **local**; *"Deploy → IaC (Terraform/CDK)"* está bajo *"cómo escalaría al stack enterprise (documentado, no MVP)"*, fast-follow días 31-60. La señal Caseware se da **mostrando el diseño de escalado**, no quemando 11 días en construirlo. ¿Confirmas local para el día 11?

A) **Local/dev reproducible** (docker-compose) — cero fricción para el día 11; AWS + IaC documentado como fast-follow (coherente con arquitectura Seg 2) **(Recomendada)**
B) **Cloud solo el servicio, sin IaC completa** (deploy manual) — punto medio; algo de fricción, algo de señal
C) **Desplegado en cloud (AWS) con IaC** — máxima señal, pero contradice el walking-skeleton-first y Riesgo #10 (tiempo)
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 6 — Personas a modelar en User Stories
**(Confirmación — PRD Seg 7 ya fija ambos.)** El PRD nombra dos actores: **AI/ML Engineer** (dispara, revisa, aprueba) y **Operador/Admin** (golden set, política). ¿Confirmas modelar ambos?

A) **Ambos** (Engineer + Operador/Admin) — refleja el gate humano (P2) y la separación de deberes **(Recomendada)**
B) **Solo AI/ML Engineer** — un solo actor hace todo; más simple para el MVP
C) **Ambos + un tercero** (ej. Auditor/Revisor que solo lee reportes/writeups)
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 7 — Si el tiempo se acaba, ¿cuál es el ÚNICO entregable que DEBE funcionar?
Para priorizar el backlog (el "walking skeleton" mínimo).

A) **El escenario de datos NIIF end-to-end** (detectar caída → investigar → localizar "fuente vieja" → parche → humano confirma → re-index → gate) **(Recomendada: es el diferenciador)**
B) **El gate de no-regresión con la rama config** (medir → experimentar → gate → deploy/revert)
C) **El monitor + detección** (cazar la degradación y el writeup de incidente), aunque el fix quede manual
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 8 — Métrica North Star comprometida
**(Confirmación — PRD Seg 10.)** El PRD propone: **puntos de `recall por span de fuente`** que el loop gana sobre el baseline + guardrail **0 regresiones no detectadas** (dentro de la cobertura del golden set), con significancia (bootstrap CI / McNemar). ¿La confirmas como la métrica de éxito de Demo Day?

A) **Sí, tal cual** el PRD **(Recomendada)**
B) **Sí, pero simplificar la significancia** (reportar solo el delta + intervalo, sin McNemar) para el MVP
C) Ajustar (describe abajo)
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question — Extensión de Seguridad (opt-in del framework)
¿Se deben aplicar las reglas de la extensión de **Seguridad** como restricciones bloqueantes en este proyecto?

A) **Sí** — aplicar todas las reglas de SEGURIDAD como restricciones bloqueantes (recomendado para apps de grado productivo)
B) **No** — omitir las reglas de SEGURIDAD (adecuado para PoCs, prototipos y proyectos experimentales)
X) Other (please describe after [Answer]: tag below)

[Answer]: B  (PoC 11 días, datos públicos, gate humano central; higiene de secrets se mantiene desde arquitectura. Reactivar en el fast-follow productivo)

---

## Question — Extensión de Testing basado en Propiedades / PBT (opt-in del framework)
¿Se deben aplicar las reglas de **Property-Based Testing** como restricciones bloqueantes?

A) **Sí** — aplicar todas las reglas PBT como bloqueantes (recomendado para proyectos con lógica de negocio, transformaciones de datos, serialización o componentes con estado)
B) **Parcial** — aplicar PBT solo a funciones puras y round-trips de serialización (adecuado para complejidad algorítmica limitada)
C) **No** — omitir PBT (adecuado para CRUD simple, proyectos solo-UI o capas de integración delgadas)
X) Other (please describe after [Answer]: tag below)

[Answer]: B  (aplicar a: recall por span, decisión del gate, lógica de revert, serialización de resultados — el núcleo determinista = el guardrail)
