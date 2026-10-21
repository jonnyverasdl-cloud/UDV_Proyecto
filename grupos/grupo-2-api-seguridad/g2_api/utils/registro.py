
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from fastapi import Request
from sqlalchemy.orm import Session

logger = logging.getLogger("g2_api.auditoria")


# --- Acciones reconocidas ---------------------------------------------------

LOGIN_OK        = "LOGIN_OK"
LOGIN_FALLIDO   = "LOGIN_FALLIDO"
LOGOUT          = "LOGOUT"
ACCESS_DENIED   = "ACCESS_DENIED"
USER_CREATED    = "USER_CREATED"
USER_UPDATED    = "USER_UPDATED"
USER_DELETED    = "USER_DELETED"
ROLE_CREATED    = "ROLE_CREATED"
ROLE_UPDATED    = "ROLE_UPDATED"
FILE_UPLOADED   = "FILE_UPLOADED"
FILE_DOWNLOADED = "FILE_DOWNLOADED"


# ------------------------------------------------------------------

def _modelo_auditoria():
    """si `models.py` aun no existe, ."""
    from g2_api.models import Auditoria  # type: ignore

    return Auditoria


def _ahora() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def ip_del_request(request: Request | None) -> str | None:
    if request is None:
        return None
    cliente = getattr(request, "client", None)
    return getattr(cliente, "host", None) if cliente else None


# --- Escritura --------------------------------------------------------------

def registrar_accion(
    db: Session,
    accion: str,
    *,
    tabla: str | None = None,
    registro_id: str | int | None = None,
    actor_id: int | None = None,
    detalle: Mapping[str, Any] | None = None,
    ip_origen: str | None = None,
) -> bool:
    try:
        Auditoria = _modelo_auditoria()
        fila = Auditoria(
            accion     = str(accion).upper(),
            actor_id   = actor_id,
            tabla      = tabla,
            registro_id= str(registro_id) if registro_id is not None else None,
            detalle    = dict(detalle) if detalle else None,
            ip_origen  = ip_origen,
            creado_en  = _ahora(),
        )
        db.add(fila)
        db.commit()
        return True
    except Exception:  # noqa: BLE001
        db.rollback()
        logger.exception("No se pudo registrar la accion %s", accion)
        return False


# --- Atajos usados por los routers ------------------------------------------

def registrar_login_ok(
    db: Session, actor_id: int, *, ip_origen: str | None = None
) -> bool:
    return registrar_accion(
        db, LOGIN_OK, actor_id=actor_id, tabla="auth", ip_origen=ip_origen
    )


def registrar_logout(
    db: Session, actor_id: int, *, ip_origen: str | None = None
) -> bool:
    return registrar_accion(
        db, LOGOUT, actor_id=actor_id, tabla="auth", ip_origen=ip_origen
    )


def registrar_login_fallido(
    db: Session, correo: str, *, ip_origen: str | None = None
) -> bool:
    """Registra un intento fallido.

    - `actor_id` se resuelve si el usuario existe; si no, queda NULL.
    """
    correo_norm = (correo or "").strip().lower()
    actor_id: int | None = None
    try:
        from g2_api.models import Usuario  # type: ignore

        u = (
            db.query(Usuario)
            .filter(Usuario.correo == correo_norm)
            .first()
        )
        if u is not None:
            actor_id = getattr(u, "id_usuario", None) or getattr(u, "id", None)
    except Exception:  # noqa: BLE001
        actor_id = None

    return registrar_accion(
        db,
        LOGIN_FALLIDO,
        actor_id   = actor_id,
        tabla      = "auth",
        registro_id= correo_norm,
        ip_origen  = ip_origen,
    )


# --- Consultas -----------------------------------------

def contar_intentos_fallidos(db: Session, correo: str, minutos: int) -> int:
    """Cuenta LOGIN_FALLIDO del mismo correo en la ventana de `minutos`."""
    try:
        Auditoria = _modelo_auditoria()
        desde = _ahora() - timedelta(minutes=int(minutos))
        return int(
            db.query(Auditoria)
            .filter(
                Auditoria.accion      == LOGIN_FALLIDO,
                Auditoria.registro_id == (correo or "").strip().lower(),
                Auditoria.creado_en   >= desde,
            )
            .count()
        )
    except Exception:  # noqa: BLE001
        logger.exception("No se pudo contar intentos fallidos")
        return 0


def esta_bloqueado(
    db: Session,
    correo: str,
    *,
    max_intentos: int,
    minutos: int,
) -> bool:
    """True si el correo supero `max_intentos` fallos en los ultimos `minutos`."""
    return contar_intentos_fallidos(db, correo, minutos) >= int(max_intentos)
