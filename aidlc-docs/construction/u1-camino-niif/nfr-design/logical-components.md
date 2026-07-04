# NFR Design — Componentes Lógicos — U1 · Camino NIIF

> Componentes lógicos (tecnología-agnóstico) que materializan los patrones de `nfr-design-patterns.md`, y dónde viven en `src/ratchet/<módulo>/`. No son clases finales; son responsabilidades con fronteras.

## Componentes nuevos (introducidos por NFR Design)

### `StateHasher` — módulo `evaluator/` (o `domain/` util)
- **Responsabilidad:** computar `config_hash`, `corpus_hash`, `patch_hash` y ensamblar la `StateKey`/`ReproKey` (P-1).
- **Depende de:** `RagPatientPort.get_config()` y `RagPatientPort.corpus_fingerprint()`; `canonical_json`.
- **Determinista, sin LLM.** Testeable con PBT (mismo input → mismo hash; cambio de 1 doc → cambia `corpus_hash`).

### `BootstrapEstimator(seed)` — módulo `evaluator/`
- **Responsabilidad:** CI bootstrap del recall y del delta pareado (P-2), `B=1000`, `numpy.default_rng(seed)`.
- **Determinista dado el seed.** El seed se persiste en el `RunRecord`.

### `RetryPolicy` — módulo `adapter/` (envoltura) o `domain/`
- **Responsabilidad:** retry acotado + backoff exponencial (max=3) alrededor de **operaciones de lectura idempotentes** de `RagPatientPort`/`LlmPort` (`retrieve`, `generate`, `get_config`, `corpus_fingerprint`) (P-4). Al agotar reintentos → señaliza fallo → corrida `inconclusa`.
- **NO envuelve mutaciones** (`apply_data_patch`, `reindex`): esas van por `revert`+`inconclusa`, no retry (CG-1).
- **No decide nada de negocio**; solo resiliencia de I/O.

### `RunRepository` (idempotente) — módulo `persistence/`
- **Responsabilidad:** persistir/leer `RunRecord`, `Baseline`, `GoldenSet`, writeups, approvals, decisiones. **Upsert idempotente** con `UNIQUE(StateKey)` en DB (P-1, Q3).
- **Dos implementaciones tras el mismo puerto (P5):** Postgres (integración/e2e) e in-memory (unit tests), con paridad de unicidad.

### `AgencyBoundary` (contrato de imports) — raíz del proyecto / CI
- **Responsabilidad:** contrato `import-linter` que prohíbe a `gate/` y `orchestrator/` importar el cliente LLM/`adapter/llm` (P-3, Q4). No es código de runtime; es un gate de build.

## Puertos afectados (extensión de contratos existentes)

### `RagPatientPort` — módulo `adapter/`
- **Método nuevo (requisito NFR-2):** `corpus_fingerprint() -> list[(doc_id, doc_content: str)]` — devuelve **contenido crudo** (no pre-hasheado); Ratchet aplica su `normalize()`+`sha256` (dueño único de la normalización, §P-1). Habilita `corpus_hash` sin acoplar Ratchet al store del RAG.
- **Requisito de determinismo:** `retrieve()` determinista para índice fijo (P-2).

### `LlmPort` — módulo `adapter/` (o `investigator/`)
- Aísla el cliente LLM; solo lo importan `investigator/` (U1) y `experimenter/` (U2+). **Nunca** `gate/`/`orchestrator/` (P-3).

## Mapa componente lógico → paquete `src/ratchet/`
| Componente lógico | Paquete | Patrón |
|---|---|---|
| `StateHasher` | `evaluator/` | P-1 |
| `BootstrapEstimator(seed)` | `evaluator/` | P-2 |
| `RetryPolicy` | `adapter/` | P-4 |
| `RunRepository` (+ fake) | `persistence/` | P-1 |
| `AgencyBoundary` (import-linter) | raíz + CI | P-3 |
| `corpus_fingerprint()` | `adapter/` (puerto C1) | P-1/P-2 |
| `LlmPort` | `adapter/` | P-3 |
| `ApprovalRequest` (ya en FD) | `reporter/` | P-5 |

## Componentes lógicos NO introducidos en U1 (diferidos)
- `CircuitBreaker`, `JobQueue`/`Worker` (RQ+Redis), `LlmResponseCache`, `LoadBalancer`/health-checks, `Tracer` (LangFuse). Todos = fase endurecer.

## Impacto en la estructura de código (sin cambios de layout)
- No se crean paquetes nuevos: `StateHasher`/`BootstrapEstimator` caben en `evaluator/`, `RetryPolicy`/`corpus_fingerprint`/`LlmPort` en `adapter/`, `RunRepository` en `persistence/`. El layout de `unit-of-work.md` se mantiene.
- Nuevos artefactos de build: contrato `import-linter` (config en la raíz) ejecutado en CI (Build & Test).
