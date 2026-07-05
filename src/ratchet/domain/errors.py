"""Excepciones del dominio (vocabulario compartido; sin dependencias)."""

from __future__ import annotations


class RagError(RuntimeError):
    """Fallo operacional del RAG paciente (entorno/red/índice).

    Vive en el dominio (no en el adaptador) para que evaluador y adaptador compartan el
    vocabulario sin acoplarse entre sí. El evaluador captura SOLO este tipo para degradar
    la corrida a INCONCLUSA (P1); cualquier otra excepción (bug propio) se propaga.
    """


class DataOpError(RuntimeError):
    """Fallo en una operación de datos del RAG (apply_data_patch/reindex atómico — BR-64/65).

    Vocabulario de dominio: el orquestador captura SOLO este tipo para degradar a INCONCLUSA
    (con revert automático); un bug propio se propaga en vez de enmascararse.
    """
