"""Errores controlados que G5 puede devolver de forma clara a la API."""


class ApiError(Exception):
    """Guarda la información que la API necesita para explicar un error.

    FastAPI usa estos datos para armar la respuesta JSON, sin mostrar detalles
    internos del servidor.
    """

    def __init__(self, status: int, code: str, message: str, details=None):
        """Guarda el estado HTTP, el código y el mensaje del error."""
        self.status = status
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)
