# Requirements — Ratchet

> Salida de la fase **Requirements Analysis** (AI-DLC v0.1.8, profundidad *Comprehensive*).
> Insumo principal: `specs/prd.md` + `specs/arquitectura.md`. Decisiones abiertas resueltas en `requirement-verification-questions.md`.
> Trazabilidad: cada requisito referencia su origen en el PRD.

## Intent Analysis
- **User request:** construir Ratchet siguiendo el pipeline AI-DLC (a partir del PRD/arquitectura existentes).
- **Request type:** New Project (greenfield).
- **Scope estimate:** System-wide (loop completo medir→localizar→arreglar→decidir + adaptador + persistencia + interfaz).
- **Complexity estimate:** Complex (dominio regulado, garantías de no-regresión, agencia acotada por verificador, pieza de portafolio).
- **Depth:** Comprehensive.

## Contexto de Negocio
- **Qué es:** el **SRE de guardia del conocimiento de un RAG** — cuando la confiabilidad cae, localiza la capa del defecto (**datos** o **config**), escribe el writeup y arregla en la capa correcta: config solo si un gate confirma que no empeora; datos solo si un humano confirma el parche. *(definicion.md; PRD Seg 1)*
- **JTBD:** "Como equipo que corre un asistente RAG en producción, necesito saber si sigue siendo confiable y mejorarlo automática y seguramente a medida que cambian documentos y modelos, para que no se degrade en silencio ni pierda la confianza." *(PRD Seg 3)*
- **Objetivo del proyecto:** (1) validar que la calidad de un RAG se puede mejorar automática y seguramente con el loop, sin empeorar nunca; (2) demostrar ingeniería de IA de producción (evals, retrieval, experimentación, trazabilidad) — pieza de portafolio para rol Senior AI / AI Data Engineer (target Caseware).
- **Hito:** Demo Day **2026-07-13** (11 días).

## Actores / Personas *(Q6 → ambos; PRD Seg 7)*
- **AI/ML Engineer** — dispara corridas, revisa writeups, aprueba deploys y parches.
- **Operador/Admin** — cura el golden set y define la política (nº de variantes, umbrales).

## Requisitos Funcionales

| ID | Requisito | Prioridad | Origen |
|---|---|---|---|
| **FR-1** | **Adaptador al RAG objetivo:** conectar a un RAG externo; leer su lineage (documento→chunk→retrieve→genera); **aplicar/revertir config**; **aplicar/revertir parche de datos + re-index**. Contrato config+datos, reversible. | Must | Arq Seg 1; P5 |
| **FR-2** | **Golden set & Registro:** versionar golden set (**≥50**, etiquetado por **span de fuente**), baseline, historial de corridas y decisiones, en PostgreSQL. | Must | PRD Seg 10; Q3 |
| **FR-3** | **Evaluación:** computar **recall por span** (determinista) y **faithfulness** (LLM-judge) contra el golden set; anclar la decisión en la métrica determinista. | Must | PRD Seg 10; P3 |
| **FR-4** | **Monitor:** detectar caídas de confiabilidad vs. baseline y disparar el loop; distinguir regresión de un deploy propio vs. deriva del entorno. | Must | PRD Seg 8; P1 |
| **FR-5** | **Investigador / Localizador (read-only):** recorrer el lineage con herramientas y **localizar la capa del defecto** entre 5 (retrieval miss, chunking, fuente vieja, cobertura, generación); escribir un **writeup de incidente**; prescribir la capa de fix. | Must | PRD Seg 5 (CU-4); panel 2 |
| **FR-6** | **Rama de fix CONFIG:** proponer variantes dirigidas por el diagnóstico; experimentarlas (evaluadas por FR-3); **gate de no-regresión**; desplegar el ganador o revertir. | Must | PRD Seg 8; CU-2 |
| **FR-7** | **Rama de fix DATOS:** proponer parche (p. ej. reemplazar doc viejo tras cambio de norma) → **humano confirma** → aplicar + re-index → **gate post-aplicación** (re-eval; revert si empeora). *(MVP: versión delgada = reemplazar doc + re-index.)* | Must | PRD Seg 8; Journey 1-B |
| **FR-8** | **Decisión / Gate (revert-safety):** nunca desplegar algo peor; revert asimétrico (revert para deploy propio; re-experimentar ante deriva). Aplica a **ambas ramas**. | Must | PRD Seg 6; P1 |
| **FR-9** | **Reportes & Aprobación:** writeup de incidente + reporte antes/después; **aprobación humana obligatoria** para avanzar (deploy/parche). | Must | PRD Seg 8; P2 |
| **FR-10** | **Interfaz:** **CLI + API mínima** (FastAPI) para disparar, ver reportes y aprobar. Sin UI web. | Must | Q4; Arq Seg 2 |
| **FR-11** | **Segundo paciente (RAG open-source real):** validar la mejora sobre un RAG de terceros (no solo el construido por Mauricio) para matar el "paciente amañado". **Fallback:** si no integra ~día 7, validar sobre slice held-out con fallas orgánicas y documentar el gap. | Must (con fallback) | Q1; PRD Riesgo #3 |

## Requisitos No Funcionales

| ID | Atributo | Requisito | Táctica | Origen |
|---|---|---|---|---|
| **NFR-1** | Confiabilidad / Corrección | 0 regresiones **no detectadas** (dentro de la cobertura del golden set); decidir con seguridad | Gate de no-regresión + revert automático; anclar en recall determinista; aprobación humana | Arq NFR-1; P1/P3 |
| **NFR-2** | Reproducibilidad / Auditabilidad | Toda decisión re-verificable después | Versionar golden set/config/resultados; recomputar métricas; corridas idempotentes; **audit trail completo** | Arq NFR-2; P4 |
| **NFR-3** | Extensibilidad / Mantenibilidad | Agnóstico al modelo/RAG; roadmap a plataforma | Monolito modular con costuras; **interfaces de adaptador** (RAG/LLM/store por config) | Arq NFR-3; P5 |
| **NFR-4** | Testing (PBT parcial) | Correctitud del núcleo determinista garantizada por property-based testing | PBT sobre: **recall por span, decisión del gate, lógica de revert, serialización de resultados** | Q-PBT (B) |
| **NFR-5** | Seguridad | Baseline **no bloqueante** en el MVP; higiene de secrets | Gestión de secrets/keys LLM (desde Arq SPOF); reactivar extensión en fast-follow productivo | Q-Seguridad (B) |
| **NFR-6** | Portabilidad / Despliegue | Reproducible localmente para Demo Day | **docker-compose** local; diseño de escalado a AWS/IaC **documentado** (no construido) | Q5; Arq Seg 2 |

## Escenarios de Usuario *(Q2 → ambos; jerarquía panel 2)*
- **Escenario HÉROE (datos):** cambia la NIIF 16 → el RAG cita la versión vieja → Monitor caza la caída → Investigador localiza "fuente vieja" (no retrieval) → writeup → humano confirma el parche → reemplazo + re-index → gate re-evalúa → recall recupera (revert si empeora). *(PRD Journey 1-B)*
- **Escenario APOYO (config):** el loop mueve recall 0.70→0.88 vía experimentación dirigida + gate de no-regresión; caza una degradación introducida. *(PRD Journey 1)*
- **Escenario GATE HUMANO (P2):** sin aprobador presente, nada avanza pero **nada se rompe** — cuello de botella deliberado, no fragilidad. *(PRD Journey 3)*

## Criterios de Éxito / Métricas *(Q8 → tal cual PRD Seg 10)*
- **North Star:** puntos de **recall por span de fuente** que el loop gana sobre el baseline.
- **Guardrail:** **0 regresiones no detectadas** (dentro de cobertura del golden set / clases críticas).
- **Significancia:** bootstrap CI / McNemar sobre golden set **≥50**.
- **Localización:** **% de localizaciones correctas ≥ 0.8**.
- **Integridad:** **0** acciones que hagan trampa al golden set.

## Restricciones y Supuestos
- **Tiempo:** 11 días a Demo Day (2026-07-13). Prioridad si se acaba el tiempo *(Q7)*: **el escenario de datos NIIF end-to-end** es el único entregable no-negociable.
- **Stack:** Python-first — FastAPI + PostgreSQL + Job Runner async (monolito modular). LLM Claude/Bedrock. *(Arq Seg 2)*
- **Dominio/corpus:** normas contables públicas NIIF/NIA (sabor Caseware; corpus accesible, PDFs limpios).
- **Supuesto crítico:** el RAG objetivo expone control de config **y** de datos (aplicar/revertir + re-index), reversible. `TBD día 1`: elegir el RAG open-source y validar re-index *(FR-11)*.

## Fuera de Alcance (Won't-Have — a propósito)
Multi-agente/debate · planificador sofisticado (Bayesian/bandit) · deploy sin humano · curación autónoma del golden set · lineage a nivel de embeddings · pipeline OCR completo · UI web · despliegue cloud/IaC construido (fast-follow días 31-60). *(PRD Seg 8; critica.md)*

## Configuración de Extensiones
| Extensión | Habilitada | Alcance | Decidida en |
|---|---|---|---|
| Security Baseline | **No** | Reactivar en fast-follow productivo | Requirements Analysis |
| Property-Based Testing | **Sí (Parcial)** | Núcleo determinista: recall/gate/revert/serialización | Requirements Analysis |

## Resumen
Ratchet es un sistema **greenfield, complejo, de dominio regulado** cuyo corazón es un loop de mejora continua de RAG con **agencia río arriba del gate** y **verificación determinista río abajo**. 11 FRs y 6 NFRs, con el **escenario de datos NIIF** como entregable no-negociable y **0 regresiones no detectadas** como guardrail. Las decisiones abiertas del PRD quedaron resueltas; el único `TBD` de construcción es *cuál* RAG open-source (con fallback definido).
