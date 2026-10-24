"""Aplicación FastAPI que reúne la API y la página del proyecto.

Aquí se conectan las rutas de programas y, si están instaladas, las de los
otros grupos. También se sirve la interfaz web y se da un formato común a los
errores de la API.
"""

import importlib
import logging
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

ROOT = Path(__file__).resolve().parent.parent
log = logging.getLogger("udv")
# Añade los módulos de cada grupo para que FastAPI pueda cargar sus rutas.
for group in sorted((ROOT / "grupos").glob("grupo-*")):
    if group.is_dir() and str(group) not in sys.path:
        sys.path.insert(0, str(group))

from g5_programas.router import router as programas_router
from g5_programas.errors import ApiError

app = FastAPI(
    title="UDV · Workflow docente",
    version="1.0.0",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
    redoc_url=None,
)
app.state.database_session_factory = None
app.include_router(programas_router)

# Si los routers de los otros grupos están instalados, también los carga.
for module, name in (
    ("g2_api.routers.auth", "router"),
    ("g2_api.routers.users", "router"),
    ("g2_api.routers.roles", "router"),
):
    try:
        app.include_router(getattr(importlib.import_module(module), name))
    except (ImportError, AttributeError) as exc:
        log.warning("Router compartido aún no disponible %s: %s", module, exc)


# Todas las rutas devuelven los errores con el mismo formato.
@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    """Devuelve los errores conocidos de la aplicación como JSON."""
    return JSONResponse(
        status_code=exc.status,
        content={"error": {
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
        }},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Explica qué dato de la solicitud no pasó la validación."""
    errors = exc.errors()
    invalid_json = any(error.get("type") == "json_invalid" for error in errors)
    details = {
        ".".join(str(part) for part in error.get("loc", ())[1:]): error.get("msg", "Valor inválido.")
        for error in errors
    }
    status = 400 if invalid_json else 422
    return JSONResponse(
        status_code=status,
        content={"error": {
            "code": "BAD_REQUEST" if invalid_json else "VALIDATION_ERROR",
            "message": "JSON mal formado." if invalid_json else "La solicitud contiene campos inválidos.",
            "details": details,
        }},
    )


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    """Devuelve los errores HTTP con el mismo formato que el resto de la API."""
    codes = {
        400: "BAD_REQUEST",
        401: "UNAUTHENTICATED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
    }
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {
            "code": codes.get(exc.status_code, "HTTP_ERROR"),
            "message": str(exc.detail),
            "details": {},
        }},
        headers=exc.headers,
    )


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(request: Request, exc: SQLAlchemyError):
    """Convierte un error de base de datos antes de responder a la solicitud."""
    from g5_programas.database import translate_database_error

    return await api_error_handler(request, translate_database_error(exc))


try:
    from g2_api.middleware.error_handler import register_error_handlers
except ImportError as exc:
    log.warning("Manejador de errores compartido de G2 aún no disponible: %s", exc)
else:
    register_error_handlers(app)


# Rutas para revisar el servicio y abrir la página principal.
@app.get("/health", tags=["Sistema"])
def health():
    """Confirma que la aplicación está respondiendo."""
    return {"status": "ok", "routers": ["g5_programas"]}


@app.get("/", include_in_schema=False)
def frontend():
    """Abre la página del programa de curso."""
    return FileResponse(ROOT / "frontend" / "Programa.html")


app.mount("/", StaticFiles(directory=ROOT / "frontend", html=True), name="frontend")
