#!/usr/bin/env bash
# PostToolUse hook — corre tras cada Edit/Write.
# HOY: lint de Python (ruff) cuando exista .py; validación ligera de enlaces Markdown.
# Los tests (pytest) completos se activan en Estación 5, con código.
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
    if command -v ruff >/dev/null 2>&1; then
      if ! ruff check "$file"; then
        echo "❌ ruff falló en $file — corrige antes de continuar." >&2
        exit 2
      fi
    fi
    ;;
  *.md)
    # Chequeo ligero de enlaces relativos a .md que podrían estar rotos.
    grep -oE '\]\(([^)]+\.md)\)' "$file" 2>/dev/null | sed -E 's/\]\(|\)//g' | while read -r link; do
      case "$link" in http*|\#*|"") continue;; esac
      target="$(dirname "$file")/$link"
      [ -f "$target" ] || echo "⚠️  enlace posiblemente roto en $file → $link" >&2
    done
    ;;
esac
exit 0
