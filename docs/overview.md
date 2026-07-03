# Overview

> Insumo del PRD (formato curso). Resumen de una página. Completar junto con Mauricio.

## Elevator pitch
El **SRE de guardia del conocimiento de un RAG**: cuando la confiabilidad cae, un **investigador read-only** recorre el lineage (documento→chunk→retrieve→genera), **localiza en qué capa está el defecto —datos o config—** y lo arregla en la capa correcta (config con gate determinista; datos con confirmación humana). Como un trinquete, la calidad avanza o se mantiene, nunca retrocede por un cambio propio. Ver `definicion.md`.

## Problema
El RAG se degrada en silencio tras lanzar; la prueba de-una-sola-vez no lo caza; los equipos miden pero rara vez auto-mejoran. (Detalle en `definicion.md`.)

## Solución (resumen)
Loop: **medir → investigar el lineage y localizar la capa del defecto (datos o config) → arreglar en la capa correcta (experimentar config / proponer parche de datos) → decidir (gate / revertir)**, con aprobación humana en el deploy. El razonamiento propone; el juez y el gate son código determinista.

## Usuarios
TBD (ver `icp.md`).

## Por qué ahora
Ola de agentes en empresas + Gartner (40% cancelados a 2027 por falta de confiabilidad/controles).

## Alcance del demo
RAG de muestra sobre **normas contables públicas (NIIF/NIA)** — sabor Caseware. Detalle de MVP: TBD.
