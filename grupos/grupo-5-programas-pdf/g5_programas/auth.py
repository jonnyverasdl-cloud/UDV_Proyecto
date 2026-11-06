"""Revisa quién hizo la solicitud y qué puede hacer dentro de G5.

La identidad y los roles vienen de la sesión que prepara G2, no de los datos
que envía el navegador. Antes de cada operación, G5 comprueba que ese usuario
tenga el permiso necesario.
"""

from dataclasses import dataclass
from typing import Any

from fastapi import Depends

from .errors import ApiError

try:
    from g2_api.routers.auth import obtener_usuario_actual
except ModuleNotFoundError as error:
    if error.name != "g2_api":
        raise

    def obtener_usuario_actual() -> Any:
        raise ApiError(
            503,
            "AUTH_PROVIDER_UNAVAILABLE",
            "La autenticación de G2 no está disponible en esta aplicación.",
        )


@dataclass(frozen=True)
class Actor:
    """Datos del usuario que está usando el sistema."""

    id: int
    name: str
    roles: frozenset[str]


def _value(user: Any, key: str, default: Any = None) -> Any:
    """Busca un dato del usuario, venga como objeto o como diccionario."""
    if isinstance(user, dict):
        return user.get(key, default)
    return getattr(user, key, default)


async def authenticated_actor(
    user: Any = Depends(obtener_usuario_actual),
) -> Actor:
    """Convierte a Actor el usuario autenticado que devuelve G2.

    Deja el ID y los roles en un formato fácil de usar. Si el usuario no tiene
    un ID válido, detiene la solicitud con un error 401.
    """
    if user is None:
        raise ApiError(401, "UNAUTHENTICATED", "Debes iniciar sesión.")

    actor_id = _value(user, "id", _value(user, "user_id"))
    try:
        actor_id = int(actor_id)
    except (TypeError, ValueError):
        raise ApiError(401, "UNAUTHENTICATED", "La sesión no identifica un usuario válido.")
    if actor_id <= 0:
        raise ApiError(401, "UNAUTHENTICATED", "La sesión no identifica un usuario válido.")

    raw_roles = _value(user, "roles", ())
    if isinstance(raw_roles, str):
        roles = frozenset({raw_roles.strip().lower()})
    elif isinstance(raw_roles, dict):
        roles = frozenset(str(role) for role, enabled in raw_roles.items() if enabled)
    else:
        try:
            roles = frozenset(
                str(_value(role, "codigo", _value(role, "name", role))).strip().lower()
                for role in raw_roles
            )
        except TypeError:
            roles = frozenset()

    first_name = _value(user, "nombres", _value(user, "name", ""))
    last_name = _value(user, "apellidos", "")
    name = " ".join(str(part).strip() for part in (first_name, last_name) if part)
    return Actor(id=actor_id, name=name, roles=roles)


ROLE_ALIASES = {
    "author": frozenset({"docente", "teacher", "elaborador"}),
    "coordinator": frozenset({"coordinator", "coordinador-academico", "coordinador_academico"}),
    "reviewer": frozenset({
        "revisor",
        "coordinator",
        "coordinador-academico",
        "coordinador_academico",
        "reviewer",
    }),
    "authority": frozenset({"autoridad", "decanatura", "decano", "dean"}),
}


def require_role(actor: Actor, role: str) -> None:
    """Comprueba que el usuario tenga el rol necesario para esta acción."""
    if not actor.roles.intersection(ROLE_ALIASES[role]):
        raise ApiError(403, "FORBIDDEN", "No tienes permiso para realizar esta acción.")
