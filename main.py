"""Punto de entrada de la aplicación (mantenido por el PM, README §4).

Hace importables los paquetes de cada grupo (g1_bd, g2_api, ...) y monta sus
routers en una sola app FastAPI. Un router que todavía no existe en la rama se
omite y aparece en /health, para que el deploy no se caiga mientras los
grupos integran su trabajo.

Convención para los grupos: cada router declara su ruta completa con el
prefijo /api/v1 (por ejemplo APIRouter(prefix="/api/v1/auth")).

Correr local:  uvicorn main:app --reload
"""
import importlib
import logging
import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent
log = logging.getLogger("udv")

# Las carpetas de grupo llevan guiones y no se importan directo:
# se agregan al path para poder hacer `from g2_api import ...`.
for carpeta in sorted((RAIZ / "grupos").glob("grupo-*")):
    if carpeta.is_dir() and str(carpeta) not in sys.path:
        sys.path.insert(0, str(carpeta))

# Routers registrados. Para sumar uno: agregar ("paquete.modulo", "variable").
# Cada grupo se descomenta cuando su PR entra a main (nombres reales de sus paquetes).
ROUTERS = [
    ("g2_api.routers.auth", "router"),
    ("g2_api.routers.auth", "me_router"),   # GET /api/v1/me
    ("g2_api.routers.users", "router"),
    ("g2_api.routers.roles", "router"),
    ("g2_api.routers.files", "router"),     # G2: archivos (G2-21 corregido en PR #20)
    ("workflow.api", "router"),             # G3
    ("g4_inbox.routes", "router"),          # G4 (PR del 9-nov)
    ("g5_programas.router", "router"),      # G5 (PR del 6-nov)
    ("g6_admin.api", "router"),             # G6
]

app = FastAPI(
    title="UDV · Workflow docente",
    version="0.1.0",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
    redoc_url=None,
)

# Formato de error común: servicio compartido del G2 (CONTRATO_COMUN §1).
try:
    from g2_api.middleware.error_handler import register_error_handlers
    register_error_handlers(app)
except ImportError as exc:
    log.warning("Manejador de errores del G2 no disponible: %s", exc)

montados, pendientes = [], {}
for modulo, nombre in ROUTERS:
    try:
        app.include_router(getattr(importlib.import_module(modulo), nombre))
        montados.append(f"{modulo}:{nombre}")
    except Exception as exc:  # el grupo aún no integró ese módulo a esta rama
        pendientes[f"{modulo}:{nombre}"] = f"{type(exc).__name__}: {exc}"
        log.warning("Router omitido %s:%s -> %s", modulo, nombre, exc)

# Ganchos opcionales de cada grupo sobre la app (solo tocan sus propias rutas).
for modulo, nombre in [
    ("g2_api.openapi_docs", "completar_openapi"),   # G2-33: codigos y ejemplos en Swagger
    ("g5_programas.errors", "registrar_errores"),   # G5: ApiError -> JSON del contrato
]:
    try:
        getattr(importlib.import_module(modulo), nombre)(app)
    except Exception as exc:  # noqa: BLE001
        log.warning("Gancho omitido %s:%s -> %s", modulo, nombre, exc)


# Interfaz (README §4: los estáticos y estilos compartidos los sirve main.py).
# Cada pantalla vive en la carpeta de su grupo; aquí solo se publica.
# El login es el de G2; el token se guarda en la pestaña como "udv_token".
PANTALLAS = [
    ("/udv-styles", "grupos/udv-styles"),                               # estilos compartidos (PM)
    ("/app/g2",     "grupos/grupo-2-api-seguridad/frontend-login"),     # G2: pantalla de login
    ("/app/g3",     "grupos/grupo-3-workflow-tareas/frontend"),         # G3: tareas
    ("/app/g4",     "grupos/grupo-4-inbox-entregas/g4_inbox/static"),   # G4: bandeja y entregas
    ("/app/g5",     "grupos/grupo-5-programas-pdf/frontend"),           # G5: programas y PDF
    ("/app/g6",     "grupos/grupo-6-administracion/g6_admin/pantallas"),# G6: panel, catálogos, auditoría
    ("/app",        "portal"),                                          # inicio y login (PM)
]
pantallas_montadas = []
for ruta, carpeta in PANTALLAS:
    directorio = RAIZ / carpeta
    if directorio.is_dir():
        app.mount(ruta, StaticFiles(directory=str(directorio), html=True), name=ruta.strip("/").replace("/", "-"))
        pantallas_montadas.append(ruta)
    else:
        log.warning("Pantalla omitida %s -> no existe %s", ruta, carpeta)


@app.get("/", include_in_schema=False)
def inicio():
    return RedirectResponse("/app/")


@app.get("/health", tags=["Sistema"])
def health():
    """Estado de la app y de los routers. No requiere base de datos."""
    return {"status": "ok", "routers": montados, "pendientes": pendientes, "pantallas": pantallas_montadas}


@app.get("/health/db", tags=["Sistema"])
def health_db():
    """Comprueba la conexión a MySQL usando DATABASE_URL."""
    url = os.getenv("DATABASE_URL")
    if not url:
        return {"status": "sin_configurar", "detalle": "Falta DATABASE_URL"}
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            version = conn.execute(text("SELECT VERSION()")).scalar()
            tablas = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = DATABASE() AND table_type = 'BASE TABLE'"
            )).scalar()
        engine.dispose()
        return {"status": "ok", "version": version, "tablas": tablas}
    except Exception as exc:
        return {"status": "error", "detalle": f"{type(exc).__name__}: {exc}"}
