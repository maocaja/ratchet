# Inception (Estación 4) — índice y mapeo a los 6 artefactos del runbook

> Este repo usa **aidlc-workflows v0.1.8**, que organiza los artefactos de Inception en subcarpetas y con algunos nombres propios. El **contenido de los 6 artefactos** que pide el runbook de la Estación 4 está completo; esta tabla mapea cada nombre canónico a su ubicación real.

| # | Artefacto canónico (runbook) | Dónde vive en este repo | Notas |
|---|---|---|---|
| 00 | `workspace-detection.md` | [`../aidlc-state.md`](../aidlc-state.md) (sección *Workspace State* + *Stage Progress*) | v0.1.8 lo consolida en el state tracking |
| 01 | `requirements-analysis.md` | [`requirements/requirements.md`](requirements/requirements.md) (+ [`requirement-verification-questions.md`](requirements/requirement-verification-questions.md)) | FRs, NFRs, criterios MVP |
| 02 | `user-stories.md` | [`user-stories/stories.md`](user-stories/stories.md) + [`personas.md`](user-stories/personas.md) | Personas + historias INVEST + escenarios Gherkin; incluye la Épica-Journey NIIF |
| 03 | `workflow-planning.md` | [`plans/execution-plan.md`](plans/execution-plan.md) (+ `story-generation-plan.md`, `unit-of-work-plan.md`, `application-design-plan.md`, `user-stories-assessment.md`) | Orden de construcción, dependencias, puntos human-in-the-loop |
| 04 | `application-design.md` | [`application-design/application-design.md`](application-design/application-design.md) + [`components.md`](application-design/components.md) + [`services.md`](application-design/services.md) + [`component-dependency.md`](application-design/component-dependency.md) | Coincide con los 3 sub-archivos que pide el runbook; añade `component-methods.md` |
| 05 | `units-generation.md` | [`application-design/unit-of-work.md`](application-design/unit-of-work.md) + [`unit-of-work-story-map.md`](application-design/unit-of-work-story-map.md) + [`unit-of-work-dependency.md`](application-design/unit-of-work-dependency.md) | 3 unidades por dominio (U1 Camino NIIF, U2 Config, U3 Credibilidad) |

## Arquitectura Just-in-Time (runbook §Arquitectura JIT)
| Bloque | Dónde vive |
|---|---|
| **C4 Nivel 1 y 2 (Mermaid)** | [`../../specs/arquitectura.md`](../../specs/arquitectura.md) — Seg 1 (Contexto) + Seg 2 (Contenedores) |
| **NFRs → tácticas + verificación** | `arquitectura.md` Seg 3 (matriz NFR) + Construction: `construction/u1-camino-niif/nfr-requirements/` y `nfr-design/` |
| **ADRs (mín. 1, típico 3–6)** | [`../../docs/adr/`](../../docs/adr/) — 7 ADRs |

## Fase actual
Inception (Estación 4) **completa**. Trabajo en curso: **Estación 5 (Construction)** — diseño de U1 completo; Code Generation pendiente. Estado detallado en [`../aidlc-state.md`](../aidlc-state.md).
