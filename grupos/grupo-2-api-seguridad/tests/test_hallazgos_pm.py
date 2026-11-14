# Pruebas de los hallazgos del PM en la integracion (12-nov).
# Usan la misma base SQLite temporal que las demas pruebas.

from datetime import datetime, timezone

import pytest

from g2_api.models import Archivo, Permiso, Rol, RolPermiso, Usuario, UsuarioRol
from g2_api.seguridad import hashear_contrasena
from tests.test_users import (
    DOCENTE_CORREO, DOCENTE_CLAVE, URL, _cuerpo, _login, headers_admin, headers_docente, sembrado,
)

CLAVE = "Prueba2026!"


def _usuario_con_rol(db, uid, correo, codigo_rol, permisos):
    # crea un rol con sus permisos y un usuario con ese rol
    rol = Rol(id=uid + 10, codigo=codigo_rol, nombre=codigo_rol)
    db.add(rol)
    for i, codigo in enumerate(permisos):
        db.add(Permiso(id=uid * 10 + i, codigo=codigo, descripcion=codigo))
    db.add(Usuario(id=uid, correo=correo, nombres="Prueba", apellidos="Rol",
                   hash_contrasena=hashear_contrasena(CLAVE), activo=True))
    db.flush()
    for i, _ in enumerate(permisos):
        db.add(RolPermiso(rol_id=rol.id, permiso_id=uid * 10 + i))
    db.add(UsuarioRol(usuario_id=uid, rol_id=rol.id))
    db.commit()


def _archivo(db, tmp_path, autor_id, eliminado=False):
    # guarda un PDF de prueba del autor y devuelve su id
    ruta = tmp_path / "evidencia.pdf"
    ruta.write_bytes(b"%PDF-1.4 prueba")
    fila = Archivo(nombre_original="evidencia.pdf", nombre_interno="evidencia.pdf",
                   tipo_mime="application/pdf", tamano_bytes=15, hash_sha256="0" * 64,
                   ubicacion=str(ruta), autor_id=autor_id,
                   eliminado_en=datetime.now(timezone.utc).replace(tzinfo=None) if eliminado else None)
    db.add(fila)
    db.commit()
    return fila.id


# ---------- 1 y 2: archivos ----------

def test_revisor_descarga_la_evidencia_del_docente(client, db, sembrado, tmp_path):
    _usuario_con_rol(db, 5, "revisor@demo.udv.edu.gt", "reviewer", ["files.download"])
    archivo_id = _archivo(db, tmp_path, autor_id=2)
    headers = _login(client, "revisor@demo.udv.edu.gt", CLAVE)
    assert client.get(f"/api/v1/files/{archivo_id}", headers=headers).status_code == 200


def test_docente_no_dueno_no_descarga(client, db, sembrado, tmp_path):
    # el docente tiene files.download (como en la matriz del G1), pero no es dueño
    db.add(Permiso(id=99, codigo="files.download", descripcion="Descargar archivos"))
    db.flush()
    db.add(RolPermiso(rol_id=2, permiso_id=99))
    db.commit()
    archivo_id = _archivo(db, tmp_path, autor_id=1)
    headers = _login(client, DOCENTE_CORREO, DOCENTE_CLAVE)
    assert client.get(f"/api/v1/files/{archivo_id}", headers=headers).status_code == 403


def test_archivo_eliminado_da_404(client, db, sembrado, tmp_path, headers_docente):
    archivo_id = _archivo(db, tmp_path, autor_id=2, eliminado=True)
    assert client.get(f"/api/v1/files/{archivo_id}", headers=headers_docente).status_code == 404


def test_tipo_no_permitido_dice_el_motivo(client, headers_docente):
    r = client.post("/api/v1/files", files={"file": ("imagen.gif", b"GIF89a" + b"\x00" * 40, "image/gif")},
                    headers=headers_docente)
    assert r.status_code == 400
    assert "PDF" in r.json()["error"]["message"]


# ---------- 3 y 4: validacion con 422, nunca 500 ----------

@pytest.mark.parametrize("cambios", [
    {"nombres": "x" * 300},
    {"apellidos": "x" * 300},
    {"correo": "no-es-correo"},
])
def test_crear_usuario_con_datos_invalidos_422(client, headers_admin, cambios):
    r = client.post(URL, json=_cuerpo(**cambios), headers=headers_admin)
    assert r.status_code == 422


@pytest.mark.parametrize("codigo", ["Jefe-Area", "x" * 31, ""])
def test_crear_rol_con_codigo_invalido_422(client, headers_admin, codigo):
    r = client.post("/api/v1/roles", json={"codigo": codigo, "nombre": "Jefe"}, headers=headers_admin)
    assert r.status_code == 422


# ---------- 5: coordinacion puede leer usuarios ----------

def test_coordinacion_lee_usuarios(client, db, sembrado):
    _usuario_con_rol(db, 7, "coordinacion@demo.udv.edu.gt", "coordinator", ["users.read"])
    headers = _login(client, "coordinacion@demo.udv.edu.gt", CLAVE)
    assert client.get(URL, headers=headers).status_code == 200
    assert client.get(f"{URL}/1", headers=headers).status_code == 200
    assert client.post(URL, json=_cuerpo(), headers=headers).status_code == 403
