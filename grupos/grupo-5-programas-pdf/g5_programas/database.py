"""Conexión con MySQL y manejo de las sesiones que usa G5.

G5 usa las tablas y reglas de G1. Aquí se abre una sesión por solicitud, se
identifica quién hizo cada cambio y se convierten los errores de MySQL en
respuestas que la API puede mostrar.
"""

import logging
import os
import re
from functools import lru_cache

from fastapi import Request
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from .auth import Actor
from .errors import ApiError

log = logging.getLogger("udv.g5.database")


@lru_cache(maxsize=1)
def _session_factory():
    """Prepara las sesiones de la base de datos usando DATABASE_URL."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ApiError(503, "DATABASE_UNAVAILABLE", "La base de datos no está configurada.")
    engine = create_engine(url, pool_pre_ping=True, pool_recycle=1800)
    return sessionmaker(bind=engine, expire_on_commit=False)


def get_session(request: Request):
    """Abre una sesión para la solicitud y la cierra al terminar."""
    factory = request.app.state.database_session_factory or _session_factory
    session = factory()
    try:
        yield session
    except SQLAlchemyError as exc:
        session.rollback()
        raise translate_database_error(exc)
    finally:
        session.close()


def set_database_actor(session: Session, actor: Actor) -> None:
    """Le indica a MySQL qué usuario está haciendo el cambio."""
    session.execute(text("SET @actor_id = :actor_id"), {"actor_id": actor.id})


def translate_database_error(exc: SQLAlchemyError) -> ApiError:
    """Convierte errores de MySQL en mensajes que la API puede devolver.

    Los errores esperados conservan su significado, como un dato duplicado o
    inválido. Si aparece uno inesperado, se guarda en el log y se devuelve un
    error general de servicio.
    """
    original = getattr(exc, "orig", None)
    message = str(original or "")
    original_args = getattr(original, "args", ())
    is_signal = (
        "45000" in message
        or getattr(original, "sqlstate", None) == "45000"
        or bool(original_args and original_args[0] == 1644)
    )
    if original_args and original_args[0] == 1062:
        return ApiError(409, "CONFLICT", "El registro ya existe.")
    if original_args and original_args[0] in {1048, 1452, 3819}:
        return ApiError(422, "VALIDATION_ERROR", "Los datos no cumplen el esquema de G1.")
    if is_signal:
        match = re.search(r"\((400|404|409|422)\)", message)
        status = int(match.group(1)) if match else 409
        code = {
            400: "BAD_REQUEST",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "VALIDATION_ERROR",
        }[status]
        public_message = re.sub(r"\s*\((?:400|404|409|422)\)", "", message)
        public_message = re.sub(r"^ERROR:\s*", "", public_message)
        return ApiError(status, code, public_message or "La operación no es válida.")

    log.exception("Fallo al consultar la base de datos", exc_info=exc)
    return ApiError(503, "DATABASE_ERROR", "No fue posible completar la operación.")
