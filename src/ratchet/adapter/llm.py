"""LlmPort / cliente LLM.

Blanco PROHIBIDO del contrato import-linter G2: ni gate/ ni orchestrator/
pueden importar este modulo. Vive rio arriba (investigator/).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LlmPort(Protocol):
    """Puerto minimo para clientes LLM usados fuera de gate/orchestrator."""

    def complete(self, prompt: str) -> str:
        """Devuelve una completacion para `prompt`."""
