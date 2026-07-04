# Validación del paquete — U1 · Camino NIIF (E7 runbook §3)

> Revisión humana del planning wave (equivalente al `validate`/`dry-run` de OpenSymphony, hecho manualmente — el script de la skill no está instalado en Fase A). Todos los checks del runbook §3 y del demo §2.

## Checks del contrato

| Check (runbook §3 / demo §2) | Resultado |
|---|---|
| `task-package.yaml` existe | ✅ |
| Cada task file del manifiesto existe | ✅ 14/14 |
| Cada milestone del frontmatter existe en el manifiesto | ✅ (M0, M1, M2, M3) |
| `blockedBy` / `blocks` / `parent` apuntan a IDs válidos del mismo manifiesto | ✅ (todos referencian TASK-001..013; `parent: null` en todas — sin sub-issues en U1) |
| No hay ciclos en el DAG | ✅ (orden topológico 001→013) |
| Cada tarea referencia los documentos AI-DLC que necesita (`Context`) | ✅ (functional-design, nfr-*, infrastructure, ADRs, carry-overs) |
| Acceptance criteria medibles | ✅ (atados a BR-xx / NFR-U1-xx / CG-x verificables) |
| Test plans con comandos o evidencia manual clara | ✅ (`pytest`, `lint-imports`, PBT, regresiones inyectadas) |
| Las tareas caben en sesiones ejecutables por agente | ✅ (una tarea ≈ un módulo; estimados 2-5 pts) |

## Olas de despacho (waves — tareas no bloqueadas en paralelo)
```
Wave 0:  TASK-000  (DATOS — humano, en paralelo con TODO M1; debe cerrar antes de W3/W5)
Wave 1:  TASK-001                          (scaffold)
Wave 2:  TASK-002                          (domain)
Wave 3:  TASK-003, TASK-007                (evaluator, adapter — 007 requiere 000)
Wave 4:  TASK-004, TASK-005, TASK-008      (gate, persistence, investigator)
Wave 5:  TASK-006, TASK-010                (registry [req 000], reporter)
Wave 6:  TASK-009                          (monitor)
Wave 7:  TASK-011                          (orchestrator — convergencia)
Wave 8:  TASK-012                          (api + reporte HTML)
Wave 9:  TASK-013                          (e2e + CI)
```
> Nota: quien ejecute puede despachar cada ola en paralelo con subagentes; el orquestador solo avanza cuando las dependencias están Done. **TASK-000 corre en su propio carril (humano) desde el día 1.**

## Ruta crítica y calendario (Demo Day: 13 jul, ~9 días)
- **Riesgo #1: TASK-000 (curación de datos).** No es código, no delegable, y bloquea el demo. **Arrancar ya, en paralelo con M1.** Estimado 8 pts (el mayor), owner = humano.
- Camino de código: M1 (001-004) → M2 (005-011) → M3 (012-013). El e2e NIIF (013) es lo último y requiere TASK-000 cerrado.
- **Regla de fecha:** si al final de M1 (código) TASK-000 no está Done, es la señal temprana de que el demo peligra.

## Dependencias externas (Fase B/C — no bloquean Fase A)
- Publicar a Linear (Fase B): cuenta Linear + OpenSymphony instalado.
- AI PR review (Fase B): GitHub Actions + `AI_REVIEW_API_KEY`.
- Ejecución real (Fase C): levantar la pausa de código.

## Estado
Planning wave **validado manualmente y listo**. Fase A completa. La publicación a Linear (Fase B) y la ejecución (Fase C) requieren cuentas/herramientas externas y —la Fase C— levantar la pausa de código.
