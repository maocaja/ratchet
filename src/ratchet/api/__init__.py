"""C10 superficie FastAPI + CLI Typer (disparar, reportar, aprobar).

`create_app` (FastAPI) y el CLI Typer (`ratchet.api.cli`) espejan los 3 verbos. El render HTML
del reporte vive en `ratchet.api.html`. Se importan perezosamente para no medir el baseline al
importar el paquete.
"""

from ratchet.api.html import render_report_html
from ratchet.api.service import ReportService

__all__ = ["ReportService", "render_report_html"]
