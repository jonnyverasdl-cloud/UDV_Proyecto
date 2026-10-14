# Por defecto las pruebas usan una base SQLite temporal: No necesitan Docker ni MySQL y corren en cualquier computadora.
# Para probar contra el MySQL local del Docker, definir TEST_DATABASE_URL antes de correr pytest, por ejemplo:
# $env:TEST_DATABASE_URL = "mysql+pymysql://udv_app:CLAVE@localhost:3307/db_udv"
# Con MySQL las tablas NO se crean ni se borran (las creó el Grupo 1): jamás se hace drop_all en MySQL.
import os
import tempfile

_url_prueba = os.environ.get("TEST_DATABASE_URL")
if _url_prueba:
    os.environ["DATABASE_URL"] = _url_prueba
else:
    _tmp = tempfile.mkdtemp()
    os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["SECRET_KEY"] = "clave-solo-para-pruebas"
os.environ["CORS_ORIGINS"] = "http://localhost:5500"

import pytest # noqa: E402
from fastapi.testclient import TestClient # noqa: E402

from g2_api.database import Base, SessionLocal, engine # noqa: E402
from g2_api.main import app # noqa: E402


@pytest.fixture()
def db():
    # Sesión para la prueba. En SQLite las tablas quedan limpias en cada prueba.
    from g2_api import models # noqa: F401

    if engine.dialect.name == "sqlite":
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
    with SessionLocal() as sesion:
        yield sesion

@pytest.fixture()
def client():
    # Cliente HTTP de pruebas. No requiere base de datos mientras los routers usen el JSON de prueba.
    with TestClient(app) as c:
        yield c
