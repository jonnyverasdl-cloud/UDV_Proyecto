from __future__ import annotations

import json

import pytest
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.testclient import TestClient

from g2_api.middleware.error_handler import registrar_manejadores
from g2_api.utils.paginacion import (
    PER_PAGE_MAX,
    Paginacion,
    paginar,
    params_paginacion,
)


# --------------------------------------------------------------------------
#  pruebas
# --------------------------------------------------------------------------

class _FakeQuery:
    """Sustituto mínimo de sqlalchemy.orm.Query para probar `paginar`."""

    def __init__(self, total: int = 250) -> None:
        self._total = total
        self._offset = 0
        self._limit = total

    def count(self) -> int:
        return self._total

    def offset(self, n: int) -> "_FakeQuery":
        self._offset = n
        return self

    def limit(self, n: int) -> "_FakeQuery":
        self._limit = n
        return self

    def all(self):
        return list(
            range(self._offset, min(self._offset + self._limit, self._total))
        )


def _crear_app() -> FastAPI:
    app = FastAPI()
    registrar_manejadores(app)

    @app.get("/boom")
    def boom():
        raise HTTPException(status_code=401, detail="Token inválido")

    @app.get("/no-encontrado")
    def no_encontrado():
        raise HTTPException(status_code=404, detail="No existe")

    @app.get("/conflicto")
    def conflicto():
        raise HTTPException(
            status_code=409,
            detail={"code": "DUPLICATE_EMAIL", "message": "Correo ya registrado"},
        )

    @app.get("/prohibido")
    def prohibido():
        raise HTTPException(status_code=403)

    @app.get("/explotar")
    def explotar():
        raise RuntimeError("SELECT * FROM usuario WHERE contrasena='x'")

    @app.get("/validar")
    def validar(
        correo: str = Query(..., min_length=3),
        edad: int = Query(..., ge=0, le=120),
    ):
        return {"correo": correo, "edad": edad}

    @app.get("/lista")
    def lista(p: Paginacion = Depends(params_paginacion)):
        return paginar(_FakeQuery(250), p.page, p.per_page)

    return app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(_crear_app(), raise_server_exceptions=False)


# --------------------------------------------------------------------------
# Formato común de error
# --------------------------------------------------------------------------

def _assert_formato(body: dict) -> None:
    assert set(body.keys()) == {"error"}
    assert set(body["error"].keys()) == {"code", "message", "details"}
    assert isinstance(body["error"]["details"], dict)


def test_formato_error_401(client):
    r = client.get("/boom")
    assert r.status_code == 401
    body = r.json()
    _assert_formato(body)
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert "Token inválido" in body["error"]["message"]


def test_formato_error_404(client):
    r = client.get("/no-encontrado")
    assert r.status_code == 404
    body = r.json()
    _assert_formato(body)
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["details"] == {}


def test_formato_error_403_sin_detail(client):
    r = client.get("/prohibido")
    assert r.status_code == 403
    body = r.json()
    _assert_formato(body)
    assert body["error"]["code"] == "FORBIDDEN"


def test_error_409_respeta_code_del_detail(client):
    r = client.get("/conflicto")
    assert r.status_code == 409
    body = r.json()
    _assert_formato(body)
    assert body["error"]["code"] == "DUPLICATE_EMAIL"
    assert body["error"]["message"] == "Correo ya registrado"


def test_error_500_no_filtra_informacion_interna(client):
    r = client.get("/explotar")
    assert r.status_code == 500
    body = r.json()
    _assert_formato(body)
    assert body["error"]["code"] == "INTERNAL_ERROR"
    texto = json.dumps(body).lower()
    for prohibido in ("select", "runtimeerror", "traceback", "contrasena", ".py"):
        assert prohibido not in texto


# --------------------------------------------------------------------------
# 422 con detalle por campo
# --------------------------------------------------------------------------

def test_422_trae_detalle_por_campo(client):
    r = client.get("/validar")  # faltan correo y edad
    assert r.status_code == 422
    body = r.json()
    _assert_formato(body)
    assert body["error"]["code"] == "VALIDATION_ERROR"
    campos = body["error"]["details"]["campos"]
    nombres = {c["campo"] for c in campos}
    assert {"correo", "edad"} <= nombres
    for c in campos:
        assert c["mensaje"]
        assert c["tipo"]


def test_422_campo_fuera_de_rango(client):
    r = client.get("/validar", params={"correo": "abc", "edad": 999})
    assert r.status_code == 422
    campos = r.json()["error"]["details"]["campos"]
    assert any(c["campo"] == "edad" for c in campos)


# --------------------------------------------------------------------------
# Paginación
# --------------------------------------------------------------------------

def test_paginacion_estructura_y_tamano(client):
    r = client.get("/lista")
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"page", "per_page", "total", "data"}
    assert body["page"] == 1
    assert body["per_page"] == 20
    assert body["total"] == 250
    assert len(body["data"]) == 20
    assert body["data"][0] == 0


def test_paginacion_segunda_pagina(client):
    r = client.get("/lista", params={"page": 2, "per_page": 10})
    body = r.json()
    assert body["page"] == 2
    assert body["per_page"] == 10
    assert body["data"][0] == 10


def test_paginacion_page_invalida_da_422(client):
    r = client.get("/lista", params={"page": 0})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_paginacion_per_page_excede_maximo_da_422(client):
    r = client.get("/lista", params={"per_page": PER_PAGE_MAX + 1})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


# --------------------------------------------------------------------------

from datetime import datetime  # noqa: E402

from sqlalchemy import (  # noqa: E402
    Column,
    DateTime,
    Integer,
    JSON,
    String,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker  # noqa: E402

from g2_api.utils import registro  # noqa: E402

_AuditBase = declarative_base()


class _AuditoriaFake(_AuditBase):
    """Refleja las columnas reales de la tabla `auditoria`."""

    __tablename__ = "auditoria"
    id          = Column(Integer, primary_key=True)
    tabla       = Column(String(50),  nullable=True)
    registro_id = Column(String(255), nullable=True, index=True)
    accion      = Column(String(50),  nullable=False, index=True)
    actor_id    = Column(Integer, nullable=True)
    ip_origen   = Column(String(45),  nullable=True)
    detalle     = Column(JSON, nullable=True)
    creado_en   = Column(DateTime, nullable=False, index=True)


@pytest.fixture()
def db_mem(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    _AuditBase.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    # Forzamos a registro.py a usar nuestra Auditoria falsa.
    monkeypatch.setattr(registro, "_modelo_auditoria", lambda: _AuditoriaFake)
    yield db
    db.close()


def test_registrar_accion_guarda_fila(db_mem):
    ok = registro.registrar_accion(
        db_mem, "LOGIN_OK",
        actor_id=7, tabla="auth", ip_origen="127.0.0.1",
    )
    assert ok is True
    fila = db_mem.query(_AuditoriaFake).one()
    assert fila.accion    == "LOGIN_OK"
    assert fila.actor_id  == 7
    assert fila.tabla     == "auth"
    assert fila.ip_origen == "127.0.0.1"
    assert isinstance(fila.creado_en, datetime)


def test_registrar_login_fallido_normaliza_correo(db_mem):
    ok = registro.registrar_login_fallido(db_mem, "  X@Y.COM ", ip_origen="10.0.0.1")
    assert ok is True
    fila = db_mem.query(_AuditoriaFake).one()
    assert fila.accion      == "LOGIN_FALLIDO"
    assert fila.actor_id    is None         
    assert fila.registro_id == "x@y.com"    
    assert fila.ip_origen   == "10.0.0.1"


def test_contar_intentos_fallidos_por_correo(db_mem):
    for _ in range(3):
        registro.registrar_login_fallido(db_mem, "a@b.com")
    registro.registrar_login_fallido(db_mem, "otro@b.com")

    assert registro.contar_intentos_fallidos(db_mem, "a@b.com",   15) == 3
    assert registro.contar_intentos_fallidos(db_mem, "A@B.COM",   15) == 3
    assert registro.contar_intentos_fallidos(db_mem, "otro@b.com", 15) == 1
    assert registro.contar_intentos_fallidos(db_mem, "nadie@b.com", 15) == 0


def test_esta_bloqueado_segun_umbral(db_mem):
    for _ in range(5):
        registro.registrar_login_fallido(db_mem, "a@b.com")

    assert registro.esta_bloqueado(
        db_mem, "a@b.com", max_intentos=5, minutos=15
    ) is True
    assert registro.esta_bloqueado(
        db_mem, "a@b.com", max_intentos=6, minutos=15
    ) is False


def test_registro_no_rompe_si_models_no_existe():
    """registrar_accion debe devolver False (no lanzar) si no hay modelo."""

    class _S:
        def add(self, _):
            raise RuntimeError("sin modelo")

        def commit(self):
            pass

        def rollback(self):
            pass

    from g2_api.utils import registro as reg

    import builtins

    original = builtins.__import__

    def _import_falso(name, *a, **k):
        if name == "g2_api.models":
            raise ImportError("sin models.py")
        return original(name, *a, **k)

    builtins.__import__ = _import_falso
    try:
        assert reg.registrar_accion(_S(), "TEST") is False
    finally:
        builtins.__import__ = original
