# Aplicacion principal del Grupo 2 (Persona 5).
# Cada persona agrega aqui su router cuando lo sube.
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from g2_api import config
from g2_api.database import init_db
from g2_api.routers import auth
from g2_api.routers import users

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # crea las tablas si no existen
    yield

app = FastAPI(
    title="Grupo 2 - API y Seguridad",
    version="0.1.0",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi",
    redoc_url=None,
    lifespan=lifespan,
)

# CORS: solo los origenes definidos en CORS_ORIGINS del .env
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Routers (cada persona agrega el suyo)
app.include_router(auth.router) # Persona 1
app.include_router(users.router) # Persona 2

