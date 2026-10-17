"""Pruebas de catálogos: escenarios G6-01, G6-02, G6-03 y G6-21 a G6-25."""

import pytest
from g2_api.utils.paginacion import PER_PAGE_MAX

from g6_admin.catalogos import CATALOGOS

RECURSOS = list(CATALOGOS)
VALIDO = {"code": "NORTE", "name": "Sede Norte"}


def crear(cliente, recurso="campuses", datos=None):
    return cliente.post(f"/api/v1/{recurso}", json=VALIDO if datos is None else datos)


def campos_con_error(respuesta) -> set[str]:
    return {d["field"] for d in respuesta.json()["error"]["details"]}


# ── G6-01 y G6-21 a G6-25: administración agrega y el registro aparece ────

@pytest.mark.parametrize("recurso", RECURSOS)
def test_admin_agrega_registro_y_el_docente_lo_ve(admin, docente, recurso):
    respuesta = crear(admin, recurso, {"code": " norte-1 ", "name": "  Sede   Norte "})

    assert respuesta.status_code == 201
    creado = respuesta.json()
    assert creado["code"] == "NORTE-1"
    assert creado["name"] == "Sede Norte"
    assert creado["is_active"] is True

    lista = docente.get(f"/api/v1/{recurso}").json()
    assert lista["total"] == 1
    assert lista["data"][0]["id"] == creado["id"]


def test_admin_puede_agregar_registro_inactivo(admin):
    respuesta = crear(admin, datos={**VALIDO, "is_active": False})
    assert respuesta.status_code == 201
    assert respuesta.json()["is_active"] is False


def test_se_guarda_quien_agrego_el_registro(admin, servicio):
    crear(admin)
    assert servicio.repositorio.listar("campuses")[0].created_by == 1


# ── G6-02 y G6-03: el docente solo consulta; el servidor lo hace cumplir ──

@pytest.mark.parametrize("recurso", RECURSOS)
def test_docente_no_puede_agregar(admin, docente, recurso):
    respuesta = crear(docente, recurso)

    assert respuesta.status_code == 403
    assert respuesta.json()["error"]["code"] == "FORBIDDEN"
    assert admin.get(f"/api/v1/{recurso}").json()["total"] == 0


def test_docente_recibe_403_antes_que_errores_de_validacion(docente):
    # Aunque el cuerpo sea inválido, primero se revisa el permiso.
    assert crear(docente, datos={"code": "x"}).status_code == 403
    assert crear(docente, datos={"code": 123}).status_code == 403


def test_docente_puede_consultar(admin, docente):
    crear(admin)
    respuesta = docente.get("/api/v1/campuses")
    assert respuesta.status_code == 200
    assert respuesta.json()["total"] == 1


@pytest.mark.parametrize("metodo", ["get", "post"])
def test_sin_sesion_responde_401(sin_sesion, metodo):
    respuesta = getattr(sin_sesion, metodo)(
        "/api/v1/campuses", **({"json": VALIDO} if metodo == "post" else {}))
    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["code"] == "UNAUTHORIZED"


# ── Validación (422) y conflicto (409) ────────────────────────────────────

def test_campos_obligatorios_dan_422_con_detalle_por_campo(admin):
    respuesta = crear(admin, datos={})
    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["code"] == "VALIDATION_ERROR"
    assert campos_con_error(respuesta) == {"code", "name"}


@pytest.mark.parametrize("codigo", ["A", "CON ESPACIO", "SEDE-Ñ", "X" * 21, "-NORTE"])
def test_codigo_con_formato_invalido(admin, codigo):
    respuesta = crear(admin, datos={"code": codigo, "name": "Sede"})
    assert respuesta.status_code == 422
    assert "code" in campos_con_error(respuesta)


def test_nombre_demasiado_largo(admin):
    respuesta = crear(admin, datos={"code": "LARGO", "name": "a" * 121})
    assert respuesta.status_code == 422
    assert "name" in campos_con_error(respuesta)


def test_campo_no_reconocido(admin):
    respuesta = crear(admin, datos={**VALIDO, "color": "azul"})
    assert respuesta.status_code == 422
    assert "color" in campos_con_error(respuesta)


def test_tipo_de_dato_incorrecto(admin):
    respuesta = crear(admin, datos={"code": 123, "name": "Sede"})
    assert respuesta.status_code == 422
    assert "code" in campos_con_error(respuesta)


def test_codigo_duplicado_da_409_sin_importar_mayusculas(admin):
    assert crear(admin).status_code == 201
    respuesta = crear(admin, datos={"code": "norte", "name": "Otra sede"})
    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["code"] == "CONFLICT"
    assert campos_con_error(respuesta) == {"code"}


def test_mismo_codigo_se_permite_en_otro_catalogo(admin):
    assert crear(admin, "campuses").status_code == 201
    assert crear(admin, "areas").status_code == 201


def test_todo_error_usa_el_formato_comun(admin, docente, sin_sesion):
    respuestas = [
        crear(admin, datos={}),                  # 422
        crear(admin, datos={"code": 1}),         # 422 de tipo de dato
        crear(docente),                          # 403
        sin_sesion.get("/api/v1/campuses"),      # 401
        admin.get("/api/v1/no-existe"),          # 404
    ]
    for respuesta in respuestas:
        assert {"code", "message", "details"} <= set(respuesta.json()["error"])


# ── Listado: paginación, búsqueda, filtro y orden ─────────────────────────

def test_paginacion_con_la_forma_del_contrato(admin):
    for numero in range(25):
        crear(admin, datos={"code": f"S-{numero:02d}", "name": f"Sede {numero:02d}"})

    pagina = admin.get("/api/v1/campuses?page=3&per_page=10").json()
    assert set(pagina) == {"page", "per_page", "total", "data"}
    assert (pagina["page"], pagina["per_page"], pagina["total"]) == (3, 10, 25)
    assert len(pagina["data"]) == 5


@pytest.mark.parametrize("consulta", [f"per_page={PER_PAGE_MAX + 1}", "per_page=0", "page=0"])
def test_parametros_de_paginacion_fuera_de_rango(admin, consulta):
    assert admin.get(f"/api/v1/campuses?{consulta}").status_code == 422


def test_busqueda_ignora_mayusculas_y_tildes(admin):
    crear(admin, "periods", {"code": "2026-S1", "name": "Primer período 2026"})
    crear(admin, "periods", {"code": "2026-S2", "name": "Segundo período 2026"})

    resultado = admin.get("/api/v1/periods?q=PRIMER periodo").json()
    assert [r["code"] for r in resultado["data"]] == ["2026-S1"]


def test_filtro_por_activos(admin):
    crear(admin, datos={"code": "ACTIVA", "name": "Activa"})
    crear(admin, datos={"code": "CERRADA", "name": "Cerrada", "is_active": False})

    resultado = admin.get("/api/v1/campuses?active=false").json()
    assert [r["code"] for r in resultado["data"]] == ["CERRADA"]


def test_lista_ordenada_por_nombre(admin):
    for code, name in [("C", "Zacapa"), ("A", "Antigua"), ("B", "Escuintla")]:
        crear(admin, datos={"code": f"{code}{code}", "name": name})
    nombres = [r["name"] for r in admin.get("/api/v1/campuses").json()["data"]]
    assert nombres == ["Antigua", "Escuintla", "Zacapa"]


# ── OpenAPI: las rutas coinciden con el CONTRATO.md del G6 ────────────────

def test_openapi_incluye_las_rutas_de_catalogos_del_contrato(admin):
    rutas = admin.get("/openapi.json").json()["paths"]
    for recurso in RECURSOS:
        assert {"get", "post"} <= set(rutas[f"/api/v1/{recurso}"])
