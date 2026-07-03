# Servicios y Orquestación — Ratchet

## Servicio principal · LoopOrchestrator
- **Responsabilidad:** ejecutar el loop de mejora continua como un **flujo de control determinista** y auditable.
- **Restricción de diseño (G2):** el orquestador **no llama al LLM**. Rutea únicamente sobre **datos deterministas**: scores del Evaluator, claim ya verificado (`verify_claim`), veredicto del Gate. La agencia LLM vive río arriba (Investigator.Localizer, Experimenter.propose_variants) y devuelve estructuras.
- **Por qué:** sirve P4 (auditable) y "cerca del gate = determinista / la matemática dispone".

### Secuencia orquestada (medir → localizar → arreglar → gate → reportar)
```
1. Monitor.check(rag, baseline)
     └─ si no hay caída → fin (nada que hacer)
2. Investigator: ProbeToolkit (deterministas) → Localizer.localize (LLM) → Diagnosis {capa, evidencia}
3. Investigator.verify_claim(Diagnosis)          # G3: re-verifica el claim antes de actuar
4. route(Diagnosis.capa):
   ├─ capa = config:
   │     Experimenter.propose_variants (LLM, dirigido) → run_experiment (Evaluator) → EvalResult[]
   │     Gate.evaluate_change(mejor_variante, baseline) → GateVerdict
   │     Reporter.request_approval → (aprueba) RagAdapter.apply_config
   │
   └─ capa = datos (fuente-vieja/cobertura):
         Investigator propone Patch → Reporter.request_approval   # humano confirma ANTES de aplicar
         (aprueba) RagAdapter.apply_data_patch + reindex          # requiere supports_data_ops (G1)
         Gate.evaluate_change(post_parche, baseline) → GateVerdict
5. Gate.revert_if_worse(handle, verdict)          # aplica a AMBAS ramas (P1)
6. Reporter.build_report(run)                     # antes/después, reproducible
7. GoldenSetRegistry.record_run + record_decision + save_writeup
```

## Servicios de soporte
| Servicio | Responsabilidad | Notas |
|---|---|---|
| **EvaluationService** (envuelve C3) | correr evals reproducibles contra golden set versionado | ancla decisión en recall determinista |
| **AdapterRegistry** (resuelve C1) | seleccionar la implementación de `RagPatientPort` por paciente | P5; expone `supports_data_ops` (G1) |
| **ApprovalService** (parte de C8) | gestionar el gate humano (P2) | si no hay aprobador → mantiene baseline, nada se rompe |
| **PersistenceService** (C12) | repos + migraciones + idempotencia | NFR-2 |

## Patrones de orquestación
- **Orquestación explícita** (no coreografía por eventos): flujo visible y auditable en un solo lugar. *(Descartado B por implícito; ver plan Q3.)*
- **Ejecución:** el LoopOrchestrator encola las partes largas (experimentos) en el **JobRunner** (skeleton síncrono; endurecer a cola real).
- **Puntos de control humano (P2):** exactamente dos —confirmar parche de datos (antes de aplicar) y aprobar deploy tras el gate—; ambos vía ApprovalService.
- **Fronteras de agencia (resumen):**
  - Río arriba del gate (LLM permitido): `Localizer.localize`, `Experimenter.propose_variants`, `write_incident`.
  - Río abajo (solo determinista): `verify_claim`, `Gate.*`, `LoopOrchestrator` routing, `recall_por_span`.
