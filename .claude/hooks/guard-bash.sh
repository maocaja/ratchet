#!/usr/bin/env bash
# PreToolUse hook (matcher: Bash) — bloquea comandos destructivos/irreversibles.
# Defensa en profundidad sobre el deny de permisos (que se evade con variantes).
# Encarna el trinquete: nunca empeorar de forma irreversible sin intención explícita.
set -uo pipefail

payload="$(cat)"
cmd=""
if command -v jq >/dev/null 2>&1; then
  cmd="$(printf '%s' "$payload" | jq -r '.tool_input.command // empty' 2>/dev/null || true)"
fi
[ -z "$cmd" ] && exit 0

deny() {
  jq -n --arg r "$1" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: $r
    }
  }'
  exit 0
}

# 1) Borrado recursivo/forzado o push forzado (irreversibles).
#    Nota: --force-with-lease NO se bloquea (es la variante segura).
if printf '%s' "$cmd" | grep -Eiq 'rm[[:space:]]+-[a-z]*r[a-z]*f|rm[[:space:]]+-[a-z]*f[a-z]*r|sudo[[:space:]]+rm|git[[:space:]]+push[[:space:]].*(--force([[:space:]]|=|$)|[[:space:]]-f([[:space:]]|$))'; then
  deny "Comando destructivo/irreversible bloqueado por policy del repo (trinquete). Si es intencional, córrelo tú fuera del agente."
fi

# 2) SQL destructivo — solo si el comando parece EJECUTARlo (psql/dropdb/alembic), para no
#    dar falsos positivos con grep/echo que solo mencionen las palabras.
if printf '%s' "$cmd" | grep -Eiq '(psql|dropdb|alembic)' \
   && printf '%s' "$cmd" | grep -Eiq 'drop[[:space:]]+(table|database|schema)|truncate[[:space:]]+table|downgrade[[:space:]]+base'; then
  deny "Operación destructiva sobre la base de datos (drop/truncate/downgrade) bloqueada por policy. La verdad (golden set/baseline) es el SPOF #1 — cámbiala tú a mano, con intención."
fi

exit 0
