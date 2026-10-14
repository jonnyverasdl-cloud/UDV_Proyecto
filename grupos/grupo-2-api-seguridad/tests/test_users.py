# Pruebas de la base del proyecto (Persona 5): Arranque, documentación, errores comunes y modelos.
# Cada persona tiene sus propias pruebas (test_auth, test_users, test_errores, test_files); estas cubren lo compartido.
from sqlalchemy import inspect, text
from sqlalchemy.orm import configure_mappers

from g2_api import models
from g2_api.database import Base, engine, probar_conexion


def test_la_app_arranca_y_muestra_la_documentacion(client):
    # La interfaz de documentación (Swagger) responde.
    respuesta = client.get("/api/v1/docs")
    assert respuesta.status_code == 200


def test_openapi_lista_las_rutas_del_contrato(client):
    # El OpenAPI se genera solo y debe incluir las rutas que ya existen.
    respuesta = client.get("/api/v1/openapi.json")
    assert respuesta.status_code == 200
    # Se quita la barra final para aceptar "/users" y "/users/" (el contrato usa la forma sin barra).
    rutas = {ruta.rstrip("/") for ruta in respuesta.json()["paths"]}
    assert "/api/v1/auth/login" in rutas
    assert "/api/v1/users" in rutas
    assert "/api/v1/roles" in rutas


def test_ruta_inexistente_responde_404_con_formato_comun(client):
    respuesta = client.get("/api/v1/esta-ruta-no-existe")
    assert respuesta.status_code == 404
    cuerpo = respuesta.json()
    assert cuerpo["error"]["code"] == "NOT_FOUND"
    assert "message" in cuerpo["error"]
    assert "details" in cuerpo["error"]


def test_login_con_cuerpo_vacio_responde_422_con_detalle_por_campo(client):
    respuesta = client.post("/api/v1/auth/login", json={})
    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["error"]["code"] == "VALIDATION_ERROR"
    campos = {d["field"] for d in cuerpo["error"]["details"]}
    assert {"correo", "password"} <= campos


def test_los_errores_no_muestran_informacion_interna(client):
    # Un 404 no debe traer rutas del servidor, SQL ni trazas.
    texto = client.get("/api/v1/nada").text.lower()
    for prohibido in ("traceback", "select ", "/home/", "c:\\", "secret"):
        assert prohibido not in texto


def test_los_modelos_coinciden_con_las_tablas_del_grupo_1():
    # Si un modelo está mal armado, configure_mappers lanza un error.
    configure_mappers()
    tablas = set(Base.metadata.tables)
    esperadas = {"usuario", "rol", "permiso", "rol_permiso", "usuario_rol", "sesion_token", "archivo", "auditoria"}
    assert esperadas <= tablas
    columnas_usuario = {c.name for c in models.Usuario.__table__.columns}
    # Estas dos columnas son las del límite de intentos de login (versión 1.1.0 de la base).
    assert {"intentos_fallidos", "bloqueado_hasta", "hash_contrasena", "eliminado_en"} <= columnas_usuario


def test_la_conexion_a_la_base_responde():
    assert probar_conexion() is True
    with engine.connect() as conexion:
        assert conexion.execute(text("SELECT 1")).scalar() == 1


def test_guardar_y_leer_un_usuario_con_su_rol(db):
    # Solo en SQLite (tablas temporales). Con MySQL no se escribe en la base compartida desde las pruebas.
    if engine.dialect.name != "sqlite":
        return
    rol = models.Rol(codigo="admin", nombre="Administrador")
    usuario = models.Usuario(
        correo="prueba@demo.udv.edu.gt", nombres="Prueba", apellidos="Base", hash_contrasena="hash-falso"
    )
    db.add_all([rol, usuario])
    db.commit()
    db.add(models.UsuarioRol(usuario_id=usuario.id, rol_id=rol.id))
    db.commit()
    leido = db.query(models.Usuario).filter_by(correo="prueba@demo.udv.edu.gt").one()
    assert [r.codigo for r in leido.roles] == ["admin"]
    assert leido.intentos_fallidos == 0
    assert "usuario_rol" in inspect(engine).get_table_names()
