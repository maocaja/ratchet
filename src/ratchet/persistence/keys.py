"""Serialización canónica de la clave de estado (§P-1) para idempotencia y UNIQUE."""

from __future__ import annotations

import json

from ratchet.domain import StateRef


def state_key_str(state_ref: StateRef) -> str:
    """String canónico y estable de `StateRef.key()` (§P-1).

    Es la clave de idempotencia del `RunRecord` (BR-73) y la columna `UNIQUE` en Postgres.
    El `seed` NO entra (la reproducibilidad bit-exacta va aparte, `ReproKey`).
    """
    golden_set_version, config_hash, corpus_hash, patch_hash, (k, tau) = state_ref.key()
    return json.dumps(
        [golden_set_version, config_hash, corpus_hash, patch_hash, [k, tau]],
        separators=(",", ":"),
        ensure_ascii=False,
    )
