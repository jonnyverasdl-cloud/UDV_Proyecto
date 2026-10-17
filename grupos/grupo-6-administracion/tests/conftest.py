"""Preparación de las pruebas del G6.

Las rutas se prueban con el formato de error y el control de roles reales del
G2. Lo único que se reemplaza es quién inició sesión, con la herramienta de
FastAPI para pruebas (dependency_overrides): así cada prueba elige si actúa
como administración, como docente o sin sesión, sin tocar la base de datos.
"""

import os
import tempfile

# g2_api lee su configuración al importarse: valores solo para pruebas, igual
# que en el conftest del G2. La base es un SQLite temporal, nunca MySQL.
_carpeta = tempfile.mkdtemp()
os.environ["SECRET_KEY"] = "clave-solo-para-pruebas-g6"
os.environ["DATABASE_URL"] = f"sqlite:///{_carpeta}/pruebas_g6.db"

import pytest  # noqa: E402
from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from g2_api.middleware.auth_middleware import obtener_usuario_actual  # noqa: E402
from g2_api.middleware.error_handler import register_error_handlers  # noqa: E402

from g6_admin import api  # noqa: E402
from g6_admin.catalogos import RepositorioEnMemoria, ServicioCatalogos  # noqa: E402

# Usuarios ficticios con los códigos de rol de la tabla `rol` del G1.
ADMINISTRACION = {"id": 1, "correo": "admin@ejemplo.test", "roles": ["admin"], "activo": True}
DOCENTE = {"id": 2, "correo": "docente@ejemplo.test", "roles": ["teacher"], "activo": True}


def _cliente(servicio: ServicioCatalogos, usuario: dict | None) -> TestClient:
    app = FastAPI()
    register_error_handlers(app)          # formato de error del G2
    app.include_router(api.router)        # igual que lo monta main.py

    def usuario_de_prueba():
        if usuario is None:
            raise HTTPException(status_code=401, detail="Usuario no autenticado")
        return usuario

    app.dependency_overrides[obtener_usuario_actual] = usuario_de_prueba
    app.dependency_overrides[api.obtener_servicio] = lambda: servicio
    return TestClient(app)


@pytest.fixture
def servicio() -> ServicioCatalogos:
    """Catálogos vacíos: cada prueba empieza sin registros."""
    return ServicioCatalogos(RepositorioEnMemoria())


@pytest.fixture
def admin(servicio) -> TestClient:
    return _cliente(servicio, ADMINISTRACION)


@pytest.fixture
def docente(servicio) -> TestClient:
    return _cliente(servicio, DOCENTE)


@pytest.fixture
def sin_sesion(servicio) -> TestClient:
    return _cliente(servicio, None)
