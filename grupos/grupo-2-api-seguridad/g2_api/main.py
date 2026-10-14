# Aplicacion principal del Grupo 2 (Persona 5).
# Cada persona agrega aqui su router cuando lo sube.
from importlib.util import find_spec

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from g2_api import config
from g2_api.middleware.error_handler import register_error_handlers
from g2_api.routers import auth
from g2_api.routers import roles
from g2_api.routers import users

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db() # Crea las tablas si no existen.
    yield

app = FastAPI(
    title="Grupo 2 - API y Seguridad",
    version="0.1.0",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",  # Misma ruta que el main.py de la raíz del PM.
    redoc_url=None,
)

# Errores: Todos salen con el formato comun (codigo, mensaje y detalles). Es el archivo de Edgar.
register_error_handlers(app)

# CORS: Solo los origenes definidos en CORS_ORIGINS del .env.
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Routers: Cada persona agrega el suyo.
app.include_router(auth.router) # Persona 1: /auth/login, /auth/logout, /me.
app.include_router(users.router) # Persona 2: /users.
app.include_router(roles.router) # Persona 2: /roles.

# Persona 4: /files. El archivo routers/files.py lo sube Fulvio en la semana 2.
# Mientras no exista, la app arranca igual; en cuanto exista, se monta solo.
# Si files.py existe pero tiene un error, el error SÍ se muestra (no se oculta).
if find_spec("g2_api.routers.files") is not None:
    from g2_api.routers import files

    app.include_router(files.router)
