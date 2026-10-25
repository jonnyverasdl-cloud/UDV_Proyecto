# Pruebas de usuarios y permisos (Persona 2: Randy): users.py y auth_middleware.py.
# Corren contra la base SQLite temporal de tests/conftest.py, nunca contra MySQL.
# Usan las fixtures `client` y `db` de conftest.py (la base se limpia en cada prueba).
# Correr: python -m pytest tests/test_users.py -v

import uuid

import pytest

from g2_api.models import Rol, Usuario, UsuarioRol
from g2_api.seguridad import hashear_contrasena

URL = "/api/v1/users"
LOGIN = "/api/v1/auth/login"

#El docente es para probar el error 403
ADMIN_CORREO = "admin@demo.udv.edu.gt"
ADMIN_CLAVE = "Demo2026!"
DOCENTE_CORREO = "docente@demo.udv.edu.gt"
DOCENTE_CLAVE = "Docente2026!"
CLAVE_NUEVA = "Abc12345!"


_HASH_ADMIN = hashear_contrasena(ADMIN_CLAVE)
_HASH_DOCENTE = hashear_contrasena(DOCENTE_CLAVE)



def _sembrar(db):
    #Dos roles y usuarios para pruebas con los códigos y roles requeridos
    db.add(Rol(id=1, codigo="admin", nombre="Administrador"))
    db.add(Rol(id=2, codigo="teacher", nombre="Docente"))
    db.add(Usuario(id=1, correo=ADMIN_CORREO, nombres="Admin", apellidos="Pruebas",
                   hash_contrasena=_HASH_ADMIN, activo=True))
    db.add(Usuario(id=2, correo=DOCENTE_CORREO, nombres="Docente", apellidos="Pruebas",
                   hash_contrasena=_HASH_DOCENTE, activo=True))
    db.flush()
    db.add(UsuarioRol(usuario_id=1, rol_id=1))
    db.add(UsuarioRol(usuario_id=2, rol_id=2))
    db.commit()


def _login(client, correo, clave):
    r = client.post(LOGIN, json={"correo": correo, "password": clave})
    assert r.status_code == 200, f"No se pudo iniciar sesión como {correo}: {r.text}"
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

#prepara el entorno de prueba
@pytest.fixture()
def sembrado(db):
    _sembrar(db)


@pytest.fixture()
def headers_admin(client, sembrado):
    return _login(client, ADMIN_CORREO, ADMIN_CLAVE)


@pytest.fixture()
def headers_docente(client, sembrado):
    return _login(client, DOCENTE_CORREO, DOCENTE_CLAVE)


def _cuerpo(**cambios):
    # Cuerpo válido para POST /users, con un correo distinto en cada llamada
    cuerpo = {
        "nombres": "Ana",
        "apellidos": "Lopez",
        "correo": f"prueba_{uuid.uuid4().hex[:8]}@udv.com.gt",
        "password": CLAVE_NUEVA,
        "rol": "teacher",
        "activo": True,
    }
    cuerpo.update(cambios)
    return cuerpo

#Crea un docente de prueba
def _crear(client, headers, **cambios):
    r = client.post(URL, json=_cuerpo(**cambios), headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def _correos(client, headers):
    
    r = client.get(URL, params={"per_page": 100}, headers=headers)
    assert r.status_code == 200, r.text
    return [u["correo"] for u in r.json()["data"]]


def _assert_error(r, estado, codigo):
    # {"error": {"code", "message", "details"}}
    assert r.status_code == estado, r.text
    cuerpo = r.json()
    assert set(cuerpo.keys()) == {"error"}
    assert set(cuerpo["error"].keys()) == {"code", "message", "details"}
    assert cuerpo["error"]["code"] == codigo


# Se crea una petición por cada endpoint del archivo users.py
ENDPOINTS = [
    pytest.param("get", URL, {}, id="GET-lista"),
    pytest.param("get", f"{URL}/1", {}, id="GET-por-id"),
    pytest.param("post", URL, {"json": _cuerpo()}, id="POST-crear"),
    pytest.param("patch", f"{URL}/1", {"json": {"activo": False}}, id="PATCH"),
]


#pruebas sin autenticación

@pytest.mark.parametrize("metodo, ruta, extra", ENDPOINTS)
def test_sin_token_401(client, metodo, ruta, extra):
    r = getattr(client, metodo)(ruta, **extra)
    _assert_error(r, 401, "UNAUTHORIZED")


def test_token_basura_401(client):
    r = client.get(URL, headers={"Authorization": "Bearer abc123"})
    _assert_error(r, 401, "UNAUTHORIZED")


def test_distinto_bearer_401(client):
    r = client.get(URL, headers={"Authorization": "Basic YWRtaW46MTIz"})
    assert r.status_code == 401


def test_token_modificado_401(client, headers_admin):
    token = headers_admin["Authorization"].split(" ", 1)[1]
    encabezado, payload, firma = token.split(".")
    firma = ("A" if firma[0] != "A" else "B") + firma[1:]    # se altera la firma
    alterado = ".".join([encabezado, payload, firma])
    r = client.get(URL, headers={"Authorization": f"Bearer {alterado}"})
    assert r.status_code == 401


def test_el_correo_no_autentica(client, sembrado):
    
    r = client.get(URL, headers={"usuario-actual": ADMIN_CORREO})
    assert r.status_code == 401


# Prueba de autenticado pero sin permiso 

@pytest.mark.parametrize("metodo, ruta, extra", ENDPOINTS)
def test_docente_sin_permiso_403(client, headers_docente, metodo, ruta, extra):
    r = getattr(client, metodo)(ruta, headers=headers_docente, **extra)
    _assert_error(r, 403, "FORBIDDEN")


def test_usuario_no_puede_ver_a_otro_usuario_403(client, headers_docente):
    
    assert client.get(f"{URL}/1", headers=headers_docente).status_code == 403


def test_403_no_crea_el_usuario(client, headers_docente, headers_admin):
    cuerpo = _cuerpo()
    assert client.post(URL, json=cuerpo, headers=headers_docente).status_code == 403
    assert cuerpo["correo"] not in _correos(client, headers_admin)


# prueba de listar y consultar

def test_admin_lista_usuarios_200(client, headers_admin):
    r = client.get(URL, headers=headers_admin)
    assert r.status_code == 200
    correos = [u["correo"] for u in r.json()["data"]]
    assert ADMIN_CORREO in correos and DOCENTE_CORREO in correos


def test_admin_consulta_un_usuario_200(client, headers_admin):
    r = client.get(f"{URL}/1", headers=headers_admin)
    assert r.status_code == 200
    datos = r.json()
    assert datos["id"] == 1
    assert datos["correo"] == ADMIN_CORREO
    assert datos["roles"] == ["admin"]

#no muestra las contraseñas
def test_no_muestra_contrasena(client, headers_admin):
    
    textos = [
        client.get(URL, headers=headers_admin).text,
        client.get(f"{URL}/1", headers=headers_admin).text,
        client.post(URL, json=_cuerpo(), headers=headers_admin).text,
    ]
    for texto in textos:
        assert "hash_contrasena" not in texto
        assert "password" not in texto.lower()
        assert "$2b$" not in texto


# not found 404

def test_consultar_usuario_inexistente_404(client, headers_admin):
    r = client.get(f"{URL}/999999", headers=headers_admin)
    _assert_error(r, 404, "NOT_FOUND")


def test_actualizar_usuario_inexistente_404(client, headers_admin):
    r = client.patch(f"{URL}/999999", json={"activo": False}, headers=headers_admin)
    _assert_error(r, 404, "NOT_FOUND")


def test_id_no_numerico_422(client, headers_admin):
    r = client.get(f"{URL}/abc", headers=headers_admin)
    _assert_error(r, 422, "VALIDATION_ERROR")


# se genera el id automáticamente

def test_crear_usuario_201(client, headers_admin):
    cuerpo = _cuerpo()
    r = client.post(URL, json=cuerpo, headers=headers_admin)
    assert r.status_code == 201
    datos = r.json()
    assert datos["correo"] == cuerpo["correo"]
    assert datos["roles"] == ["teacher"]
    assert datos["activo"] is True


def test_el_id_lo_genera_el_sistema(client, headers_admin):
    primero = _crear(client, headers_admin)
    segundo = _crear(client, headers_admin)
    assert primero["id"] == 3            
    assert segundo["id"] == 4


def test_el_id_enviado_por_el_cliente_se_ignora(client, headers_admin):
    r = client.post(URL, json=_cuerpo(id=999), headers=headers_admin)
    assert r.status_code == 201
    assert r.json()["id"] != 999


def test_el_usuario_creado_puede_iniciar_sesion(client, headers_admin):
    
    usuario = _crear(client, headers_admin, password="Otra-Clave-2026!")
    r = client.post(LOGIN, json={"correo": usuario["correo"], "password": "Otra-Clave-2026!"})
    assert r.status_code == 200


def test_usuario_creado_aparece_en_el_listado(client, headers_admin):
    usuario = _crear(client, headers_admin)
    assert usuario["correo"] in _correos(client, headers_admin)


# prueba para el correo repetido

def test_correo_repetido_409_y_no_se_duplica(client, headers_admin):
    cuerpo = _cuerpo()
    assert client.post(URL, json=cuerpo, headers=headers_admin).status_code == 201

    r = client.post(URL, json=cuerpo, headers=headers_admin)
    _assert_error(r, 409, "CONFLICT")

    assert _correos(client, headers_admin).count(cuerpo["correo"]) == 1


def test_correo_de_un_usuario_existente_409(client, headers_admin):
    r = client.post(URL, json=_cuerpo(correo=ADMIN_CORREO), headers=headers_admin)
    assert r.status_code == 409


def test_actualizar_a_un_correo_ya_registrado_409(client, headers_admin):
    usuario = _crear(client, headers_admin)
    r = client.patch(f"{URL}/{usuario['id']}", json={"correo": ADMIN_CORREO}, headers=headers_admin)
    assert r.status_code == 409


# Prueba para validar entradas

def test_rol_inexistente_400(client, headers_admin):
    r = client.post(URL, json=_cuerpo(rol="rol-que-no-existe"), headers=headers_admin)
    assert r.status_code == 400


@pytest.mark.parametrize("campo", ["password"])
def test_campo_obligatorio_faltante_422(client, headers_admin, campo):
    cuerpo = _cuerpo()
    del cuerpo[campo]
    r = client.post(URL, json=cuerpo, headers=headers_admin)
    _assert_error(r, 422, "VALIDATION_ERROR")
    campos = r.json()["error"]["details"]["campos"]
    assert any(campo in c["campo"] for c in campos)     


def test_tipo_de_dato_incorrecto_422(client, headers_admin):
    r = client.post(URL, json=_cuerpo(activo="quizas"), headers=headers_admin)
    _assert_error(r, 422, "VALIDATION_ERROR")


@pytest.mark.xfail(
    reason="Pasarán cuando UsuarioCreate use Field(min_length=...) y EmailStr",
    strict=False,
)
@pytest.mark.parametrize(
    "campo, valor",
    [
        ("password", "1"),
    ],
)
def test_valores_vacios_o_con_formato_invalido_422(client, headers_admin, campo, valor):
    r = client.post(URL, json=_cuerpo(**{campo: valor}), headers=headers_admin)
    assert r.status_code == 422

#creacion de entorno para XSS Inyeccion SQL

@pytest.mark.parametrize(
    "texto",
    [
        "<script>alert(1)</script>",          
        "x'); DROP TABLE usuario;--",         
        "' OR '1'='1",                        
    ],
)
def test_entradas_maliciosas_se_tratan_como_texto(client, headers_admin, texto):
    r = client.post(URL, json=_cuerpo(nombres=texto), headers=headers_admin)
    assert r.status_code in (201, 422)
    if r.status_code == 201:
        assert r.json()["nombres"] == texto     
        assert "application/json" in r.headers["content-type"]

    
    assert ADMIN_CORREO in _correos(client, headers_admin)


# Pruebas para paginación

def test_paginacion_por_defecto(client, headers_admin):
    r = client.get(URL, headers=headers_admin)
    assert r.status_code == 200
    cuerpo = r.json()
    assert set(cuerpo.keys()) == {"page", "per_page", "total", "data"}
    assert cuerpo["page"] == 1
    assert cuerpo["per_page"] == 20
    assert cuerpo["total"] == 2          
    assert len(cuerpo["data"]) == 2


def test_paginacion_con_per_page(client, headers_admin):
    for _ in range(3):
        _crear(client, headers_admin)

    r = client.get(URL, params={"page": 1, "per_page": 2}, headers=headers_admin)
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["page"] == 1
    assert cuerpo["per_page"] == 2
    assert cuerpo["total"] == 5          #
    assert len(cuerpo["data"]) == 2


def test_las_paginas_no_repiten_usuarios(client, headers_admin):
    for _ in range(3):
        _crear(client, headers_admin)

    ids = []
    for pagina in (1, 2, 3):
        r = client.get(URL, params={"page": pagina, "per_page": 2}, headers=headers_admin)
        ids += [u["id"] for u in r.json()["data"]]
    assert sorted(ids) == [1, 2, 3, 4, 5]      # ninguno repetido y ninguno perdido


def test_pagina_fuera_de_rango_devuelve_data_vacia(client, headers_admin):
    r = client.get(URL, params={"page": 9999, "per_page": 10}, headers=headers_admin)
    assert r.status_code == 200
    assert r.json()["data"] == []


@pytest.mark.parametrize("params", [{"page": 0}, {"per_page": 0}, {"per_page": 101}, {"page": "abc"}])
def test_parametros_de_paginacion_invalidos_422(client, headers_admin, params):
    r = client.get(URL, params=params, headers=headers_admin)
    _assert_error(r, 422, "VALIDATION_ERROR")


def test_la_lista_paginada_no_expone_contrasenas(client, headers_admin):
    texto = client.get(URL, headers=headers_admin).text
    assert "hash_contrasena" not in texto and "$2b$" not in texto


# Pruebas para actualizar y desactivar

def test_actualizar_nombres_200(client, headers_admin):
    usuario = _crear(client, headers_admin)
    r = client.patch(f"{URL}/{usuario['id']}", json={"nombres": "Nombre Nuevo"}, headers=headers_admin)
    assert r.status_code == 200
    assert r.json()["nombres"] == "Nombre Nuevo"
    assert client.get(f"{URL}/{usuario['id']}", headers=headers_admin).json()["nombres"] == "Nombre Nuevo"


def test_cambiar_el_rol_reemplaza_al_anterior(client, headers_admin):
    usuario = _crear(client, headers_admin)
    r = client.patch(f"{URL}/{usuario['id']}", json={"rol": "admin"}, headers=headers_admin)
    assert r.status_code == 200
    assert r.json()["roles"] == ["admin"]      


def test_cambiar_a_un_rol_inexistente_400(client, headers_admin):
    usuario = _crear(client, headers_admin)
    r = client.patch(f"{URL}/{usuario['id']}", json={"rol": "no-existe"}, headers=headers_admin)
    assert r.status_code == 400


def test_cambiar_la_contrasena(client, headers_admin):
    usuario = _crear(client, headers_admin, password="Primera-Clave-1!")
    r = client.patch(f"{URL}/{usuario['id']}", json={"password": "Segunda-Clave-2!"}, headers=headers_admin)
    assert r.status_code == 200

    viejo = client.post(LOGIN, json={"correo": usuario["correo"], "password": "Primera-Clave-1!"})
    nuevo = client.post(LOGIN, json={"correo": usuario["correo"], "password": "Segunda-Clave-2!"})
    assert viejo.status_code == 401
    assert nuevo.status_code == 200


def test_usuario_desactivado_pierde_el_acceso(client, headers_admin):
    usuario = _crear(client, headers_admin, password="Clave-Activa-1!")
    headers_usuario = _login(client, usuario["correo"], "Clave-Activa-1!")

    r = client.patch(f"{URL}/{usuario['id']}", json={"activo": False}, headers=headers_admin)
    assert r.status_code == 200
    assert r.json()["activo"] is False

    
    login = client.post(LOGIN, json={"correo": usuario["correo"], "password": "Clave-Activa-1!"})
    assert login.status_code == 401
    
    assert client.get(URL, headers=headers_usuario).status_code == 401