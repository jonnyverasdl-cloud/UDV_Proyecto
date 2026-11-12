"""Autenticación: el usuario sale del token de login del Grupo 2 (nada de X-User / X-Role).

`current_user` (la única dependencia de usuario) hace tres cosas, en este orden:
    1. pide a G2 el usuario del token (`obtener_usuario_actual`; sin token válido G2 responde 401).
       G2 devuelve un objeto `Usuario` (no un dict): `usuario.id` y `usuario.roles`, y cada
       rol tiene su `codigo`,
    2. lo traduce al formato interno {"id", "role", "roles", "name", "campus", "unit"},
    3. hace `SET @actor_id` en la conexión para que la auditoría de G1 registre quién hizo
       el cambio.
Un usuario puede tener varios roles (p. ej. revisor y docente): `roles` los trae todos y
`role` es el primero, por compatibilidad con el código que usa un solo rol.
"""
from fastapi import Depends

from .db import set_actor
from .deps import get_conn
from .errors import Unauthorized

try:
    from g2_api.routers.auth import obtener_usuario_actual
except ImportError:                                  # solo pasa fuera del repo completo
    def obtener_usuario_actual():
        raise Unauthorized("El login del Grupo 2 no está disponible en este entorno")

# Código de rol (G1/G2) -> rol de la matriz de G3 (workflow/matrix.py).
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


def _role_codes(raw) -> list:
    """Códigos de rol del usuario (en orden, sin repetir). Cada rol es un objeto con `codigo`
    (o, por tolerancia, un dict o un texto)."""
    roles = _field(raw, "roles") or []
    codes = []
    for r in roles:
        code = r if isinstance(r, str) else _field(r, "codigo", "code")
        if code:
            code = ROLE_MAP.get(str(code).lower(), str(code).lower())
            if code not in codes:
                codes.append(code)
    return codes


def actor_desde_g2(raw) -> dict:
    uid = _field(raw, "id", "id_usuario", "user_id")
    roles = _role_codes(raw)
    if uid is None or not roles:
        raise Unauthorized("No se pudo identificar al usuario del token")
    nombres, apellidos = _field(raw, "nombres"), _field(raw, "apellidos")
    name = _field(raw, "name", "nombre") or " ".join(x for x in (nombres, apellidos) if x) or None
    return {"id": int(uid), "role": roles[0], "roles": roles, "name": name,
            "campus": _field(raw, "campus", "sede"), "unit": _field(raw, "unit", "unidad")}


def current_user(raw=Depends(obtener_usuario_actual), conn=Depends(get_conn)) -> dict:
    actor = actor_desde_g2(raw)
    set_actor(conn, actor["id"])
    return actor