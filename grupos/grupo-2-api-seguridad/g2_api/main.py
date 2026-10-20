# Aplicacion principal del Grupo 2 (Persona 5).
# Cada persona agrega aqui su router cuando lo sube.
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from g2_api import config
from g2_api.middleware.error_handler import register_error_handlers
from g2_api.routers import auth
from g2_api.routers import files
from g2_api.routers import roles
from g2_api.routers import users

app = FastAPI(
    title="Grupo 2 - API y Seguridad",
    version="0.1.0",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json", # Misma ruta que el main.py de la raíz del PM.
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
app.include_router(auth.router) # Persona 1: /auth/login y /auth/logout.
# GET /api/v1/me (Daniel): Se conecta solo cuando auth.py ya trae me_router. Así main.py no se rompe antes.
if hasattr(auth, "me_router"):
    app.include_router(auth.me_router)
app.include_router(users.router) # Persona 2: /users.
app.include_router(roles.router) # Persona 2: /roles.
app.include_router(files.router) # Persona 4: /files.

