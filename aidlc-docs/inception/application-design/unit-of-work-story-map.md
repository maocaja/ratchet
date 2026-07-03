# Mapa Historia → Unidad — Ratchet

## Asignación
| Historia | Unidad | Prioridad | 🎯 NIIF |
|---|---|---|---|
| US-01 Conectar adaptador | U1 | Must | 🎯 |
| US-05 Curar golden set | U1 | Must | 🎯 |
| US-06a Evaluar — recall-por-span | U1 | Must | 🎯 |
| US-07 Fijar baseline | U1 | Must | — |
| US-08 Monitor detecta caída | U1 | Must | 🎯 |
| US-10 Localizar capa del defecto | U1 | Must | 🎯 |
| US-11 Writeup de incidente | U1 | Must | 🎯 |
| US-13 Parche datos + confirmación humana | U1 | Must | 🎯 |
| US-03 Aplicar parche + reindex | U1 | Must | 🎯 |
| US-14 Gate no-regresión + revert | U1 | Must | 🎯 |
| US-16 Aprobación humana (gate P2) | U1 | Must | 🎯 |
| US-17 Reporte antes/después | U1 | Must | 🎯 |
| US-06b Evaluar — faithfulness | U3 | Must (post-skeleton) | — |
| US-02 Aplicar/revertir config | U2 | Must | — |
| US-12 Proponer + experimentar variantes | U2 | Must | — |
| US-04 2º paciente open-source + fallback | U3 | Must | — |
| US-09 Distinguir deriva vs. deploy propio | U3 | Should | — |
| US-15 Revert asimétrico | U3 | Should | — |
| US-18 Definir política de autonomía | U3 | Should | — |

## Validación de cobertura
- **Total historias:** 19 (US-06 partida en US-06a/US-06b). **Asignadas:** 19. **Huérfanas:** 0. ✅
- **U1:** 12 historias (todas Must; 11 marcadas 🎯 + US-07 soporte). Faithfulness NO está en U1 (movido a U3).
- **U2:** 2 historias (Must).
- **U3:** 5 historias (2 Must — US-04, US-06b — + 3 Should).
- **Camino no-negociable (🎯):** completo dentro de U1 → el walking skeleton entrega el escenario NIIF end-to-end de forma autónoma, con **recall-por-span** como métrica (faithfulness llega después).
