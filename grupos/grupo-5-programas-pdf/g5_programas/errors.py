"""Errores controlados que G5 puede devolver de forma clara a la API."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse


class ApiError(HTTPException):
    """Guarda la información que la API necesita para explicar un error.

    Como HTTPException, el manejador compartido de G2 conserva el código HTTP y
    produce el formato de error común.
    """

    def __init__(self, status: int, code: str, message: str, details=None):
        """Guarda el estado HTTP, el código y el mensaje del error."""
        self.status = status
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(
            status_code=status,
            detail={
                "code": code,
                "message": message,
                "details": self.details,
            },
        )


async def _api_error_handler(_request: Request, error: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status,
        content={
            "error": {
                "code": error.code,
                "message": error.message,
                "details": error.details,
            }
        },
    )


def registrar_errores(app: FastAPI) -> None:
    """Registra el formato JSON común para las excepciones controladas de G5."""
    app.add_exception_handler(ApiError, _api_error_handler)
