# Definición del proyecto (estrella polar v2 — enfoque agéntico)

> Reencuadrado: **2026-07-05** tras auditoría de un 2º panel de expertos + investigación de mercado (julio 2026).
> v1 (framing "eval tool") preservada en `definicion-v1-eval.md`. El porqué del pivote, al final.
> Proyecto del curso **Hardcore AI 30X** + pieza de portafolio para roles **Senior/Staff AI Engineer**.
> Nombre: **Ratchet** (un trinquete solo avanza, nunca retrocede — la calidad mejora o se mantiene, nunca empeora por un cambio propio).

## Qué es (una frase)

Ratchet es un **agente de confiabilidad del conocimiento** — *the on-call SRE for your RAG's knowledge*. Cuando un asistente RAG empieza a fallar, Ratchet **recibe un incidente**, **investiga la causa bajo incertidumbre** recorriendo el lineage (documento→chunk→retrieve→genera), **propone la corrección en la capa correcta**, y **actúa solo dentro de un gate determinista que prueba que no empeora**. *El razonamiento propone; la matemática dispone.*

> **Estado hoy vs. destino (honestidad).** Hoy existe el **esqueleto determinista de U1** (recall-por-span, gate + significancia, localizador **por reglas**) + un paciente **stub in-process**. La **agencia real** —investigador multi-hipótesis, RAG externo, demo de contradictorios— es lo que **v2 construye**. Hasta que exista, la palabra **"Agent" describe el destino, no el estado.**

## El cambio de categoría (la decisión estratégica)

| Antes (v1) | Ahora (v2) |
|---|---|
| "RAG Evaluation Tool" | **Knowledge Reliability Agent** |
| corre evals → muestra métricas (dashboard) | **resuelve incidentes de conocimiento** (agente que investiga y actúa) |
| recibe un documento | **recibe un incidente** (`INC-142`: "responde mal a *¿qué es la NIIF 16?*") |
| compite con LangSmith/Ragas/Braintrust (commodity) | ocupa un cruce vacío: agente que investiga+actúa, frenado por determinismo, sobre un RAG que puede no controlar |

**Categoría:** Knowledge Reliability Agent. **Tagline:** *the on-call SRE for your RAG's knowledge.*

## El problema

Los RAG se degradan en silencio (*knowledge drift*): cambia una norma, el corpus queda viejo, crece el corpus, cambia el modelo → la calidad cae y **nadie re-evalúa**. Cuando pasa, alguien tiene que **investigar por qué** (la capa es incierta), **arreglar la capa correcta**, y **probar que no rompió nada**. Hoy: humanos SME lentos, o herramientas de eval que solo **miden y muestran** — no investigan ni actúan. Ejemplo: sale una modificación a la NIIF 16; el RAG cita la versión vieja por meses; nadie lo nota.

## Insight / tesis

Ng: *"No optimices un agente. Construye el sistema que mejora a todos los agentes, continuamente."* Loop tipo Ng: **deploy → observe → investigate → remediate → verify → deploy.** Y el principio que lo hace confiable: **el razonamiento propone, la matemática dispone** — *cuanto más lejos del gate, más agente; cuanto más cerca, más determinista.*

## El corazón agéntico (lo que lo hace un agente de verdad, no teatro)

Ratchet **no** opera sobre casos que un `if` resuelve. Opera sobre **incidentes ambiguos** donde ninguna regla decide sola: **documentos contradictorios · degradación parcial con los docs presentes · causa compuesta (config + datos) · fallo novel.**

El loop (con estado, memoria y autonomía graduada):

```
recibir incidente → observar → generar hipótesis múltiples
→ juntar evidencia decidiendo qué mirar → razonar y rankear
→ decidir (arreglar / juntar más / escalar) → actuar bajo el gate
→ auto-criticar → verificar → cerrar el incidente
```

**El agente vive en `investigator/` (río arriba); nunca en el gate.** Su valor es manejar la ambigüedad que las reglas no pueden.

## Los guardrails (lo que lo diferencia Y lo hace confiable)

- **G1 · Datos con humano:** la corrección de datos requiere confirmación humana; nunca auto-cambia contenido regulado.
- **G2 · Core sin LLM:** el gate y el orquestador jamás llaman al LLM; rutean sobre datos verificados (import-linter, fail-closed). El cerebro LLM está río arriba.
- **G3 · Investigador read-only:** emite un claim verificable `{capa, evidencia}`; `verify_claim` (determinista) lo recomprueba **antes** de cualquier acción.
- **Todo claim del agente es falsificable** por un test determinista. **Recall = código; faithfulness = juez; nunca al revés** (más estricto que el mercado 2026, que usa juez para ambos).

## La prueba de sinceridad (nos obliga a no hacernos trampa)

El demo estrella es **documentos contradictorios con señales en conflicto**: dos versiones de una norma vivas en el corpus, ambas recuperadas. La regla ingenua ("gana la fecha más nueva") **está diseñada para fallar** → el agente *tiene* que razonar sobre múltiples señales que se contradicen (cláusula de derogación, fecha de vigencia, alineación con el golden set). El agente propone qué versión es la vigente; **`verify_claim` lo falsea contra el golden set** (la verdad humana): si su elección no hace correctas las respuestas doradas, el claim falla → reconsidera o **escala**. Casos genuinamente disputados → escalan al humano.

> **La vara:** cuando alguien pregunte *"¿por qué es un agente y no un dashboard con un `if`?"*, este demo es la respuesta. **Si un `if` lo hubiera resuelto, fracasamos y lo decimos.**

## JTBD

"Como equipo que corre un asistente RAG en producción, necesito **investigar y resolver** las caídas de confiabilidad a medida que cambian documentos y modelos —sabiendo la causa y con la garantía de que el arreglo no empeora nada— para que no se degrade en silencio ni pierda la confianza."

## Qué valida el proyecto

1. **Producto:** un agente puede **investigar la causa de un incidente de conocimiento bajo incertidumbre** y remediarlo **de forma segura** — config auto si el gate lo prueba, datos con humano — sin empeorar nunca (gate de no-regresión + auto-revert, con **significancia**).
2. **Carrera:** demuestra la ingeniería que un Staff/Principal AI Engineer debe dominar: **agencia CON guardrails** — la disciplina anti-agentwashing que separa un agente real de un LLM atornillado.

## Las piezas

- **El paciente (externo) — destino:** un RAG **propio, real, corriendo como su propio servicio** (proceso aparte, **BM25 determinista, HTTP**), al que Ratchet se conecta **por afuera** por el adaptador `RagPatientPort` (**ADR-008**). *(Hoy: stub in-process; el servicio externo es net-new, pero reusa la lógica BM25/patch/reindex de `SampleRagPatient` — ~80% ya está.)* Un **2º paciente independiente** (AnythingLLM) llega en **U3** (la prueba anti-circularidad); **MCP** es dirección **enterprise** (fast-follow), no MVP. Demo sobre **normas contables públicas (NIIF/NIA)**. Que corra aparte —no metido dentro de Ratchet— mata la crítica de **acoplamiento**; la de **circularidad** se responde en U3.
- **El agente (lo nuestro) — destino:** el investigador LLM que razona el incidente + el sustrato determinista que lo verifica y lo frena. *(Hoy: `investigator/` es el localizador determinista **por reglas**; el loop de hipótesis/auto-crítica es lo que v2 construye.)*
- **Capacidad graduada por acceso:** en un RAG que controlás → medir + localizar + **arreglar**; en uno que no → medir + localizar + **recomendar** (capability flag `supports_data_ops`).

## Dominio: NIIF en la demo, "conocimiento regulado" en el pitch

- **Demo = NIIF concreto** (corpus ya curado, golden set ≥50 por span). Concreto le gana a abstracto en una demo, siempre.
- **Posicionamiento = conocimiento regulado** (finanzas/legal/compliance), con NIIF como proof point. El loop es horizontal → se pitchea igual a bancos/fintech. Se separan a propósito: no se generaliza la demo; sí el pitch.

## Política de autonomía (el toggle — agencia calibrada por confianza)

- **Modo supervisado (default):** también config pasa por gate humano (aprobar deploy). Modelo de dos gates intacto.
- **Modo autónomo-config:** config auto-deploya si el gate lo prueba **dentro de la cobertura del golden set**, con auto-revert; **datos, siempre humano.** El toggle mismo *demuestra* autonomía graduada. Claim honesto: *"auto-actúa en config dentro de cobertura; fuera de cobertura no reclama seguridad."*

## Manejo del LLM (architecture just-in-time)

El LLM vive detrás de la costura `LlmPort`. **Para el MVP: Anthropic (Claude) directo** — el razonamiento más fuerte, mínima fricción. **Bedrock/Vertex = swap posterior** (camino enterprise) sin tocar el cerebro del agente. El proveedor se decide *cuando duela*, no ahora. El LLM está en el camino crítico → si falla, el agente **escala/marca inconclusa** (P1), nunca crashea. Salida **estructurada** (tool-use) para que el razonamiento sea parseable y verificable. La no-determinación queda acotada a la *propuesta*; la *decisión* es determinista (el gate).

## Lo que reusamos (no empezamos de cero)

Todo lo determinista de U1 (recall-por-span, gate + significancia, sondas, `verify_claim`, monitor, persistencia) → se vuelve **las herramientas, el verificador y la memoria** del agente. El gate determinista es lo que hace al agente **confiable** — el freno que a casi todos los agentes de 2026 les falta (Gartner: *Guardian Agents*).

## Lo que NO hacemos (anti-agentwashing, a propósito)

Nada de **narrar razonamiento sobre decisiones cableadas** · nada de **auto-cambiar datos regulados** · nada de **juez-LLM donde hay verificación determinista** · nada de multi-agente/debate decorativo. El agente propone; la matemática dispone.

---

## Nota del pivote (v1 → v2)

v1 definió Ratchet como *"sistema que mejora un RAG"* y lo construyó como un **esqueleto determinista** (U1 completo, 184 tests) — pero el escenario demo (*fuente-vieja*) se resuelve con una regla, así que **no demostraba agencia real**. La investigación de julio 2026 confirmó que *"evaluar un RAG"* está comoditizado y que el **cruce agente-que-investiga-y-actúa sobre un RAG que no controlás está vacío**. v2 no tira nada: re-centra el proyecto en su **corazón agéntico** (que la propia v1 ya nombraba, línea 45) usando lo determinista como sustrato verificado. El compromiso: **la palabra "Agent" se gana con el demo de contradictorios, o no se usa.** Contexto completo del pivote: `critica.md` (panel 1), **`critica-panel-agentico.md`** (panel 2, agéntico) y **`investigacion-2026.md`** (mercado + técnica, con fuentes).
