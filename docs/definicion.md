# Definición del proyecto (estrella polar) — semilla del PRD

> Cristalizado: 2026-07-02. Proyecto del curso Hardcore AI + pieza de portafolio para roles Senior AI / AI Data Engineer (target: Caseware y similares).
> Nombre: **Ratchet** (elegido 2026-07-02 — un trinquete solo avanza, nunca retrocede).

## Qué es (una frase)
El **SRE de guardia del conocimiento de un RAG**: cuando la confiabilidad cae, **localiza en qué capa está el defecto —datos o config—** recorriendo el lineage (documento→chunk→retrieve→genera), escribe el diagnóstico y lo arregla en la capa correcta: **config** solo si un gate confirma que no empeora; **datos** solo si un humano confirma el parche. Como un trinquete, **la calidad avanza o se mantiene, nunca retrocede por un cambio propio.**

**NO es** "un agente que prueba agentes" (eso es solo la parte de medir). **Es un sistema que MEJORA un asistente RAG** — mide + arregla + re-evalúa. Termómetro + médico.

## El problema (columna vertebral del PRD)
Los buenos equipos SÍ prueban su RAG — pero:
- (a) casi siempre **una vez, a mano, al lanzar** (foto, no proceso);
- (b) el RAG **se degrada después de lanzar** (cambian documentos/normas, cambia la versión del modelo, crece el corpus) → cae en silencio y **nadie re-evalúa**;
- (c) aunque midan, **rara vez auto-mejoran** (un humano ajusta a mano).
→ Resultado: IA no confiable, gasto sin retorno, proyectos cancelados (Gartner: 40% de proyectos agentic cancelados a 2027).

Ejemplo: sale una modificación a la NIIF 16; el RAG sigue citando la versión vieja por meses; nadie lo nota. El loop caza la caída de recall y dispara la corrección.

## Insight / tesis (Ng)
"No optimices un agente. Construye el sistema que mejora a todos los agentes, continuamente." Data-Centric AI + loop de mejora continua.

## JTBD
"Como equipo que corre un asistente RAG en producción, necesito saber si sigue siendo confiable y mejorarlo automáticamente a medida que cambian documentos y modelos, para que no se degrade en silencio ni pierda la confianza."

## Qué valida el proyecto
1. **Producto:** la calidad de un asistente RAG se puede mejorar **automática y seguramente** con el loop medir→diagnosticar→experimentar→decidir — sin ajuste manual, y **sin empeorarla nunca** (el **gate** impide desplegar algo peor; revierte un deploy propio que empeore; ante **deriva del entorno**, re-experimenta). Demo: recall 0.70 → 0.88 movido por el loop + el **gate de no-regresión** + cazar una degradación. *(Detalle calibrado en `specs/prd.md` Seg. 6/8.)*
2. **Carrera:** demuestra ingeniería de IA de producción (evaluación, retrieval, experimentación, observabilidad), no solo llamar a un LLM.

## Cómo se conecta a la realidad
En producción **envuelve** un RAG existente (el de una empresa). Para el demo, Mauricio **construye un RAG de muestra** (el "paciente") sobre **normas contables públicas (NIIF/NIA)** — sabor Caseware, corpus accesible, sin fricción.

## Las piezas
- **Los pacientes:** el asistente RAG que construyes + **uno open-source real** (para no amañar la demo), sobre normas contables.
- **El sistema (lo nuestro):** el loop → **medir**, **localizar el defecto (datos vs config)**, **arreglar en la capa correcta** (config gateado / datos con humano), **decidir/revertir**.

## Por qué el dominio Caseware
Máxima señal para el rol; el dominio (documentos/normas/alto riesgo) justifica de verdad la tesis; corpus público; espeja lo que Caseware necesita para su propio asistente de IA. El loop es horizontal → se pitchea igual a bancos/fintech.

## Pendiente de definir en el PRD
Alcance del MVP (sí/no), métricas objetivo (números meta), no-goals, esbozo de arquitectura.

## Refinamiento por auditoría de panel (2026-07-02)
Un panel de 5 expertos auditó el diagnóstico. Cambios adoptados:
- **El corazón agéntico = diagnóstico causal:** el modelo razona POR QUÉ falla (¿no se recuperó? ¿se recuperó y respondió mal? ¿hueco de corpus?) y **dirige qué perilla probar** → promovido al MVP. Sin esto, el loop es "un for-loop" y la demo cuenta media tesis.
- **Credibilidad:** (1) **segundo paciente real** (RAG open-source de terceros) para que la mejora no salga de un paciente amañado; (2) **golden set ≥50** (no 15) + **significancia** (¿real o ruido?); (3) **recall por span de fuente** (no por chunk) para comparar chunkings de forma justa.
- **Claim angostado (honesto):** *"previene regresiones y diagnostica la causa dirigiendo el fix"* — NO "nada se degrada en silencio".
- **Anti-agentwashing (lo que NO hacemos, a propósito):** nada de multi-agente/debate, ni planificador sofisticado, ni deploy sin humano. Agencia en diagnosticar/planear; el **juez y el gate = código determinista**. Regla: *"el razonamiento propone, la matemática dispone"*.
- **Profundidad > amplitud:** un loop profundo (diagnóstico → dirige → gate → mejora) sobre 1-2 perillas > 7 módulos superficiales.

### Reencuadre del core (panel 2)
De *"afinador de config"* → **"SRE del conocimiento del RAG"**: un **investigador read-only** recorre el lineage, **localiza la capa del defecto (datos vs config)**, escribe un **writeup de incidente** y arregla en la capa correcta (config gateado / datos con humano). Arregla la incoherencia de que el escenario bandera (cambio de norma) **no se puede arreglar** girando perillas. Principio: *"cuanto más lejos del gate, más agente; cuanto más cerca, más determinista"*. Ver `critica.md`.
