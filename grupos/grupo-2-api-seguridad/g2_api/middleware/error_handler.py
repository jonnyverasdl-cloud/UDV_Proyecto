
from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("g2_api.errores")


# --- Catálogo de códigos ---------------------------------------------------

class ErrorCode:
    BAD_REQUEST         = "BAD_REQUEST"
    UNAUTHORIZED        = "UNAUTHORIZED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED       = "TOKEN_EXPIRED"
    FORBIDDEN           = "FORBIDDEN"
    NOT_FOUND           = "NOT_FOUND"
    METHOD_NOT_ALLOWED  = "METHOD_NOT_ALLOWED"
    CONFLICT            = "CONFLICT"
    VALIDATION_ERROR    = "VALIDATION_ERROR"
    EMPTY_UPDATE        = "EMPTY_UPDATE"
    TOO_MANY_REQUESTS   = "TOO_MANY_REQUESTS"
    INTERNAL_ERROR      = "INTERNAL_ERROR"


DEFAULT_CODES: dict[int, str] = {
    400: ErrorCode.BAD_REQUEST,
    401: ErrorCode.UNAUTHORIZED,
    403: ErrorCode.FORBIDDEN,
    404: ErrorCode.NOT_FOUND,
    405: ErrorCode.METHOD_NOT_ALLOWED,
    409: ErrorCode.CONFLICT,
    422: ErrorCode.VALIDATION_ERROR,
    429: ErrorCode.TOO_MANY_REQUESTS,
    500: ErrorCode.INTERNAL_ERROR,
}

DEFAULT_MESSAGES: dict[int, str] = {
    400: "Solicitud inválida.",
    401: "No autenticado o credenciales inválidas.",
    403: "No tiene permiso para realizar esta acción.",
    404: "Recurso no encontrado.",
    405: "Método no permitido para esta ruta.",
    409: "Conflicto con el estado actual del recurso.",
    422: "Datos de entrada inválidos.",
    429: "Demasiadas solicitudes.",
    500: "Error interno del servidor.",
}


def api_error(
    status_code: int,
    code: str,
    message: str,
    details: Mapping[str, Any] | Iterable | None = None,
    headers: dict[str, str] | None = None,
) -> HTTPException:
    """

    Ejemplo:
        raise api_error(
            409, "Correo ya registrado",
            details={"campo": "correo"},
        )
    """
    if isinstance(details, Mapping):
        det: dict[str, Any] = dict(details)
    elif isinstance(details, Iterable) and not isinstance(details, (str, bytes)):
        # 
        det = {"items": list(details)}
    else:
        det = {}

    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "details": det},
        headers=headers,
    )


def _payload(
    code: str,
    message: str,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """  {"error": {"code", "message", "details"}}."""
    return {
        "error": {
            "code": code,
            "message": message,
            "details": dict(details) if details else {},
        }
    }


def error_response(
    status_code: int,
    code: str | None = None,
    message: str | None = None,
    details: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=_payload(
            code or DEFAULT_CODES.get(status_code, "ERROR"),
            message or DEFAULT_MESSAGES.get(status_code, "Error."),
            details,
        ),
        headers=dict(headers) if headers else None,
    )


# --- Handlers -------------------------------------------------------------

async def _http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail  = exc.detail
    code    = DEFAULT_CODES.get(exc.status_code, "HTTP_ERROR")
    message = DEFAULT_MESSAGES.get(exc.status_code, "Error.")
    details: dict[str, Any] = {}

    if isinstance(detail, Mapping):
        # Viene de api_error()
        code    = str(detail.get("code", code))
        message = str(detail.get("message", message))
        raw = detail.get("details")
        if isinstance(raw, Mapping):
            details = dict(raw)
        elif isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)):
            details = {"items": list(raw)}
    elif isinstance(detail, str) and detail:
        if exc.status_code < 500:
            message = detail
        else:
            
            logger.warning(
                "HTTPException %s en %s %s con detail string (no expuesto): %s",
                exc.status_code, request.method, request.url.path, detail,
            )

    return error_response(
        status_code=exc.status_code,
        code=code,
        message=message,
        details=details,
        headers=getattr(exc, "headers", None),
    )


async def _validation_exception_handler(request: Request, exc: RequestValidationError):
    """422 con el detalle de CADA campo inválido."""
    campos: list[dict[str, str]] = []
    for err in exc.errors():
        loc = [
            str(p)
            for p in err.get("loc", ())
            if p not in ("body", "query", "path", "header")
        ]
        campos.append({
            "campo":   ".".join(loc) if loc else "cuerpo",
            "mensaje": str(err.get("msg", "Valor inválido.")),
            "tipo":    str(err.get("type", "value_error")),
        })

    return error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code=ErrorCode.VALIDATION_ERROR,
        message="Datos de entrada inválidos.",
        details={"campos": campos},
    )


async def _unhandled_exception_handler(request: Request, exc: Exception):
    # Traza / SQL / rutas internas: SOLO al log del servidor.
    logger.exception("Error no controlado en %s %s", request.method, request.url.path)
    return error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code=ErrorCode.INTERNAL_ERROR,
        message="Error interno del servidor.",
    )


# --- Registro -------------------------------------------------------------

def register_error_handlers(app: FastAPI) -> None:
    """Engancha los tres manejadores. Nombre que usa main.py ."""
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    app.add_exception_handler(Exception, _unhandled_exception_handler)


# Alias para compatibilidad con los tests (buscan `registrar_manejadores`).
registrar_manejadores = register_error_handlers
