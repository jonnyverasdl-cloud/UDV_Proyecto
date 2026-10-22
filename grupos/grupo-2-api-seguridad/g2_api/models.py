# Tablas del Grupo 2 en Python (Persona 5).
# Son una copia de las tablas que el Grupo 1 creó en db_udv_completo.sql (versión 1.1.0):
# usuario, rol, permiso, rol_permiso, usuario_rol, sesion_token, archivo y auditoria.
# Estos modelos No crean tablas: solo le explican a SQLAlchemy cómo leerlas y escribirlas.
# Si el Grupo 1 cambia una tabla, se actualiza este archivo para que siga igual.
# Convención: Nombres en español, igual que la base del Grupo 1.
# Fechas: Se guardan en UTC sin zona (DATETIME de MySQL no guarda zona).

from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    CHAR,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
)
from sqlalchemy.orm import relationship

from g2_api.database import Base

def ahora_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class Usuario(Base):
    __tablename__ = "usuario"

    id = Column(Integer, primary_key=True)
    correo = Column(String(254), unique=True, nullable=False, index=True)
    id_academico = Column(String(20), unique=True, nullable=True)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    telefono = Column(String(20), nullable=True)
    hash_contrasena = Column(String(255), nullable=False) # Solo el hash bcrypt, nunca la contraseña.
    unidad_academica_id = Column(Integer, nullable=True)  # FK a unidad_academica (tabla del Grupo 1).
    activo = Column(Boolean, nullable=False, default=True)
    ultimo_acceso_en = Column(DateTime, nullable=True)
    intentos_fallidos = Column(Integer, nullable=False, default=0)  # Límite de intentos de login.
    bloqueado_hasta = Column(DateTime, nullable=True) # Fin del bloqueo por intentos fallidos.
    creado_en = Column(DateTime, nullable=False, default=ahora_utc)
    actualizado_en = Column(DateTime, nullable=False, default=ahora_utc, onupdate=ahora_utc)
    eliminado_en = Column(DateTime, nullable=True) # Eliminación lógica: Nunca se borra con DELETE.
    eliminado_por = Column(Integer, ForeignKey("usuario.id"), nullable=True)

    roles = relationship(
        "Rol",
        secondary="usuario_rol",
        primaryjoin="Usuario.id == UsuarioRol.usuario_id",
        secondaryjoin="Rol.id == UsuarioRol.rol_id",
        viewonly=True,
    )

class Rol(Base):
    __tablename__ = "rol"

    id = Column(Integer, primary_key=True)
    # Códigos oficiales sembrados por el Grupo 1: admin, coordinator, teacher, reviewer, authority, auditor.
    codigo = Column(String(30), unique=True, nullable=False)
    nombre = Column(String(80), nullable=False)
    descripcion = Column(String(300), nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(DateTime, nullable=False, default=ahora_utc)
    actualizado_en = Column(DateTime, nullable=False, default=ahora_utc, onupdate=ahora_utc)

    permisos = relationship("Permiso", secondary="rol_permiso", viewonly=True)

class Permiso(Base):
    __tablename__ = "permiso"

    id = Column(Integer, primary_key=True)
    codigo = Column(String(60), unique=True, nullable=False) # Formato modulo.accion, por ejemplo users.read.
    descripcion = Column(String(300), nullable=True)
    creado_en = Column(DateTime, nullable=False, default=ahora_utc)

class RolPermiso(Base):
    __tablename__ = "rol_permiso"

    rol_id = Column(Integer, ForeignKey("rol.id"), primary_key=True)
    permiso_id = Column(Integer, ForeignKey("permiso.id"), primary_key=True)
    creado_en = Column(DateTime, nullable=False, default=ahora_utc)

class UsuarioRol(Base):
    __tablename__ = "usuario_rol"

    usuario_id = Column(Integer, ForeignKey("usuario.id"), primary_key=True)
    rol_id = Column(Integer, ForeignKey("rol.id"), primary_key=True)
    asignado_por = Column(Integer, ForeignKey("usuario.id"), nullable=True)
    asignado_en = Column(DateTime, nullable=False, default=ahora_utc)


class SesionToken(Base):
    __tablename__ = "sesion_token"

    # BIGINT en MySQL; en SQLite (pruebas) se usa INTEGER para que sea autoincremental.
    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False, index=True)
    token_hash = Column(CHAR(64), unique=True, nullable=False)  # SHA-256 del token, nunca el token.
    # La base solo acepta 'access', 'refresh' o 'reset' (CHECK del Grupo 1).
    tipo = Column(String(10), nullable=False, default="access")
    emitido_en = Column(DateTime, nullable=False, default=ahora_utc)
    expira_en = Column(DateTime, nullable=False)
    revocado_en = Column(DateTime, nullable=True) # El logout llena esta fecha.
    ip_origen = Column(String(45), nullable=True)
    user_agent = Column(String(300), nullable=True)

class Archivo(Base):
    __tablename__ = "archivo"

    # Los archivos subidos por /files (Persona 4). Solo se guardan los metadatos; el archivo va en disco.
    id = Column(Integer, primary_key=True)
    nombre_original = Column(String(255), nullable=False)
    nombre_interno = Column(String(100), unique=True, nullable=False) # Aleatorio, solo A-Z a-z 0-9 . _ -
    tipo_mime = Column(String(127), nullable=False)
    tamano_bytes = Column(BigInteger().with_variant(Integer, "sqlite"), nullable=False)
    hash_sha256 = Column(CHAR(64), nullable=False, index=True)
    ubicacion = Column(String(500), nullable=False)
    autor_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    # Un archivo se asocia como máximo a UNA de estas tres cosas (CHECK del Grupo 1).
    # Se dejan como enteros simples porque sus tablas (entrega, comentario, programa_version) son de otros grupos.
    entrega_id = Column(Integer, nullable=True)
    comentario_id = Column(Integer, nullable=True)
    programa_version_id = Column(Integer, nullable=True)
    reemplazado_por_id = Column(Integer, ForeignKey("archivo.id"), nullable=True)
    creado_en = Column(DateTime, nullable=False, default=ahora_utc)
    eliminado_en = Column(DateTime, nullable=True)  # Eliminación lógica.
    eliminado_por = Column(Integer, ForeignKey("usuario.id"), nullable=True)

class Auditoria(Base):
    __tablename__ = "auditoria"

    # Registro de accesos y acciones sensibles (utils/registro.py de Persona 3).
    # Los intentos de login fallidos se guardan como accion LOGIN_FALLIDO (actor_id vacío si el usuario no existe).
    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    tabla = Column(String(64), nullable=False)
    registro_id = Column(String(64), nullable=False)
    accion = Column(String(20), nullable=False)
    actor_id = Column(Integer, ForeignKey("usuario.id"), nullable=True)
    ip_origen = Column(String(45), nullable=True)
    # En MySQL la columna es LONGTEXT con CHECK JSON_VALID: Con el tipo JSON de SQLAlchemy un dict se guarda como JSON válido.
    # none_as_null=True guarda NULL de verdad cuando no hay detalle (no el texto 'null').
    detalle = Column(JSON(none_as_null=True), nullable=True)
    creado_en = Column(DateTime, nullable=False, default=ahora_utc)
    
