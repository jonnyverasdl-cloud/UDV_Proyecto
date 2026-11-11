"""Conecta el módulo G5 con el generador del PDF institucional."""

from .pdf_service import build_pdf as _build_pdf


def build_pdf(program, version, approval):
    """Arma el PDF con la información del programa, la versión y su aprobación."""
    return _build_pdf(program, version, approval)
