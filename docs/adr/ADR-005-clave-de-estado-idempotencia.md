# ADR-005: Clave de estado canónica + idempotencia (dueño único = NFR Design)

*Fecha: 2026-07-04*

## Contexto
La reproducibilidad/auditabilidad (NFR-2) exige poder **recomputar** una decisión y que las corridas sean **idempotentes**. El disparador de U1 es la **deriva del corpus** (una NIIF derogada ⇒ documento viejo). Durante el diseño, la tupla literal de la clave de estado se fijó por error en el **Functional Design** (business rules), y al ascenderla (3→4→5 componentes) apareció *drift* entre artefactos: el mismo dato vivía duplicado en niveles con dueños distintos.

## Decisión
Se define una **clave de estado canónica** con **un solo dueño**: `nfr-design-patterns.md §P-1`.
`StateKey = (golden_set_version, config_hash, corpus_hash, patch_hash, eval_params=(k,τ))`; la reproducibilidad bit-exacta del recall añade `seed`. Se **enforcea con `UNIQUE(StateKey)` en Postgres**. El `corpus_hash` lo computa **Ratchet** (no el RAG) vía `RagPatientPort.corpus_fingerprint()` sobre contenido crudo, normalizado con el **mismo `normalize()`** que usa el recall. Los literales del Functional Design se **bajaron a referencia** a §P-1.

## Alternativas consideradas
- **Tupla de 3 sin `corpus_hash`** — descartada: dos señales antes/después de la deriva (con `patch_hash=null`) colisionarían y se deduplicaría una señal real.
- **Meter `k/τ` dentro de `config_hash`** — descartada: `config_hash` es config del *RAG*; `k/τ` son knobs de *Ratchet*. Se mantienen explícitos como `eval_params`.
- **Fijar la tupla en el Functional Design** — descartada: nivel equivocado; causó el drift (erratum registrado en `audit.md`).

## Consecuencias
- ✅ Reproducibilidad e idempotencia reales, probadas contra Postgres.
- ✅ Dueño único ⇒ no vuelve a haber drift; el resto de artefactos referencian §P-1.
- ⚠️ Requiere que el puerto exponga `corpus_fingerprint()`.
- ⚠️ La garantía bit-exacta del recall exige que el `retrieve()` del RAG sea determinista para un índice fijo (precondición P-2).

## Estado
Aceptado (erratum de nivel de propiedad cerrado en NFR Design)
