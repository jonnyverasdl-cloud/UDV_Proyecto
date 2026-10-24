"""Prepara la ruta para que las pruebas puedan importar el módulo de G5."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GROUP_ROOT = PROJECT_ROOT / "grupos" / "grupo-5-programas-pdf"
sys.path.insert(0, str(GROUP_ROOT))
