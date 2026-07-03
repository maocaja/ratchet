# Convenciones de Python / Backend

- **Stack:** Python 3.12+, FastAPI (API + CLI), PostgreSQL, Job Runner async. Monolito modular.
- **Estructura:** el código vive en `src/ratchet/<módulo>/`, un paquete por módulo del PRD (M1 adapter, M3 eval, M4 investigador/localizador, M5 decision, M6 monitor, M7 report). M2 (golden set) se persiste en Postgres.
- **Formato/lint:** `ruff` para lint y formato (no black/isort aparte). Type hints obligatorios en funciones públicas.
- **Dependencias:** `uv` (o `pip`); fijar versiones. No añadir dependencias pesadas sin justificar.
- **Costuras (P5):** el core habla con el RAG objetivo, el LLM y el vector store SOLO por adaptadores/interfaces. NUNCA hardcodear un proveedor en el core.
- **Guardrail G2:** el `LoopOrchestrator`/core NO llama al LLM — rutea sobre datos deterministas. Las llamadas al LLM viven en el Worker (juez) y en el RAG.
- **Async:** experimentos largos van al Job Runner. En el walking skeleton puede ser síncrono/in-process; endurecer = cola real.
- **Errores:** no decidir con datos incompletos — ante fallo de LLM/RAG, marcar corrida "inconclusa" y mantener baseline (P1).
