# Pruebas del login (Persona 1: Daniel).
# Corren contra una base SQLite temporal (tests/conftest.py), nunca contra MySQL.
# Correr: pytest tests/test_auth.py -v

from g2_api.models import Rol, SesionToken, Usuario, UsuarioRol
from g2_api.seguridad import hash_token, hashear_contrasena, verificar_token

CORREO = "admin@demo.udv.edu.gt"
CLAVE = "Demo2026!"
URL = "/api/v1/auth/login"


def _crear_admin(db, activo=True):
    # Siembra un rol "admin" y un usuario con ese rol, igual que los datos del Grupo 1.
    db.add(Rol(id=1, codigo="admin", nombre="Administrador"))
    db.add(
        Usuario(
            id=1,
            correo=CORREO,
            nombres="Ana",
            apellidos="Administradora",
            hash_contrasena=hashear_contrasena(CLAVE),
            activo=activo,
        )
    )
    db.flush()
    db.add(UsuarioRol(usuario_id=1, rol_id=1))
    db.commit()


def test_login_correcto_devuelve_token(client, db):
    _crear_admin(db)
    r = client.post(URL, json={"correo": CORREO, "password": CLAVE})

    assert r.status_code == 200
    datos = r.json()
    assert datos["token_type"] == "bearer"
    assert datos["usuario"]["roles"] == ["admin"]
    assert "hash_contrasena" not in datos["usuario"]

    payload = verificar_token(datos["access_token"])
    assert payload is not None
    assert payload["sub"] == "1"


def test_login_guarda_solo_el_hash_del_token(client, db):
    _crear_admin(db)
    token = client.post(URL, json={"correo": CORREO, "password": CLAVE}).json()["access_token"]

    sesion = db.query(SesionToken).filter_by(usuario_id=1).one()
    assert sesion.token_hash == hash_token(token)
    assert sesion.token_hash != token
    assert sesion.revocado_en is None


def test_login_contrasena_incorrecta_401(client, db):
    _crear_admin(db)
    r = client.post(URL, json={"correo": CORREO, "password": "otra-clave"})
    assert r.status_code == 401


def test_login_correo_inexistente_401(client, db):
    _crear_admin(db)
    r = client.post(URL, json={"correo": "nadie@demo.udv.edu.gt", "password": CLAVE})
    assert r.status_code == 401


def test_login_usuario_inactivo_401(client, db):
    _crear_admin(db, activo=False)
    r = client.post(URL, json={"correo": CORREO, "password": CLAVE})
    assert r.status_code == 401


def test_login_sin_password_422(client, db):
    r = client.post(URL, json={"correo": CORREO})
    assert r.status_code == 422


def test_token_alterado_no_es_valido(client, db):
    _crear_admin(db)
    token = client.post(URL, json={"correo": CORREO, "password": CLAVE}).json()["access_token"]
    assert verificar_token(token + "x") is None
