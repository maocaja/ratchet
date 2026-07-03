#!/usr/bin/env bash
# PostToolUse hook — corre tras cada Edit/Write.
#   .py → autoformatea (ruff format) + autofix seguro (ruff check --fix); bloquea si quedan errores.
#   .md → valida enlaces relativos .md que podrían estar rotos.
# Los tests (pytest) completos se activan en Construction, con código.
set -uo pipefail

payload="$(cat)"
file=""
if command -v jq >/dev/null 2>&1; then
  file="$(printf '%s' "$payload" | jq -r '.tool_input.file_path // empty' 2>/dev/null || true)"
fi
[ -z "$file" ] && exit 0
[ -f "$file" ] || exit 0

case "$file" in
  *.py)
    command -v ruff >/dev/null 2>&1 || exit 0
    ruff format "$file" >/dev/null 2>&1 || true        # autoformatea
    ruff check --fix "$file" >/dev/null 2>&1 || true   # autofix seguro
    # ¿quedan errores que ruff no puede arreglar solo? Los diagnósticos van a stderr → el modelo los ve.
    if ! ruff check "$file" >&2; then
      echo "❌ ruff: quedan problemas en $file que requieren tu atención." >&2
      exit 2
    fi
    ;;
  *.md)
    grep -oE '\]\(([^)]+\.md)\)' "$file" 2>/dev/null | sed -E 's/\]\(|\)//g' | while read -r link; do
      case "$link" in http*|\#*|"") continue;; esac
      target="$(dirname "$file")/$link"
      [ -f "$target" ] || echo "⚠️  enlace posiblemente roto en $file → $link" >&2
    done
    ;;
esac
exit 0
