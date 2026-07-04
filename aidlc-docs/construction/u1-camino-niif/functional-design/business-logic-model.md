# Business Logic Model — U1 · Camino NIIF

> **Tecnología-agnóstico.** Flujos E2E del negocio + algoritmos de dominio de la **rama de datos**. Pseudocódigo ilustrativo, no implementación.
> Guardrails: **G1** (data-ops flagged) · **G2** (Orchestrator/Gate sin LLM) · **G3** (investigador read-only, claim verificable).
> Decisiones del plan: Q1 τ=0.8 · Q2 offsets · Q3 CI.lower≥0 · Q4 δ=0.05 · Q5 k=5 · Q7 dos gates · Q8 revert+inconclusa · Q9 idempotencia.

---

# Parte A — Flujos E2E (viaje del negocio de inicio a fin)

## Flujo 1: Curar y fijar el baseline *(US-05, US-07)*
### Descripción
Un humano cura el golden set (≥50, etiquetado por span de fuente) y se fija un baseline versionado como referencia estable.
### Pasos
1. Curar ítems `{question, answer, gold_span, critical, slice}` y registrarlos (`save_golden_set`, BL-3).
2. El sistema valida que todo ítem tiene `gold_span` válido (`len>0`) → crea `GoldenSetVersion` inmutable.
3. Evaluar el RAG contra esa versión → `EvalResult` (recall-por-span, BL-1).
4. Fijar como baseline (`set_baseline`, BL-3) — **rechaza** si `len(items) < 50` o si la eval es `inconclusa`.
### Reglas aplicadas
- BR-21 (inmutabilidad por versión), BR-22 (≥50), BR-23 (≥50 por rebanada), BR-24 (span válido + criticidad), BR-25 (no baseline desde inconclusa).
### Estados posibles
- `SIN_BASELINE → (eval ok ∧ ≥50) → BASELINE_FIJADO`; `(< 50 ∨ inconclusa) → RECHAZADO`.

## Flujo 2: Corrida del loop — rama de datos (escenario NIIF) *(camino no-negociable)*
### Descripción
El asistente cita una NIIF derogada (el corpus quedó con la versión vieja). Ratchet detecta la caída, localiza que el defecto es de **datos** ("fuente-vieja"), propone reemplazar el documento, un humano confirma, se aplica + reindexa, el gate re-evalúa y —si recupera— un humano aprueba; se emite un reporte antes/después. Corre **end-to-end sin LLM** (ver `infrastructure-design §Determinismo`).
### Pasos
1. **Evaluar** baseline vigente → `EvalResult` *before* (recall-por-span, BL-1).
2. **Monitor**: `check` contra baseline → `MonitorSignal` (BL-5). Si no dispara → `SIN_CAMBIO` (fin).
3. **Sondar** el lineage de los ítems afectados → `ProbeResults` deterministas (BL-6).
4. **Localizar** la capa → `Diagnosis {capa="fuente-vieja", fix_layer="datos"}`; `verify_claim` la recomprueba (BL-6, G3). Si no verifica → `INCONCLUSA`.
5. **Writeup** de incidente (síntoma, capa, evidencia, fix prescrito, "ninguna perilla lo arregla → datos") (BL-7).
6. **Proponer parche** de datos: reemplazar el `Document` por su versión vigente (BL-8).
7. **Gate humano #1** — confirmar parche (US-13). Si `reject` → `DETENIDA_HUMANO`, baseline intacto.
8. **Aplicar** parche + **reindex** (US-03). Si `reindex` falla → revert automático + `INCONCLUSA` (Q8).
9. **Re-evaluar** → `EvalResult` *after* (BL-1).
10. **Gate de no-regresión** (BL-4): `approve` solo si `CI.lower(delta) ≥ 0` y **0 regresiones críticas**; si empeora → **revert automático** → `REVERTIDA`.
11. **Gate humano #2** — aprobar deploy (US-16). Si `reject` → revert → `RECHAZADA`.
12. **Reporte** antes/después reproducible (BL-10) → `COMPLETADA`.
### Reglas aplicadas
- Recall: BR-11…BR-16. Localizador (G3): BR-51…BR-58 (BR-55 "fuente-vieja" ⇔ `span_vigente_en_corpus=False"). Parche/confirmación (P2/G1): BR-61…BR-66. Gate (🔒): BR-31…BR-37. Orquestación/idempotencia (G2/NFR-2): BR-71…BR-75.
### Estados posibles
Ver **máquina de estados** (Parte C).

## Flujo 3: Detección de caída y disparo *(US-08)*
### Descripción
Una evaluación cae por debajo del umbral vs. baseline y dispara la investigación.
### Pasos
1. Ejecutar evaluación contra la **misma** `golden_set_version` del baseline (BL-5).
2. Si `status=inconclusa` → **no** dispara (datos no fiables).
3. Si `delta = baseline.recall − current.recall ≥ δ` (default 0.05) → `triggered=True` → entra al Flujo 2.
### Reglas aplicadas
- BR-41 (umbral δ), BR-42 (misma versión), BR-43 (inconclusa no dispara).
### Estados posibles
- `MONITOREANDO → (delta ≥ δ) → INVESTIGANDO`; `(delta < δ) → SIN_CAMBIO`; `(inconclusa) → no dispara`.

---

# Parte B — Algoritmos de dominio (referencia de cada paso)

## BL-1 · Recall-por-span (determinista — C3)
**Regla de oro:** recall = código determinista. Se **recomputa**, nunca "se cree".
```text
cubre(chunk, span) :=            # offsets sobre texto normalizado del mismo doc_id
    if chunk.doc_id != span.doc_id: return 0.0
    inter = max(0, min(chunk.end, span.end) − max(chunk.start, span.start))
    return inter / (span.end − span.start)        # fracción del SPAN cubierta
hit(item, retrieved_topk) := max( cubre(c, item.gold_span) for c in retrieved_topk ) ≥ τ   # τ=0.8
evaluate(rag, gs, k=5, τ=0.8) :=
    per_item = []
    for item in gs.items:
        try: topk = rag.retrieve(item.question, k)
        except RagError: return EvalResult(status="inconclusa")     # P1
        per_item.append( (item.item_id, hit(item, topk), item.critical) )
    recall_span     = mean(h for _,h,_ in per_item)
    critical_recall = mean(h for _,h,c in per_item if c)
    return EvalResult(recall_span, per_item, ci=bootstrap_ci(per_item), critical_recall, status="ok")
```
- Comparable entre chunkings (mide cobertura del *span*); `per_item` pareable por `item_id`.

## BL-2 · Significancia (bootstrap CI)
```text
bootstrap_ci(per_item, B=1000, level=0.95) :=      # seed fijo → reproducible (NFR-2)
    means = [ mean(sample_with_replacement(per_item)) for _ in range(B) ]
    return percentile(means, 2.5), percentile(means, 97.5)
```
- Golden set chico ⇒ CI ancho ⇒ el gate exige más para afirmar mejora (defensa contra ruido).

## BL-3 · Baseline y golden set (C2)
```text
save_golden_set(items) := assert todos con gold_span válido; return GoldenSetVersion inmutable
set_baseline(eval_result) :=
    gs = get_golden_set(eval_result.golden_set_version)
    if len(gs.items) < 50: reject("golden set < 50")
    if eval_result.status != "ok": reject("no baseline desde inconclusa")
    return BaselineVersion congelando eval_result
```

## BL-4 · Gate de no-regresión + revert (C6 — determinista, G2)
```text
evaluate_change(candidate, baseline) :=
    C = {id:(hit,crit) for id,hit,crit in candidate.per_item}
    B = {id:(hit,crit) for id,hit,crit in baseline.eval_result.per_item}
    comunes = keys(C) ∩ keys(B)
    ci_delta = bootstrap_ci([ C[i].hit − B[i].hit for i in comunes ])       # pareado
    reg_crit = count(i in comunes: B[i].critical ∧ B[i].hit=1 ∧ C[i].hit=0) # regresión crítica
    if reg_crit > 0:        return GateVerdict(revert, regressions_criticas=reg_crit)   # 🔒
    if ci_delta.lower ≥ 0:  return GateVerdict(approve, regressions_criticas=0)
    else:                   return GateVerdict(revert,  regressions_criticas=0)
revert_if_worse(handle, verdict) := if verdict.decision==revert: rag.revert_data_patch(handle)
```
- **La matemática dispone:** sin LLM; decide con `per_item` + CI. Revert asimétrico (US-15) = U3.

## BL-5 · Monitor (C7)
```text
check(rag, baseline, δ=0.05) :=
    current = evaluate(rag, gs_of(baseline))          # misma golden_set_version
    if current.status=="inconclusa": return MonitorSignal(triggered=False)
    delta = baseline.recall_span − current.recall_span
    return MonitorSignal(triggered = delta ≥ δ, current, delta, threshold=δ, source="unknown")
```

## BL-6 · Investigador: localizar (C4 — read-only, G3)
```text
probe(item) := ProbeResults(span_indexado, span_en_topk, fronteras_de_chunk,
                            span_vigente_en_corpus, respuesta_usa_span)
# respuesta_usa_span = containment textual (subcadena normalizada), NO faithfulness (U3).
localize_rules(pr) :=                                 # deterministas, orden de prioridad ↓
    if not pr.span_vigente_en_corpus:  return capa="fuente-vieja", fix="datos"      # ← NIIF
    if not pr.span_indexado:           return capa="cobertura",   fix=UNDERSPECIFIED # (U2)
    if pr.span_indexado ∧ ¬pr.span_en_topk ∧ pr.fronteras_de_chunk.split: return "chunking","config"
    if pr.span_indexado ∧ ¬pr.span_en_topk: return "retrieval-miss","config"
    if pr.span_en_topk ∧ ¬pr.respuesta_usa_span: return "generación","config"
    else: AMBIGUO → Localizer(LLM) prioriza, SIN inventar capa fuera del enum
localize(pr) := dx=localize_rules(pr); dx.verified=verify_claim(dx); return dx
verify_claim(dx) := for probe_id in dx.evidencia: assert re-sonda == mismo hecho; return all_consistent
```
- **NIIF:** `span_vigente_en_corpus=False` ⇒ "fuente-vieja" ⇒ datos. Ninguna perilla lo arregla.

## BL-7 · Writeup (C4/C8, read-only)
```text
write_incident(dx, pr, signal) := Writeup(sintoma, capa_localizada=dx.capa, evidencia=dx.evidencia,
    fix_prescrito="reemplazar Document {doc_id} por su versión vigente (NIIF 16)",
    conclusion="ninguna perilla de config lo arregla → capa de datos")   # US-11
```

## BL-8 · Parche de datos + confirmación humana (C8→C1, US-13→US-03)
```text
propose_patch(writeup) := Patch(doc_id, new_content=version_vigente, rationale=writeup.fix_prescrito)
req1 = request_approval(kind="confirm-patch", proposal=patch)
if req1.decision != approve: run.status="detenida-por-humano"; mantener baseline; STOP     # US-13
apply_data_patch_flow(patch) :=
    if not rag.supports_data_ops(): mark_unavailable + fallback (G1)     # U1: paciente propio SÍ soporta
    handle = rag.apply_data_patch(patch)
    try: rag.reindex()
    except ReindexError: rag.revert_data_patch(handle); run.status="inconclusa"; STOP   # Q8
    return handle
```

## BL-9 · LoopOrchestrator — secuencia determinista (C9, G2)
**No contiene `LLM.call()`.** Rutea solo sobre datos deterministas (scores, claim ya verificado, veredicto).
```text
run_loop(rag, gs) :=
    before = evaluate(rag, gs)                                    # BL-1
    signal = Monitor.check(rag, baseline)                         # BL-5
    if not signal.triggered: return Report(decision="sin-cambio", before)
    pr = { item: probe(item) for item in ítems_fallidos(signal) } # BL-6
    dx = Investigator.localize(pr)                                # claim verificado
    if not dx.verified: run.status="inconclusa"; return Report(inconclusa)
    writeup = Investigator.write_incident(dx, pr, signal)         # BL-7
    route(dx.fix_layer):
      datos:                                                      # ← rama U1
        patch = propose_patch(writeup)                            # BL-8
        if not human_confirm(US-13): return Report(decision="detenida", writeup)
        handle = apply_data_patch_flow(patch)                     # US-03
        after  = evaluate(rag, gs); verdict = Gate.evaluate_change(after, baseline)   # BL-1, BL-4
        Gate.revert_if_worse(handle, verdict)
        if verdict.decision==approve:
            if human_approve(US-16): promote()
            else: rag.revert_data_patch(handle)
      config: → (U2, fuera de alcance)
    return Reporter.build_report(run)                             # BL-10
```

## BL-10 · Reporte antes/después (C8)
```text
build_report(run) := Report(recall_before, recall_after, delta, ci_delta, change=resumen(run.patch),
    writeup=run.writeup, decision=map_decision(run), reproducible_from=StateRef(...))  # §P-1, NFR-2
map_decision(run) :=                                             # {approve,revert} ≠ Report.decision
    if run.status=="inconclusa": return "inconclusa"
    if run.verdict.decision=="revert": return "revert"
    if run.verdict.decision=="approve": return "deploy" if aprobado_humano(run,US-16) else "pending"
```

---

# Parte C — Máquina de estados de `RunRecord`

```text
                         ┌────────────── inconclusa (fallo RAG/reindex, P1) ─────────────┐
                         │                                                                ▼
NUEVA → EVALUANDO_BEFORE → MONITOREANDO ──(no dispara)──────────────────────────────→ SIN_CAMBIO
                                   │(dispara)
                                   ▼
                              INVESTIGANDO ──(¬verified)──────────────────────────────→ INCONCLUSA
                                   │(claim verificado)
                                   ▼
                              WRITEUP_LISTO
                                   │ route=datos
                                   ▼
                         ESPERANDO_CONFIRMACION (US-13) ──(reject)──────────────────→ DETENIDA_HUMANO
                                   │(approve)
                                   ▼
                          APLICANDO_PARCHE+REINDEX ──(reindex falla)→ revert ───────→ INCONCLUSA
                                   │(ok)
                                   ▼
                              EVALUANDO_AFTER
                                   │
                                   ▼
                              GATE ──(revert: empeora / regresión crítica)──→ revert → REVERTIDA
                                   │(approve: no empeora con CI)
                                   ▼
                         ESPERANDO_APROBACION (US-16) ──(reject)──→ revert ─────────→ RECHAZADA
                                   │(approve)
                                   ▼
                               PROMOVIDA → REPORTE → COMPLETADA
```
- Terminales: `SIN_CAMBIO`, `COMPLETADA`, `REVERTIDA`, `RECHAZADA`, `DETENIDA_HUMANO`, `INCONCLUSA`.
- En todo terminal salvo `COMPLETADA/PROMOVIDA`: **el baseline se mantiene intacto** (P1/P2).
