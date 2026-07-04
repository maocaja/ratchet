# ADR-001: Adaptador hexagonal `RagPatientPort` — el RAG es un sistema externo

*Fecha: 2026-07-04*

## Contexto
Ratchet debe **medir, experimentar y arreglar** un asistente RAG sin reescribir su código, y debe poder validarse contra más de un RAG (el propio de la demo y, más adelante, uno open-source real). El vector store, el chunking y la generación pertenecen al RAG, no a Ratchet. Si el core se acoplara a un proveedor o a un store concreto, cada nuevo "paciente" obligaría a tocar el núcleo, y Ratchet dejaría de ser un sistema que *mejora* un RAG para convertirse en *un* RAG.

## Decisión
El core habla con el RAG objetivo **solo a través del puerto hexagonal `RagPatientPort`** (P5): una interfaz con implementaciones intercambiables por paciente. El RAG se modela como **sistema externo**. Las operaciones de datos (parche + reindex) van tras un **capability-flag** (`supports_data_ops()`, G1) para pacientes que no las soporten.

## Alternativas consideradas
- **Acoplar el RAG dentro del core de Ratchet** — descartada: rompe P5, impide intercambiar pacientes y mezcla la infraestructura del paciente con la del evaluador.
- **Que Ratchet posea el vector store** — descartada: Ratchet *sería* un RAG en vez de mejorar uno; contradice la estrella polar.

## Consecuencias
- ✅ Pacientes intercambiables (propio, open-source) sin tocar el core.
- ✅ Core agnóstico de proveedor; costura lista para separar en servicios al escalar.
- ⚠️ Requiere una implementación de adaptador por paciente.
- ⚠️ La rama de datos depende de `supports_data_ops()`; si es falso, aplica fallback documentado (G1).

## Estado
Aceptado
