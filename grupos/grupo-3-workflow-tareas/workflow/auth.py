"""Autenticación: el usuario sale del token de login del Grupo 2 (nada de X-User / X-Role).

`current_user` hace tres cosas, en este orden:
    1. pide a G2 el usuario del token (`obtener_usuario_actual`; si no hay token válido,
       G2 responde 401),
    2. lo traduce al formato interno {"id", "role", "name", "campus", "unit"},
    3. hace `SET @actor_id` en la conexión para que la auditoría de G1 registre quién
       hizo el cambio.

PENDIENTE: ajustar el import de abajo a la ruta real del código de G2, y revisar
ROLE_MAP / los nombres de campo en `actor_desde_g2` según lo que devuelva su función.
"""
from fastapi import Depends

from .db import set_actor
from .deps import get_conn
from .errors import Unauthorized

try:
    from app.auth import obtener_usuario_actual      # <-- AJUSTAR a la ruta real de G2
except ImportError:                                  # solo pasa fuera del repo completo
    def obtener_usuario_actual():
        raise Unauthorized("El login del Grupo 2 no está disponible en este entorno")

# Nombre del rol en G2 -> nombre del rol en la matriz de G3 (workflow/matrix.py).
ROLE_MAP = {
    "coordinador": "coordinator", "docente": "teacher", "revisor": "reviewer",
    "autoridad": "authority", "sistema": "system",
    "coordinator": "coordinator", "teacher": "teacher", "reviewer": "reviewer",
    "authority": "authority", "system": "system",
}


def _field(raw, *names):
    """Lee un campo de un dict u objeto probando varios nombres."""
    for name in names:
        value = raw.get(name) if isinstance(raw, dict) else getattr(raw, name, None)
        if value is not None:
            return value
    return None


def actor_desde_g2(raw) -> dict:
    uid = _field(raw, "id", "id_usuario", "user_id")
    rol = _field(raw, "role", "rol", "nombre_rol")
    if uid is None or rol is None:
        raise Unauthorized("No se pudo identificar al usuario del token")
    return {"id": int(uid),
            "role": ROLE_MAP.get(str(rol).lower(), str(rol).lower()),
            "name": _field(raw, "name", "nombre"),
            "campus": _field(raw, "campus", "sede"),
            "unit": _field(raw, "unit", "unidad")}


def current_user(raw=Depends(obtener_usuario_actual), conn=Depends(get_conn)) -> dict:
    actor = actor_desde_g2(raw)
    set_actor(conn, actor["id"])        # auditoría de G1: quién hizo el cambio
    return actor
