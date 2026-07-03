# Reglas de Evaluación (el corazón de Ratchet)

Regla de oro (P3): **el razonamiento propone, la matemática dispone.**

- **Recall = código determinista. Faithfulness = LLM-judge. NUNCA al revés.** No decidir con solo el juez donde hay verificación determinista.
- **Recall por span de fuente** (no por chunk): un chunk "acierta" si **cubre el span dorado** → así es comparable entre chunkings.
- **Golden set:** etiquetado por span, con **clase crítica** marcada. Mínimo **≥50**, y dimensionado **por rebanada/estrato** (no por nº de documentos) — cada rebanada de la que se haga una afirmación necesita su propio mínimo.
- **Significancia antes de afirmar mejora:** bootstrap CI / test pareado (McNemar). Reportar siempre **con margen de error**. Golden set chico = ruido → held-out es defensa parcial.
- **Guardrail 🔒:** 0 regresiones no detectadas **dentro de la cobertura**. Un falso negativo en clase crítica = incidente.
- **Gate de no-regresión:** ningún cambio avanza si no supera al baseline con significancia. Humano aprueba lo que AVANZA (P2); revertir a lo seguro es automático.
- **Localizador (G3):** el investigador es **read-only** — emite un claim verificable `{capa, evidencia}`, NO ejecuta la acción. La corrección de datos requiere **confirmación humana**.
- **Verdad = golden set, no la IA.** Ratchet enforcea coincidir con la verdad vigente que un humano definió; no la inventa (ver `docs/critica.md`, escenario de versiones contradictorias).
