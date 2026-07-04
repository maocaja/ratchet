# Deployment Architecture (mínimo) — U1 · Camino NIIF

> Diagrama de despliegue del walking skeleton. Un solo desplegable + Postgres; RAG de muestra in-process.

## Topología (docker-compose) — diagrama de despliegue

```mermaid
flowchart TB
    Operator["👤 Operador<br/>(CLI Typer / HTTP)"]

    subgraph compose["docker-compose"]
        subgraph app["app (contenedor) — monolito modular · entrypoint: alembic upgrade head → uvicorn"]
            API["FastAPI (API) + CLI Typer<br/>(C10)"]
            subgraph core["core — SIN cliente LLM (G2)"]
                ORCH["orchestrator/ · gate/"]
                EVAL["evaluator/ · monitor/ · reporter/ · registry/"]
                INV["investigator/ (Localizer)"]
                DOM["domain/ · persistence/"]
            end
            subgraph adapter["adapter/ (puertos P5)"]
                RAGPORT["RagPatientPort → RAG de muestra IN-PROCESS<br/>(corpus NIIF/NIA + vector store)<br/>generate() = STUB en U1 (CG-3)"]
                LLMPORT["LlmPort"]
            end
        end
        DB[("db — PostgreSQL 16<br/>UNIQUE(StateKey) · Alembic<br/>golden set / baseline / runs")]
    end

    Anthropic["🧠 Anthropic API<br/>(externo · juez U3 + gen)"]

    Operator -->|"ratchet run / approve / report · HTTP"| API
    API --> core
    core --> adapter
    INV -.->|"LlmPort · DORMIDA en camino NIIF<br/>(solo ramo ambiguo)"| LLMPORT
    LLMPORT -.->|"HTTPS (salida)"| Anthropic
    core -->|"SQL (SQLAlchemy)"| DB

    classDef nollm fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e;
    classDef ext fill:#fff7ed,stroke:#ea580c,color:#7c2d12;
    class core,ORCH,EVAL,DOM nollm;
    class Anthropic,DB ext;
```

> **Leyenda:** líneas sólidas = ruta viva del camino NIIF (hermética, sin red). Líneas punteadas (`-.->`) = ruta **dormida** en el camino NIIF (solo se activa en el ramo ambiguo del localizador). `gate/`/`orchestrator/` no tienen arista al LLM (G2, enforced por import-linter).

## Flujos

- **Operador → app:** CLI (`ratchet run|report|approve`) o HTTP (`POST /runs`, `GET /runs/{id}/report`, `POST /approvals/{id}`). Misma superficie (C10).
- **app → db:** SQLAlchemy; corridas idempotentes por `UNIQUE(StateKey)`.
- **app → RAG (in-process):** llamadas de método vía `RagPatientPort` (retrieve/generate/config/data-ops + `corpus_fingerprint`). Sin red.
- **app → Anthropic (red, salida):** solo desde `investigator/` (Localizer delgado); `gate/`/`orchestrator/` **no** (G2, enforced por import-linter). `RetryPolicy` envuelve solo lecturas. **Dormida en el camino NIIF** (localización determinista por `span_vigente_en_corpus`); se activa solo en el ramo ambiguo.
- **RAG `generate()`:** **stub en U1** (determinista, sin red — CG-3). Un `generate()` real usaría el **cliente LLM propio del RAG** (no el `LlmPort` de Ratchet — P5), en U3.
- **Propiedad:** el **e2e NIIF es libre-de-LLM y hermético** (sin key, sin red, reproducible en CI). Ver `infrastructure-design.md §Determinismo`.

## Ciclo de vida
1. `docker-compose up` → `db` levanta; `app` entrypoint corre `alembic upgrade head` y luego sirve.
2. Golden set se carga (CLI/seed) → baseline se fija (rechaza si <50).
3. Corrida del loop (síncrona, <5 min) → reporte antes/después persistido.
4. Reinicio: `app` es stateless → recupera todo de `db`.

## Escalado (documentado, NO U1)
```mermaid
flowchart LR
    subgraph hoy["U1 (hoy)"]
        A1["app monolito<br/>+ RAG in-process"] --- P1[("Postgres")]
    end
    subgraph end2["endurecer (roadmap, NO U1)"]
        GW["NestJS gateway"] --> CORE["core Python"] --> Q["cola SQS/RQ"] --> W["workers Lambda/EKS"]
        EXTRA["RDS Multi-AZ · LB + health checks · LangFuse · IaC Terraform<br/>2º paciente RAG = contenedor por HTTP (cambia impl. de RagPatientPort, no el core)"]
    end
    hoy -->|"costura P5:<br/>el core no cambia"| end2
```
- La costura P5 (adaptador por interfaz) es lo que hace barato este salto: el core no cambia.
