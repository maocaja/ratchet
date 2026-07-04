# Architecture Decision Records — Ratchet

Registro de decisiones arquitectónicas significativas (difíciles/costosas de revertir). Formato: Contexto · Decisión · Alternativas · Consecuencias · Estado (runbook Estación 4, Bloque 3).

Fuente de las decisiones: `aidlc-docs/audit.md`, los planes de `aidlc-docs/`, `specs/arquitectura.md` y `docs/critica.md`. Estos ADRs **destilan** decisiones ya tomadas; no introducen nuevas.

| ADR | Decisión | Estado |
|---|---|---|
| [ADR-001](ADR-001-adaptador-hexagonal-rag.md) | Adaptador hexagonal `RagPatientPort` — el RAG es sistema externo (P5) | Aceptado |
| [ADR-002](ADR-002-recall-determinista-faithfulness-juez.md) | Recall = código determinista · Faithfulness = LLM-juez (regla de oro) | Aceptado |
| [ADR-003](ADR-003-gate-determinista-revert-automatico.md) | Gate de no-regresión determinista + revert automático (G2) | Aceptado |
| [ADR-004](ADR-004-monolito-modular-vs-microservicios.md) | Monolito modular para el MVP (no microservicios) | Aceptado |
| [ADR-005](ADR-005-clave-de-estado-idempotencia.md) | Clave de estado canónica + idempotencia (dueño único = NFR Design) | Aceptado |
| [ADR-006](ADR-006-walking-skeleton-first.md) | Walking-skeleton-first — U1 Camino NIIF end-to-end primero | Aceptado |
| [ADR-007](ADR-007-postgres-desde-el-arranque.md) | PostgreSQL desde el arranque, tras puerto/repositorio | Aceptado |

> **Documentos vivos:** un ADR "Aceptado" no se edita cuando la decisión cambia — se **supersede** con un ADR nuevo (`Reemplazado por ADR-X`). Ej.: si en U2/U3 entra el Job Runner async real o el 2º paciente por HTTP, se emite un ADR que supersede al afectado, preservando la línea de tiempo.
