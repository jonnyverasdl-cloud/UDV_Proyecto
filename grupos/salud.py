"""Estado técnico del servicio para GET /api/v1/health (escenario G6-34).

No depende del framework web. Nunca devuelve detalles internos: si una
verificación falla, solo informa "error" (RNF 06 y escenario G6-36).
"""

import logging
import os
import time
import re
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any, Callable

registro = logging.getLogger(__name__)

NOMBRE_SERVICIO = "udv-workflow-docente"
RESULTADOS_VALIDOS = {"ok", "error", "not_configured"}

Verificacion = Callable[[], str]


def verificar_base_de_datos() -> str:
    """Consulta mínima a MySQL con la conexión compartida del G2."""
    from g2_api import config  # noqa: F401  (carga el .env antes de leer la variable)
    from g2_api.database import probar_conexion

    if not os.getenv("DATABASE_URL"):
        return "not_configured"
    return "ok" if probar_conexion() else "error"


VERIFICACIONES_PREDETERMINADAS: dict[str, Verificacion] = {
    "database": verificar_base_de_datos,
}

# Railway pone el commit desplegado en RAILWAY_GIT_COMMIT_SHA; en otro lugar se
# puede definir APP_COMMIT. Así se sabe exactamente qué código corre (G6-39).
VARIABLES_COMMIT = ("APP_COMMIT", "RAILWAY_GIT_COMMIT_SHA")


def commit_desplegado(variables: Mapping[str, str]) -> str | None:
    for nombre in VARIABLES_COMMIT:
        valor = variables.get(nombre, "").strip().lower()
        if re.fullmatch(r"[0-9a-f]{7,40}", valor):
            return valor[:7]
    return None


def estado_del_servicio(*, iniciado_en: float, entorno: str, version: str,
                        commit: str | None = None,
                        verificaciones: dict[str, Verificacion] | None = None
                        ) -> dict[str, Any]:
    if verificaciones is None:
        verificaciones = VERIFICACIONES_PREDETERMINADAS

    resultados: dict[str, str] = {}
    for nombre, verificar in verificaciones.items():
        try:
            resultado = verificar()
        except Exception as error:  # noqa: BLE001 - se reporta sin detalles
            registro.warning("La verificación de salud '%s' falló (%s).",
                             nombre, type(error).__name__)
            resultado = "error"
        resultados[nombre] = resultado if resultado in RESULTADOS_VALIDOS else "error"

    return {
        "status": "degraded" if "error" in resultados.values() else "ok",
        "service": NOMBRE_SERVICIO,
        "version": version,
        "environment": entorno,
        "commit": commit,
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "uptime_seconds": int(time.monotonic() - iniciado_en),
        "checks": resultados,
    }
