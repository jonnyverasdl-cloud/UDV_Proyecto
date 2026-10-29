"""Pruebas de GET /api/v1/health: escenarios G6-34, G6-36 y G6-39."""

import time
from datetime import datetime

import pytest

from g6_admin.salud import commit_desplegado, estado_del_servicio

CAMPOS = {"status", "service", "version", "environment", "commit", "time",
          "uptime_seconds", "checks"}


def test_health_responde_sin_iniciar_sesion(sin_sesion):
    respuesta = sin_sesion.get("/api/v1/health")
    assert respuesta.status_code == 200
    assert respuesta.json()["status"] == "ok"
    assert respuesta.headers["cache-control"] == "no-store"


def test_health_tiene_solo_los_campos_esperados(sin_sesion):
    assert set(sin_sesion.get("/api/v1/health").json()) == CAMPOS


def test_health_usa_fecha_iso_8601(sin_sesion):
    fecha = sin_sesion.get("/api/v1/health").json()["time"]
    assert datetime.fromisoformat(fecha).tzinfo is not None


def test_health_revisa_la_base_con_la_conexion_del_g2(sin_sesion):
    assert sin_sesion.get("/api/v1/health").json()["checks"] == {"database": "ok"}


def test_health_sin_database_url_indica_no_configurada(sin_sesion, monkeypatch):
    monkeypatch.delenv("DATABASE_URL")
    datos = sin_sesion.get("/api/v1/health").json()
    assert datos["status"] == "ok"
    assert datos["checks"] == {"database": "not_configured"}


def test_health_toma_entorno_y_version_de_variables(sin_sesion, monkeypatch):
    monkeypatch.setenv("APP_ENV", "demostracion")
    monkeypatch.setenv("APP_VERSION", "1.2.3")
    datos = sin_sesion.get("/api/v1/health").json()
    assert (datos["environment"], datos["version"]) == ("demostracion", "1.2.3")


def test_health_muestra_el_commit_desplegado(sin_sesion, monkeypatch):
    monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "3DC943C0123456789abcdef0123456789abcdef0")
    assert sin_sesion.get("/api/v1/health").json()["commit"] == "3dc943c"


@pytest.mark.parametrize("variables, esperado", [
    ({}, None),
    ({"APP_COMMIT": "abc1234"}, "abc1234"),
    ({"APP_COMMIT": "abc1234", "RAILWAY_GIT_COMMIT_SHA": "def5678"}, "abc1234"),
    ({"APP_COMMIT": "no es un commit"}, None),  # Nunca se muestra texto libre.
    ({"APP_COMMIT": "", "RAILWAY_GIT_COMMIT_SHA": "def5678"}, "def5678"),
])
def test_commit_desplegado(variables, esperado):
    assert commit_desplegado(variables) == esperado


def test_health_no_expone_secretos_del_entorno(sin_sesion, monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "valor-secreto-de-prueba")
    monkeypatch.setenv("DATABASE_URL", "mysql+pymysql://usuario:clave@servidor:3306/db_udv")
    texto = sin_sesion.get("/api/v1/health").text
    assert "valor-secreto-de-prueba" not in texto
    assert "clave@servidor" not in texto


def test_verificacion_fallida_marca_degradado_sin_detalles_internos():
    def base_caida():
        raise ConnectionError("password=abc123 host=10.0.0.5")

    estado = estado_del_servicio(iniciado_en=time.monotonic(), entorno="desarrollo",
                                 version="0.1.0", verificaciones={"database": base_caida})
    assert estado["status"] == "degraded"
    assert estado["checks"] == {"database": "error"}
    assert "abc123" not in str(estado) and "10.0.0.5" not in str(estado)


def test_verificacion_con_resultado_desconocido_cuenta_como_error():
    estado = estado_del_servicio(iniciado_en=time.monotonic(), entorno="desarrollo",
                                 version="0.1.0", verificaciones={"cola": lambda: "tal vez"})
    assert estado["checks"] == {"cola": "error"}


def test_health_responde_503_si_una_verificacion_falla(sin_sesion, monkeypatch):
    import g6_admin.salud as salud

    def base_caida():
        raise ConnectionError("sin conexión")

    monkeypatch.setitem(salud.VERIFICACIONES_PREDETERMINADAS, "database", base_caida)
    respuesta = sin_sesion.get("/api/v1/health")
    assert respuesta.status_code == 503
    assert respuesta.json()["status"] == "degraded"
