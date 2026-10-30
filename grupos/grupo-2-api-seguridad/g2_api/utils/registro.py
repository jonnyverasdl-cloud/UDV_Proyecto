

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from fastapi import Request
from sqlalchemy import func, text
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


# --- Helpers ----------------------------------------------------------------

def _modelo_auditoria():
    """ si `models` aún no está, degradamos sin romper."""
    from g2_api.models import Auditoria  # type: ignore

    return Auditoria


def _ahora() -> datetime:
    """(compatible con DATETIME de MySQL y con SQLite)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def ip_del_request(request: Request | None) -> str | None:
    """ para routers:"""
    if request is None:
        return None
    cliente = getattr(request, "client", None)
    return getattr(cliente, "host", None) if cliente else None

def fijar_actor(db: Session, actor_id: int | None) -> None:
    
    try:
        dialecto = ""
        bind = getattr(db, "bind", None)
        if bind is not None and getattr(bind, "dialect", None) is not None:
            dialecto = bind.dialect.name
        if dialecto == "mysql":
            valor = int(actor_id) if actor_id is not None and actor_id > 0 else None
            db.execute(text("SET @actor_id = :id"), {"id": valor})
    except Exception:  # noqa: BLE001
        logger.exception("No se pudo fijar @actor_id para triggers del G1")


# Alias de compatibilidad 
set_actor_id = fijar_actor

# --- Escritura --------------------------------------------------------------
def registrar_accion(
    db: Session,
    accion: str,
    *,
    tabla: str | None = None,
    registro_id: int | None = None,
    actor_id: int | None = None,
    detalle: Mapping[str, Any] | None = None,
    ip_origen: str | None = None,
) -> bool:
    """True si se guardó, False si falló."""
    try:
        # 0 no es un id válido: se persiste NULL 
        if actor_id is not None and actor_id <= 0:
            actor_id = None

        Auditoria = _modelo_auditoria()
        fila = Auditoria(
            accion      = str(accion).upper(),
            actor_id    = actor_id,
            tabla       = tabla,
            registro_id = int(registro_id) if registro_id is not None else None,
            detalle     = dict(detalle) if detalle else None,
            ip_origen   = ip_origen,
            creado_en   = _ahora(),
        )
        db.add(fila)
        db.commit()
        return True
    except Exception:  # noqa: BLE001
        db.rollback()
        logger.exception("No se pudo registrar la acción %s", accion)
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
        actor_id    = actor_id,
        tabla       = "auth",
        registro_id = actor_id,                    # INT o NULL
        detalle     = {"correo": correo_norm},     # correo normalizado
        ip_origen   = ip_origen,
    )


# --- Consultas  -----------------------------------------

def contar_intentos_fallidos(db: Session, correo: str, minutos: int) -> int:
    """Cuenta LOGIN_FALLIDO del mismo correo en la ventana de `minutos`.

    Filtra por `detalle.correo` ).
    """
    try:
        Auditoria = _modelo_auditoria()
        desde = _ahora() - timedelta(minutes=int(minutos))
        correo_norm = (correo or "").strip().lower()

        correo_en_detalle = func.json_extract(Auditoria.detalle, "$.correo")

        return int(
            db.query(Auditoria)
            .filter(
                Auditoria.accion == LOGIN_FALLIDO,
                correo_en_detalle == correo_norm,
                Auditoria.creado_en >= desde,
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
    """True si el correo superó `max_intentos` fallos en los últimos `minutos`."""
    return contar_intentos_fallidos(db, correo, minutos) >= int(max_intentos)


def limpiar_intentos(db: Session, correo: str) -> None:
    """Borra los LOGIN_FALLIDO del correo tras un login exitoso (opcional)."""
    try:
        Auditoria = _modelo_auditoria()
        correo_norm = (correo or "").strip().lower()
        correo_en_detalle = func.json_extract(Auditoria.detalle, "$.correo")
        db.query(Auditoria).filter(
            Auditoria.accion == LOGIN_FALLIDO,
            correo_en_detalle == correo_norm,
        ).delete(synchronize_session=False)
        db.commit()
    except Exception:  # noqa: BLE001
        db.rollback()
        logger.exception("No se pudieron limpiar los intentos fallidos")
