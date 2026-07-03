# Plan de Generación de User Stories — Ratchet (Part 1: Planning)

> Actúo como Product Owner. Este plan define **cómo** convertiremos los FR/NFR en historias.
> Responde las preguntas (letra tras `[Answer]:`) y dime "listo". Cada una tiene opción **Recomendada**.

## Preguntas de Planeación

### Question 1 — Enfoque de desglose (breakdown)
¿Cómo organizamos las historias?

A) **Épicas por capacidad del loop** (Épica = medir / monitorear / investigar-localizar / arreglar-config / arreglar-datos / decidir-gate / reportar-aprobar), con historias adentro, mapeadas a personas y trazadas a FR — limpio para el backlog y la trazabilidad **(Recomendada)**
B) **Por journey de usuario** (historias siguen el flujo NIIF héroe + config apoyo) — muy narrativo, pero mezcla capacidades
C) **Por feature/módulo** (M1…M7) — técnico, se aleja del lenguaje de usuario
D) **Híbrido** (épicas por capacidad + una épica-journey para el escenario NIIF)
X) Other (please describe after [Answer]: tag below)

[Answer]: D  — épicas por capacidad (traza a FR) + épica-journey "Camino NIIF (no-negociable)" como hilo curado del walking skeleton, sin duplicar historias

### Question 2 — Formato de criterios de aceptación
¿En qué formato escribimos los criterios de aceptación?

A) **Gherkin** (Given / When / Then) — testable, alineado a la Estación 4 y a testing (PBT parcial) **(Recomendada)**
B) Lista de checklist simple (bullet points)
C) Given/When/Then + ejemplos de datos concretos (más detalle)
X) Other (please describe after [Answer]: tag below)

[Answer]: A  — Gherkin; para historias del núcleo determinista (recall-por-span, umbrales del gate) añadir ejemplos con datos concretos (0.70→0.88, ≥50, cobertura de span)

### Question 3 — Granularidad de las historias
¿Qué tamaño de historia?

A) **Media (INVEST): cada historia es una capacidad construible en ~1-2 días**, independiente y testable **(Recomendada)**
B) Gruesa: una historia por FR completo (menos historias, más grandes)
C) Fina: sub-historias por cada paso del flujo (más historias, más overhead)
X) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 4 — Priorización visible en las historias
¿Marcamos prioridad para proteger el walking skeleton?

A) **Sí — etiquetar cada historia (Must / Should / Could) y marcar el "camino no-negociable" (escenario NIIF, Q7)** **(Recomendada)**
B) No — solo escribir las historias, priorizar después en el backlog
X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Plan de Ejecución (Part 2 — se ejecuta tras tu aprobación)
- [ ] Generar `personas.md` — 2 arquetipos (AI/ML Engineer, Operador/Admin): objetivos, motivaciones, frustraciones, contexto.
- [ ] Generar `stories.md` — historias por el enfoque elegido, formato INVEST.
- [ ] Escribir criterios de aceptación (formato elegido) por historia.
- [ ] Etiquetar prioridad y marcar el camino no-negociable.
- [ ] Mapear cada persona → historias; cada historia → FR de origen (trazabilidad).
- [ ] Verificar cobertura: todos los FR Must tienen ≥1 historia.
