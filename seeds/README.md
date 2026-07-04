# Datos de curación — TASK-000 / RAT-5

> **La verdad la define un humano (BR-76).** Estos archivos son la **materia prima humana** de U1 que un agente de código NO puede inventar. Los ejemplos de aquí son **placeholders a validar/reemplazar** con contenido NIIF real.

## Qué hay que producir (acceptance de RAT-5)
1. **`golden_set_niif.yaml`** — **≥50 ítems** válidos, cada uno con `{question, answer, gold_span=(doc_id,start,end,text), critical, slice}`. ≥1 crítico, ≥1 ligado a NIIF 16. Dimensionado por rebanada (≥50 por rebanada de la que se afirme algo).
2. **`corpus/`** — documentos fuente NIIF/NIA en **texto plano** (estado inicial del corpus).
3. **`corpus_vigente/`** — la **versión vigente** de los docs que se van a parchar (lo que Ratchet aplicará).

## El mecanismo del escenario NIIF 16
```
Estado inicial:  corpus/niif16.txt      = versión VIEJA (derogada)  → el RAG cita lo viejo
Golden set:      el gold_span apunta al texto VIGENTE (correcto)
Resultado:       span_vigente_en_corpus = False  → recall cae → "fuente-vieja"
El parche:       reemplaza corpus/niif16.txt por corpus_vigente/niif16.txt  → recall recupera
```
→ Por eso necesitas **el par vieja/nueva** de NIIF 16: la vieja en `corpus/`, la vigente en `corpus_vigente/`.

## Guía de curación (retriever léxico BM25)
- Como el RAG usa **BM25** (coincidencia de palabras), **las preguntas deben compartir vocabulario con el texto del `gold_span`**. Si preguntas con sinónimos ausentes en la fuente, el recall sale artificialmente bajo.
- Los **offsets** (`start`, `end`) son posiciones de carácter **reales** sobre `corpus/<doc_id>.txt` — deben coincidir exactamente con `gold_span.text`.

## Cómo validar lo que curas
```
python scripts/validate_golden_set.py
```
Verifica: ≥50 ítems, campos requeridos, offsets que cuadran con el corpus, ≥1 crítico, ≥1 NIIF 16, y la alineación léxica pregunta↔span.
