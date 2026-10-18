"""
g4_inbox.main — SOLO para correr y probar G4 de forma independiente.



Cómo correr esto:
    pip install -r requirements.txt
    uvicorn g4_inbox.main:app --reload --app-dir .

Luego:
    - http://127.0.0.1:8000/api/v1/docs         → probar los 13 endpoints
    - http://127.0.0.1:8000/static/inbox.html    → la pantalla real del inbox
      (el CSS institucional solo carga en modo standalone si corren con
      G4_STANDALONE_DEV=1 — ver nota del mount de udv-styles, más abajo)
"""

import os

from dotenv import load_dotenv

# Se carga aquí, directo, sin depender de que otro módulo lo haga como
# efecto secundario — antes esto solo pasaba si G4_USAR_MYSQL estaba
# activo (porque database.py era quien importaba config.py), así que si
# alguien solo quería ver el diseño sin conectar a MySQL, el .env nunca
# se leía y G4_STANDALONE_DEV no servía de nada.
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routes import router

app = FastAPI(
    title="Grupo 4 - Inbox y entregas",
    version="0.3.0",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",  # misma ruta que usará el main.py de la raíz
    redoc_url=None,
)

# Errores: intenta usar el formato común de G2 (register_error_handlers).
# Si G4 corre sola, sin el resto del repo al lado (g2_api no está en el
# PYTHONPATH), esto no revienta — sigue con los HTTPException normales de
# FastAPI, para no bloquear a quien solo quiere probar G4 por su cuenta.
try:
    from g2_api.middleware.error_handler import register_error_handlers
    register_error_handlers(app)
except ImportError:
    pass

# CORS: permisivo a propósito, solo para desarrollo local.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Sirve static/ (inbox.html, detalle.html, css, js) en /static/...
app.mount("/static", StaticFiles(directory="g4_inbox/static"), name="static")

# El brief del PM pidió NO montar udv-styles — esa carpeta está fuera de
# la nuestra, y la aplicación principal la sirve una vez todo esté
# integrado. Esto solo se activa si ustedes mismos ponen
# G4_STANDALONE_DEV=1, para poder ver el CSS institucional mientras
# prueban G4 solos, antes de que exista el main.py de la raíz.
if os.environ.get("G4_STANDALONE_DEV") == "1":
    app.mount("/udv-styles", StaticFiles(directory="../udv-styles"), name="udv-styles")
