# Plan de Units of Work — Ratchet (Part 1: Planning)

> Descompone el sistema en **unidades de trabajo** (agrupaciones lógicas de historias que se construyen una a una en Construction).
> Es un **monolito modular** (un solo desplegable); las unidades son de *desarrollo*, no de despliegue.
> Responde (letra tras `[Answer]:`) y dime "listo". Cada pregunta tiene opción **Recomendada**.

## Descomposición propuesta (sujeta a Q1/Q2)

| Unidad | Nombre | Historias | Prioridad | Entrega |
|---|---|---|---|---|
| **U1** | **Camino NIIF (walking skeleton)** | US-01, US-05, US-06, US-07, US-08, US-10, US-11, US-13, US-03, US-14, US-16, US-17 | Must 🎯 | rebanada vertical end-to-end de la rama de **datos** (el entregable no-negociable) |
| **U2** | **Rama Config + Experimentación** | US-02, US-12 | Must | completa la tesis: variantes dirigidas + gate sobre config (reusa Gate/Evaluator de U1) |
| **U3** | **Credibilidad + Robustez** | US-04 (2º paciente+fallback), US-09 (deriva vs deploy propio), US-15 (revert asimétrico), US-18 (política) | Must/Should | mata el "paciente amañado" + endurece el loop |

**Dependencias:** U2 depende de U1 (Gate, Evaluator, Orchestrator); U3 depende de U1+U2.
**Orden de construcción:** U1 → U2 → U3 (protege el héroe primero).

## Preguntas

### Question 1 — Estrategia de rebanado de unidades
A) **Rebanadas verticales, walking-skeleton primero** (U1 = Camino NIIF end-to-end) — cada unidad entrega valor demostrable; protege el entregable no-negociable **(Recomendada)**
B) Capas horizontales por componente (primero todos los adaptadores, luego todos los evaluadores…) — rompe el walking skeleton, nada demostrable hasta el final
C) Híbrido
X) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 2 — Cantidad/granularidad de unidades
A) **3 unidades** (U1 NIIF / U2 Config+Exp / U3 Credibilidad+Robustez) como arriba **(Recomendada)**
B) 2 unidades (U1 NIIF / U2 todo lo demás) — menos ceremonia, U2 muy grande
C) Más granular (4+ unidades)
X) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 3 — Modelo de despliegue
A) **Un solo desplegable (monolito modular)** — coherente con arquitectura Seg 2 y los 11 días **(Recomendada)**
B) Servicios separados por unidad — contradice la regla #1 (simplicidad) del MVP
X) Other (please describe after [Answer]: tag below)

[Answer]: A

### Question 4 — Organización de código (greenfield)
A) **Paquete único modular** `src/ratchet/<módulo>/` (adapter, registry, evaluator, investigator, experimenter, gate, monitor, reporter, orchestrator, api) + `tests/` + `docker-compose.yml` **(Recomendada)**
B) Otra estructura (describe)
X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Plan de Ejecución (Part 2 — tras aprobación)
- [ ] `unit-of-work.md` — definiciones de U1-U3, responsabilidades, estrategia de organización de código.
- [ ] `unit-of-work-dependency.md` — matriz de dependencias entre unidades + orden de construcción.
- [ ] `unit-of-work-story-map.md` — mapeo historia→unidad (todas las US asignadas, sin huérfanas).
- [ ] Validar fronteras y que las 18 historias están asignadas.
