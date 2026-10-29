"""Conecta el módulo G5 con el generador del PDF institucional.

El generador está en ``backend.pdf_service``. Esta función permite que el
repositorio de G5 lo use sin tener que conocer dónde está implementado.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.pdf_service import build_pdf as _build_pdf


def build_pdf(program, version, approval):
    """Arma el PDF con la información del programa, la versión y su aprobación."""
    return _build_pdf(program, version, approval)
