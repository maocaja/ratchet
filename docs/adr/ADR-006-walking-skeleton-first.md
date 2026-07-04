# ADR-006: Walking-skeleton-first — U1 Camino NIIF end-to-end primero

*Fecha: 2026-07-04*

## Contexto
Ratchet debe demostrar su **tesis completa** —medir → localizar → arreglar → re-evaluar— no piezas sueltas (medir solo es "agentwashing"). Con la fecha de Demo Day fija, el riesgo es construir *ancho* (muchas capacidades a medias) sin una *espina* que funcione de punta a punta. Hay tres unidades candidatas (rama datos, rama config, credibilidad/2º paciente).

## Decisión
Construir **U1 · Camino NIIF (rama de datos) end-to-end primero** como *walking skeleton*: la rebanada vertical no-negociable (golden set → recall-por-span → monitor → localizar "fuente-vieja" → writeup → parche con confirmación humana → aplicar+reindex → gate+revert → aprobación → reporte). Solo **recall-por-span** (faithfulness llega después). Luego U2 (rama config + experimentación) y U3 (2º paciente, faithfulness, robustez).

## Alternativas consideradas
- **Construir por capa técnica** (toda la persistencia, luego toda la API, …) — descartada: acoplamiento vertical; no hay demo funcional hasta el final.
- **Las tres unidades en paralelo** — descartada: dispersa el esfuerzo sin una espina validada; alto riesgo de no tener nada end-to-end para el Demo Day.

## Consecuencias
- ✅ Un demo end-to-end funcionando temprano; la tesis se prueba, no se promete.
- ✅ El camino NIIF resulta **libre-de-LLM y hermético** (recall=código, localización determinista, gate=código) ⇒ e2e reproducible en CI sin red.
- ⚠️ Faithfulness y la rama config quedan fuera de U1 (U3/U2).
- ⚠️ U1 corre sobre un solo paciente (riesgo "paciente amañado"); se aborda con el 2º paciente open-source en U3.

## Estado
Aceptado
