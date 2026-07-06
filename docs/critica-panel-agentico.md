# Auditoría — 2º panel de expertos (enfoque agéntico)

> Fecha: **2026-07-05**. Cargo del panel: *auditar el diagnóstico del pivote y decir cómo el producto se potencia cuando adopta comportamientos agénticos, a julio 2026.*
> Personas construidas para el ejercicio; cada una encarna una escuela real de 2026. Paralelo a `critica.md` (panel 1). Alimentó la estrella polar v2 (`definicion.md`).

## Contexto auditado

Ratchet terminó U1 como **esqueleto determinista** (recall, gate, localizador **por reglas**), pero su escenario demo (*fuente-vieja*) se resuelve con un `if` → **no demostraba agencia real**. Se propuso reencuadrar de "RAG Eval Tool" → **"Knowledge Reliability Agent"** que resuelve **incidentes de conocimiento** ambiguos, con el determinismo como freno.

## Los 5 expertos (audit + cómo potencia la agencia)

1. **Lena Vega — Arquitecta de sistemas agénticos.** La prueba de fuego de un agente es enfrentar un incidente no diseñado y aún así razonar. *Fuente-vieja* no lo hace. **Potenciación:** recolección adaptativa de evidencia (elegir qué sonda correr), hipótesis que compiten rankeadas por evidencia, valor-de-la-información (juntar/proponer/escalar), memoria entre incidentes.
2. **Aditya Ramachandran — Científico de evaluación de retrieval (el escéptico).** El agente es la parte comoditizada; el moat es el **recall determinista + significancia**. **Condición:** cada claim del agente debe ser **falsificable** por un test determinista. **Disidencia:** no sobre-invertir en el agente; un diagnóstico plausible-pero-falso que se cuela por un chequeo débil es peor que una regla que acierta.
3. **Marcus Thorne — Constructor de plataformas LLMOps.** El whitespace (vigilar un RAG ajeno) es real pero angosto; incumbentes podrían agregarlo. **Potenciación:** los incumbentes shipean **dashboards, no agentes que actúan** → cerrar el loop autónomamente dentro del gate es la ventaja. MCP como conexión = relato creíble 2026.
4. **Sofía Marín — Principal AI Engineer / entrevistadora.** El reencuadre agéntico es lo que separa esto de un proyecto de bootcamp. **Potenciación (demo):** razonamiento visible bajo incertidumbre + autonomía graduada; el agente **se equivoca una vez y se auto-corrige**. **Advertencia feroz:** nada de narrar razonamiento sobre decisiones cableadas — un revisor Principal lo huele.
5. **Haruki Ito — IA aplicada a conocimiento regulado.** "Incidente de conocimiento" mapea a cómo las firmas manejan el drift regulatorio; humano-en-el-loop para datos regulados no es opcional → valida G1. **Potenciación:** ensamblado autónomo de evidencia con trazabilidad auditable + correlación con eventos externos (fecha de publicación IASB) → razonar **causa**, no correlación.

## Cruce de fuego (desacuerdos)

- **¿Cuánta agencia?** Vega (más) vs Ramachandran (preservá verificabilidad) → **agencia en investigar; determinismo en el gate; todo claim falsificable.**
- **¿AnythingLLM o RAG propio?** Thorne (poseé el paciente para el loop completo) → resuelto luego en **ADR-008** (RAG propio ahora; AnythingLLM = 2º paciente U3).
- **¿Invertir en el agente?** Marín/Vega (diferencia) vs Ramachandran (comoditizado) → ambos ciertos para públicos distintos: agente **para el curso**; determinismo **para la defensa técnica**.

## Síntesis — comportamientos agénticos que SÍ potencian (rankeados)

1. Recolección adaptativa de evidencia · 2. Hipótesis que compiten + ranking · 3. Autonomía graduada / valor-de-la-información · 4. Auto-crítica antes de proponer (con `verify_claim`) · 5. Correlación con eventos externos · 6. Memoria entre incidentes (stretch).

**Guardrails exigidos (anti-agent-washing):** el agente nunca decide el gate ni computa recall · datos regulados = siempre humano · cada claim falsificable · nada de razonamiento narrado sobre decisiones cableadas.

## Veredicto

La agencia potencia a Ratchet en un lugar específico: **los incidentes ambiguos que las reglas no pueden resolver**, con el gate determinista manteniéndolo confiable. El demo **debe** mostrar un incidente ambiguo (contradictorios) donde el agente se gane el lugar. **Si un `if` lo hubiera resuelto, fracasamos y lo decimos.**

> **Disidencia registrada (Ramachandran):** *"un agente acotado pero genuino > un agente ambicioso que erosiona la verificabilidad."*
