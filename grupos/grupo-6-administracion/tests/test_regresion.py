"""G6-40: los casos críticos de g6_admin.regresion.

Se corren sobre las rutas reales del G6. El login es de mentira (cada correo
recibe un token con su nombre) porque el del G2 necesita sus propias tablas;
contra el login real se corren en tests/integracion.
"""

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from g2_api.database import get_db
from g2_api.middleware.auth_middleware import obtener_usuario_actual
from g2_api.middleware.error_handler import register_error_handlers
from sqlalchemy import insert

from g6_admin import api, regresion, tablas

CORREOS = {"admin@demo.test": (1, "admin"), "docente@demo.test": (3, "teacher")}
CLAVE = "clave-de-prueba"


@pytest.fixture
def llamar(fabrica, monkeypatch):
    import g6_admin.salud as salud
    monkeypatch.setitem(salud.VERIFICACIONES_PREDETERMINADAS, "database", lambda: "ok")

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(api.router)

    @app.post("/api/v1/auth/login")
    def login(datos: dict):
        if datos.get("correo") not in CORREOS or datos.get("password") != CLAVE:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        with fabrica() as s:  # Igual que el G2: el login queda en la auditoría.
            s.execute(insert(tablas.auditoria).values(
                tabla="usuario", registro_id=str(CORREOS[datos["correo"]][0]),
                accion="LOGIN_OK", actor_id=CORREOS[datos["correo"]][0],
                creado_en=datetime.now(timezone.utc).replace(tzinfo=None)))
            s.commit()
        return {"access_token": datos["correo"]}

    def usuario_del_token(request: Request):
        token = request.headers.get("authorization", "").removeprefix("Bearer ")
        if token not in CORREOS:
            raise HTTPException(status_code=401, detail="Usuario no autenticado")
        id_, rol = CORREOS[token]
        return SimpleNamespace(id=id_, correo=token, activo=True,
                               roles=[SimpleNamespace(codigo=rol)])

    @app.get("/api/v1/me")
    def me(request: Request):
        return {"id": usuario_del_token(request).id}

    def sesion():
        with fabrica() as s:
            yield s

    app.dependency_overrides[obtener_usuario_actual] = usuario_del_token
    app.dependency_overrides[get_db] = sesion
    cliente = TestClient(app)

    def llamada(metodo, ruta, token, cuerpo):
        respuesta = cliente.request(metodo, ruta, json=cuerpo, headers=(
            {"Authorization": f"Bearer {token}"} if token else {}))
        return respuesta.status_code, respuesta.json()
    return llamada


def correr(llamar, clave=CLAVE):
    return regresion.ejecutar(llamar, admin=("admin@demo.test", clave),
                              docente=("docente@demo.test", clave))


def test_todos_los_casos_pasan_con_el_g6_funcionando(llamar):
    casos = correr(llamar)
    assert [c for c in casos if not c.paso] == []
    escenarios = {c.escenario for c in casos}
    assert {"G6-34", "G6-02", "G6-26", "G6-27", "G6-28", "G6-29",
            "G6-30", "G6-31", "G6-32", "G6-33"} <= escenarios


def test_no_cambia_ningun_dato(llamar, fabrica):
    correr(llamar)
    with fabrica() as s:
        assert s.execute(tablas.sede.select()).all() == []


def test_con_clave_incorrecta_falla_y_se_detiene(llamar):
    casos = correr(llamar, clave="otra")
    assert [c.descripcion for c in casos if not c.paso] == [
        "Inicia sesión administración (admin@demo.test)",
        "Inicia sesión docente (docente@demo.test)"]
    assert len(casos) == 4


def test_detecta_si_el_docente_pudiera_agregar(llamar):
    # Si alguien quitara la protección, la regresión lo marca.
    def llamada(metodo, ruta, token, cuerpo):
        if metodo == "POST" and ruta == "/api/v1/campuses":
            return 201, {"id": 1}
        return llamar(metodo, ruta, token, cuerpo)

    fallidos = [c for c in correr(llamada) if not c.paso]
    assert [c.escenario for c in fallidos] == ["G6-02"]
    assert fallidos[0].detalle == "HTTP 201"


def test_sin_servidor_todo_falla_sin_romperse():
    casos = regresion.ejecutar(regresion.llamada_http("http://127.0.0.1:9", 1),
                               admin=("a@x", "x"), docente=("d@x", "x"))
    assert casos and not any(c.paso for c in casos)


def test_el_comando_no_muestra_la_contrasena(llamar, monkeypatch, capsys):
    monkeypatch.setenv("G6_REGRESION_CLAVE", CLAVE)
    monkeypatch.setattr(regresion, "llamada_http", lambda *_: llamar)
    codigo = regresion.main(["--admin", "admin@demo.test", "--docente", "docente@demo.test"])
    salida = capsys.readouterr().out
    assert codigo == 0
    assert CLAVE not in salida
    assert "casos pasaron" in salida
