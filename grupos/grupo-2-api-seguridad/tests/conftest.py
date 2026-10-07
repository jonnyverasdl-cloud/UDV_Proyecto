# Configuracion comun de pruebas (Persona 5). Usa una base SQLite temporal.
import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["SECRET_KEY"] = "clave-solo-para-pruebas"
os.environ["CORS_ORIGINS"] = "http://localhost:5500"

import pytest # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from g2_api.database import Base, SessionLocal, engine # noqa: E402
from g2_api.main import app # noqa: E402

@pytest.fixture()
def db():
    # Sesion con tablas limpias en cada prueba.
    from g2_api import models # noqa: F401

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as sesion:
        yield sesion

@pytest.fixture()
def client(db):
    with TestClient(app) as c:
        yield c
