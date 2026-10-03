# Tablas de seguridad (Persona 5).
# Copia exacta del diagrama de seguridad CONFIRMADO por el Grupo 1:
# usuario, rol, permiso, rol_permiso, usuario_rol y sesion_token.
# Convencion: nombres en espanol, igual que la base del Grupo 1.
# Fechas: se guardan en UTC sin zona (DATETIME de MySQL no guarda zona).

from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    CHAR,
    Column,
    DateTime,
    ForeignKey,
    Integer,
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
    id_academico = Column(String(20), nullable=True)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    telefono = Column(String(20), nullable=True)
    hash_contrasena = Column(String(255), nullable=False)  # solo hash bcrypt
    unidad_academica_id = Column(Integer, nullable=True)  # FK a la tabla de unidades del Grupo 1
    activo = Column(Boolean, nullable=False, default=True)
    ultimo_acceso_en = Column(DateTime, nullable=True)
    creado_en = Column(DateTime, nullable=False, default=ahora_utc)
    actualizado_en = Column(DateTime, nullable=False, default=ahora_utc, onupdate=ahora_utc)
    eliminado_en = Column(DateTime, nullable=True)  # eliminacion logica
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
    codigo = Column(String(60), unique=True, nullable=False)
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

    # BIGINT en MySQL; en SQLite (pruebas) se usa INTEGER para que sea autoincremental
    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False, index=True)
    token_hash = Column(CHAR(64), unique=True, nullable=False)  # SHA-256 del token, nunca el token
    tipo = Column(String(10), nullable=False, default="acceso")
    emitido_en = Column(DateTime, nullable=False, default=ahora_utc)
    expira_en = Column(DateTime, nullable=False)
    revocado_en = Column(DateTime, nullable=True)  # el logout llena esta fecha
    ip_origen = Column(String(45), nullable=True)
    user_agent = Column(String(300), nullable=True)
