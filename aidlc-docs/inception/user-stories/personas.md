# Personas — Ratchet

## Persona 1 — Andrés, AI/ML Engineer *(usuario primario)*
- **Rol:** ingeniero que corre uno o varios asistentes RAG en producción.
- **Objetivos:** saber si el RAG sigue confiable; mejorarlo sin romperlo; tener evidencia medible para stakeholders; entender **por qué** falla, no solo que falla.
- **Motivaciones:** confianza en el sistema, no vivir apagando incendios, demostrar rigor de ingeniería.
- **Frustraciones:** el RAG se degrada en silencio tras un cambio de norma/modelo; hoy afina a mano; los dashboards dicen "algo bajó" pero no la causa ni la capa.
- **Contexto técnico:** cómodo con CLI/API, Python, métricas de retrieval; no quiere una caja negra que despliegue sola.
- **Interacción con Ratchet:** dispara corridas, revisa writeups de incidente, **aprueba/rechaza** deploys y parches (gate humano).

## Persona 2 — Carolina, Operador/Admin *(gobierno del sistema)*
- **Rol:** responsable de la calidad del conjunto de evaluación y de la política de autonomía.
- **Objetivos:** que el golden set sea representativo y esté versionado; controlar cuánta autonomía tiene el loop (nº de variantes, umbrales); poder auditar toda decisión.
- **Motivaciones:** que las decisiones automáticas sean confiables y trazables; evitar "garbage in".
- **Frustraciones:** un golden set corrupto o sesgado envenena todo en silencio; autonomía sin auditoría es inaceptable en dominio regulado.
- **Contexto técnico:** conoce el dominio (normas contables), define criterios de aceptación; menos foco en código, más en gobierno y datos.
- **Interacción con Ratchet:** cura y versiona el golden set, define la política, revisa el audit trail.
