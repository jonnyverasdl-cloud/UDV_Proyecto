# Pruebas de autenticación (Persona 1: Daniel): login, logout, /me y auditoría.
# Corren contra una base SQLite temporal (tests/conftest.py), nunca contra MySQL.
# Correr: pytest tests/test_auth.py -v

from g2_api.models import Auditoria, Permiso, Rol, RolPermiso, SesionToken, Usuario, UsuarioRol
from g2_api.seguridad import hash_token, hashear_contrasena, verificar_token

CORREO = "admin@demo.udv.edu.gt"
CLAVE = "Demo2026!"
URL = "/api/v1/auth/login"
URL_LOGOUT = "/api/v1/auth/logout"
URL_ME = "/api/v1/me"


def _crear_admin(db, activo=True):
    # Siembra el rol "admin" con un permiso y un usuario con ese rol, igual que los datos del Grupo 1.
    db.add(Rol(id=1, codigo="admin", nombre="Administrador"))
    db.add(Permiso(id=1, codigo="users.read", descripcion="Consultar usuarios"))
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
    db.add(RolPermiso(rol_id=1, permiso_id=1))
    db.add(UsuarioRol(usuario_id=1, rol_id=1))
    db.commit()


def _token(client):
    return client.post(URL, json={"correo": CORREO, "password": CLAVE}).json()["access_token"]


def _bearer(token):
    return {"Authorization": f"Bearer {token}"}


# ---------- LOGIN ----------

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
    token = _token(client)

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
    assert verificar_token(_token(client) + "x") is None


# ---------- /me ----------

def test_me_con_token_devuelve_usuario_roles_y_permisos(client, db):
    _crear_admin(db)
    r = client.get(URL_ME, headers=_bearer(_token(client)))

    assert r.status_code == 200
    datos = r.json()
    assert datos["correo"] == CORREO
    assert datos["roles"] == ["admin"]
    assert datos["permisos"] == ["users.read"]
    assert "hash_contrasena" not in datos


def test_me_sin_token_401(client, db):
    r = client.get(URL_ME)
    assert r.status_code == 401


def test_me_con_token_falso_401(client, db):
    _crear_admin(db)
    r = client.get(URL_ME, headers=_bearer("esto.no.es-un-token"))
    assert r.status_code == 401


# ---------- LOGOUT ----------

def test_logout_cierra_la_sesion(client, db):
    _crear_admin(db)
    token = _token(client)

    r = client.post(URL_LOGOUT, headers=_bearer(token))
    assert r.status_code == 200

    # La sesión quedó marcada como cerrada en la base.
    db.expire_all()
    sesion = db.query(SesionToken).filter_by(token_hash=hash_token(token)).one()
    assert sesion.revocado_en is not None


def test_despues_del_logout_el_token_ya_no_sirve(client, db):
    _crear_admin(db)
    token = _token(client)
    client.post(URL_LOGOUT, headers=_bearer(token))

    assert client.get(URL_ME, headers=_bearer(token)).status_code == 401
    assert client.post(URL_LOGOUT, headers=_bearer(token)).status_code == 401


def test_logout_sin_token_401(client, db):
    r = client.post(URL_LOGOUT)
    assert r.status_code == 401


# ---------- AUDITORÍA (G2-36) ----------

def _acciones(db):
    db.expire_all()
    return [fila.accion for fila in db.query(Auditoria).order_by(Auditoria.id).all()]


def test_login_correcto_queda_en_auditoria(client, db):
    _crear_admin(db)
    _token(client)

    fila = db.query(Auditoria).filter_by(accion="LOGIN_OK").one()
    assert fila.actor_id == 1
    assert fila.tabla == "usuario"


def test_login_fallido_queda_en_auditoria(client, db):
    _crear_admin(db)
    client.post(URL, json={"correo": CORREO, "password": "otra-clave"})
    client.post(URL, json={"correo": "nadie@demo.udv.edu.gt", "password": "x"})

    assert _acciones(db) == ["LOGIN_FALLIDO", "LOGIN_FALLIDO"]


def test_logout_queda_en_auditoria(client, db):
    _crear_admin(db)
    client.post(URL_LOGOUT, headers=_bearer(_token(client)))

    assert _acciones(db) == ["LOGIN_OK", "LOGOUT"]
