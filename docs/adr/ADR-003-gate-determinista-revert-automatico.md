# ADR-003: Gate de no-regresión determinista + revert automático (G2)

*Fecha: 2026-07-04*

## Contexto
La identidad del producto es "mejora o revierte, **nunca empeora**". El guardrail es **0 regresiones no detectadas dentro de cobertura**; un falso negativo en clase crítica es un incidente. El humano debe aprobar lo que **AVANZA** (P2), pero revertir a lo seguro debe ser **automático** — no puede depender de que haya un aprobador disponible. La agencia (LLM) debe vivir río arriba del gate, no dentro de él.

## Decisión
El `Gate` es **determinista y sin LLM** (G2). Compara el candidato contra el baseline sobre la métrica ancla (recall-por-span) con **CI bootstrap pareado**: aprueba **solo si `CI.lower(delta) ≥ 0`** (no empeora con significancia). Si empeora, ejecuta **revert automático**. Cualquier regresión en **clase crítica** ⇒ revert inmediato, sin importar el delta agregado (guardrail 🔒). El `LoopOrchestrator` tampoco llama al LLM: rutea solo sobre datos deterministas ya verificados.

## Alternativas consideradas
- **Que un LLM decida el deploy/revert** — descartada: viola G2, no reproducible, mete al juez en la ruta crítica.
- **Delta puntual ≥ 0 sin intervalo de confianza** — descartada: un golden set chico haría pasar mejoras que son ruido.
- **Revert que requiera aprobación humana** — descartada: revertir a lo seguro debe ser automático (P1/P2); esperar a un humano para revertir deja el sistema en estado peor.

## Consecuencias
- ✅ La calidad nunca retrocede por un cambio propio; el gate es "la matemática dispone".
- ✅ Verificable mecánicamente: `import-linter` prohíbe que `gate/`/`orchestrator/` importen el cliente LLM.
- ⚠️ Golden set chico ⇒ CI ancho ⇒ cuesta más *probar* mejora (es la barra honesta, no un bug).
- ⚠️ El revert asimétrico (deriva vs. deploy propio) se difiere a U3.

## Estado
Aceptado
