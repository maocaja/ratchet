#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["pyyaml"]
# ///
"""Valida el golden set NIIF (TASK-000 / RAT-5) contra sus acceptance criteria.

Uso:  python scripts/validate_golden_set.py    (o: uv run --script scripts/validate_golden_set.py)

Chequea: ≥50 ítems, campos requeridos, offsets que cuadran con el corpus vigente,
≥1 crítico, ≥1 ligado a NIIF 16, y la guía léxica (pregunta comparte vocabulario con el span).
NO valida la corrección contable — esa es tu parte humana (BR-76).
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
GS = ROOT / "seeds" / "golden_set_niif.yaml"
CORPUS_VIGENTE = ROOT / "seeds" / "corpus_vigente"
CORPUS = ROOT / "seeds" / "corpus"
MIN_ITEMS = 50


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s.lower()).strip()


def tokens(s: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", normalize(s)) if len(t) > 3}


def doc_text(doc_id: str) -> str | None:
    for base in (CORPUS_VIGENTE, CORPUS):
        p = base / f"{doc_id}.txt"
        if p.exists():
            return p.read_text(encoding="utf-8")
    return None


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    if not GS.exists():
        print(f"❌ No existe {GS}")
        return 1

    data = yaml.safe_load(GS.read_text(encoding="utf-8")) or {}
    items = data.get("items") or []

    if len(items) < MIN_ITEMS:
        errors.append(f"Solo {len(items)} ítems (se requieren ≥{MIN_ITEMS}).")

    n_critical = 0
    n_niif16 = 0
    seen_ids: set[str] = set()

    for i, it in enumerate(items):
        tag = it.get("item_id", f"#{i}")
        for field in ("item_id", "question", "answer", "gold_span", "critical", "slice"):
            if field not in it:
                errors.append(f"[{tag}] falta campo '{field}'.")
        if it.get("item_id") in seen_ids:
            errors.append(f"[{tag}] item_id duplicado.")
        seen_ids.add(it.get("item_id"))

        if it.get("critical") is True:
            n_critical += 1
        if it.get("slice") == "niif16" or (it.get("gold_span") or {}).get("doc_id") == "niif16":
            n_niif16 += 1

        span = it.get("gold_span") or {}
        doc_id, start, end, text = (span.get(k) for k in ("doc_id", "start", "end", "text"))
        if None in (doc_id, start, end, text):
            errors.append(f"[{tag}] gold_span incompleto.")
            continue
        if not (isinstance(start, int) and isinstance(end, int) and start < end):
            errors.append(f"[{tag}] offsets inválidos (start<end enteros).")
            continue
        if text.strip().startswith("[EJEMPLO"):
            warnings.append(f"[{tag}] gold_span.text es placeholder — reemplazar.")
            continue
        txt = doc_text(doc_id)
        if txt is None:
            errors.append(f"[{tag}] no existe corpus para doc_id '{doc_id}'.")
            continue
        if end > len(txt):
            errors.append(f"[{tag}] end={end} fuera de rango (doc len={len(txt)}).")
            continue
        if normalize(txt[start:end]) != normalize(text):
            errors.append(f"[{tag}] gold_span.text NO coincide con corpus[{start}:{end}].")
        # guía léxica (BM25): la pregunta comparte vocabulario con el span
        if not (tokens(it.get("question", "")) & tokens(text)):
            warnings.append(f"[{tag}] pregunta sin vocabulario común con el span (BM25 fallará).")

    if n_critical == 0:
        errors.append("Ningún ítem con critical: true (se requiere ≥1).")
    if n_niif16 == 0:
        errors.append("Ningún ítem ligado a NIIF 16 (se requiere ≥1 para el escenario).")

    for w in warnings:
        print(f"⚠️  {w}")
    for e in errors:
        print(f"❌ {e}")

    print(
        f"\nResumen: {len(items)} ítems · {n_critical} críticos · {n_niif16} NIIF16 · "
        f"{len(errors)} errores · {len(warnings)} warnings"
    )
    if errors:
        print("→ Golden set NO cumple aún (RAT-5 en progreso).")
        return 1
    print("✅ Golden set cumple los acceptance de RAT-5.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
