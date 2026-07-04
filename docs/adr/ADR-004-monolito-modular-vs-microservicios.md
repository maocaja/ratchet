# ADR-004: Monolito modular para el MVP (no microservicios)

*Fecha: 2026-07-04*

## Contexto
Ratchet es a la vez proyecto del curso (Demo Day: 13 jul 2026) y pieza de portafolio para roles Senior AI Engineer (target Caseware, cuyos JD mencionan patrones event-driven/serverless). Hay tensión entre **mostrar arquitectura enterprise** y **entregar algo que funcione end-to-end a tiempo**. La Regla #1 de arquitectura del proyecto es "simplicidad sobre complejidad".

## Decisión
El **MVP es un monolito modular en Python**, un solo desplegable, con **costuras claras** entre módulos (paquetes en `src/ratchet/<módulo>/`, fronteras por interfaz). El **escalado enterprise** (gateway NestJS, cola SQS/EventBridge, workers Lambda/EKS, IaC Terraform/CDK, observabilidad LangFuse) se **documenta** como roadmap fast-follow **pero NO se construye** en el MVP.

## Alternativas consideradas
- **Microservicios / event-driven desde el día 1** — descartada: complejidad operativa alta sobre un skeleton aún no validado end-to-end; contradice la Regla #1 y arriesga el Demo Day.
- **Script monolítico sin costuras** — descartada: sin fronteras internas, separar en servicios después sería una reescritura, no una extracción.

## Consecuencias
- ✅ Camino más corto a un demo end-to-end; simplicidad de desarrollo y despliegue (docker-compose app + Postgres).
- ✅ Las costuras (adaptadores, puertos) permiten extraer servicios luego sin tocar el core.
- ✅ El escalado enterprise queda **documentado y honesto**, alineado a los JD, sin fingir que está construido.
- ⚠️ El monolito de proceso único es un SPOF (mitigado: stateless + estado en Postgres → reinicio rápido; multi-instancia = endurecer).

## Estado
Aceptado
