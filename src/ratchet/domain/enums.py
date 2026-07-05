"""Enumeraciones del dominio (valores cerrados). Ver functional-design/domain-entities.md."""

from enum import StrEnum


class Capa(StrEnum):
    """Capa del defecto que localiza el investigador (BR-53)."""

    RETRIEVAL_MISS = "retrieval-miss"
    CHUNKING = "chunking"
    FUENTE_VIEJA = "fuente-vieja"
    COBERTURA = "cobertura"
    GENERACION = "generación"


class FixLayer(StrEnum):
    """Capa donde se aplica el fix prescrito (U1: datos)."""

    CONFIG = "config"
    DATOS = "datos"


class GateDecision(StrEnum):
    """Veredicto del gate determinista (BR-31/32/34)."""

    APPROVE = "approve"
    REVERT = "revert"


class ApprovalKind(StrEnum):
    """Los dos gates humanos distintos (BR-61)."""

    CONFIRM_PATCH = "confirm-patch"  # US-13
    APPROVE_DEPLOY = "approve-deploy"  # US-16


class ApprovalDecision(StrEnum):
    PENDING = "pending"
    APPROVE = "approve"
    REJECT = "reject"


class EvalStatus(StrEnum):
    OK = "ok"
    INCONCLUSA = "inconclusa"  # P1: fallo de RAG/entorno


class RunStatus(StrEnum):
    """Rollup grueso del estado de la corrida (además de `RunState` fino)."""

    EN_PROGRESO = "en-progreso"
    COMPLETADA = "completada"
    INCONCLUSA = "inconclusa"


class RunState(StrEnum):
    """Máquina de estados fina del RunRecord (business-logic-model.md Parte C)."""

    NUEVA = "nueva"
    EVALUANDO_BEFORE = "evaluando-before"
    MONITOREANDO = "monitoreando"
    SIN_CAMBIO = "sin-cambio"
    INVESTIGANDO = "investigando"
    INCONCLUSA = "inconclusa"
    WRITEUP_LISTO = "writeup-listo"
    ESPERANDO_CONFIRMACION = "esperando-confirmacion"  # US-13
    DETENIDA_HUMANO = "detenida-humano"
    APLICANDO_PARCHE_REINDEX = "aplicando-parche-reindex"
    EVALUANDO_AFTER = "evaluando-after"
    GATE = "gate"
    REVERTIDA = "revertida"
    ESPERANDO_APROBACION = "esperando-aprobacion"  # US-16
    RECHAZADA = "rechazada"
    PROMOVIDA = "promovida"
    REPORTE = "reporte"
    COMPLETADA = "completada"


# Estados terminales: en todos salvo COMPLETADA/PROMOVIDA el baseline se mantiene (P1/P2).
TERMINAL_STATES: frozenset[RunState] = frozenset(
    {
        RunState.SIN_CAMBIO,
        RunState.COMPLETADA,
        RunState.REVERTIDA,
        RunState.RECHAZADA,
        RunState.DETENIDA_HUMANO,
        RunState.INCONCLUSA,
    }
)


class ReportDecision(StrEnum):
    """Decisión en términos de resultado (≠ GateVerdict.decision)."""

    DEPLOY = "deploy"
    REVERT = "revert"
    PENDING = "pending"
    INCONCLUSA = "inconclusa"


class MonitorSource(StrEnum):
    OWN_DEPLOY = "own-deploy"
    ENV_DRIFT = "env-drift"
    UNKNOWN = "unknown"  # U1: clasificación fina = U3


class Role(StrEnum):
    ENGINEER = "engineer"
    OPERADOR_ADMIN = "operador-admin"
