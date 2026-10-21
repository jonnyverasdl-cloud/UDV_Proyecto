# Autenticación del Grupo 2 (Persona 1: Daniel).
# POST /api/v1/auth/login  → valida correo y contraseña y entrega un token JWT.
# POST /api/v1/auth/logout → cierra la sesión: ese token deja de servir.
# GET  /api/v1/me          → quién soy, mis roles y mis permisos (nunca la contraseña).

import json
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from g2_api import config
from g2_api.database import get_db
from g2_api.models import SesionToken, Usuario
from g2_api.seguridad import crear_token, hash_token, verificar_contrasena, verificar_token

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticacion"])
me_router = APIRouter(prefix="/api/v1", tags=["Autenticacion"])  # main.py lo conecta solo si existe.


# TEMPORAL: users.py y auth_middleware.py (Randy) todavía importan esta lista.
# El login YA NO la usa. Se borra cuando users y el middleware pasen a la base.
_ruta_json = os.path.join(os.path.dirname(__file__), "..", "datos_prueba", "usuarios_prueba.json")
with open(_ruta_json, "r", encoding="utf-8") as _archivo:
    usuarios = json.load(_archivo)["usuarios"]


def _ahora_utc():
    # Hora actual en UTC sin zona (así guarda las fechas MySQL).
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---------- LOGIN ----------

# Lo que recibe el login. Si falta un campo o no es texto, FastAPI responde 422 solo.
class LoginRequest(BaseModel):
    correo: str
    password: str


# Mismo mensaje para "no existe" y "contraseña mala": así nadie puede adivinar qué correos existen.
CREDENCIALES_INVALIDAS = "Correo o contraseña incorrectos"


@router.post("/login")
def login(datos: LoginRequest, request: Request, db: Session = Depends(get_db)):
    # 1. Buscar al usuario por correo (sin contar los eliminados).
    usuario = (
        db.query(Usuario)
        .filter(Usuario.correo == datos.correo, Usuario.eliminado_en.is_(None))
        .first()
    )

    # 2. Si no existe, está inactivo o la contraseña no coincide: 401.
    if usuario is None or not usuario.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=CREDENCIALES_INVALIDAS)
    if not verificar_contrasena(datos.password, usuario.hash_contrasena):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=CREDENCIALES_INVALIDAS)

    # 3. Crear el token JWT.
    token, expira = crear_token(usuario.id)

    # 4. Guardar la sesión en sesion_token (solo el hash del token, nunca el token).
    db.add(
        SesionToken(
            usuario_id=usuario.id,
            token_hash=hash_token(token),
            tipo="access",
            expira_en=expira.replace(tzinfo=None),
            ip_origen=request.client.host if request.client else None,
            user_agent=(request.headers.get("user-agent") or "")[:300] or None,
        )
    )
    usuario.ultimo_acceso_en = _ahora_utc()
    db.commit()

    # 5. Responder con el token. El frontend lo manda después en: Authorization: Bearer <token>
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # en segundos
        "usuario": {
            "id": usuario.id,
            "correo": usuario.correo,
            "nombres": usuario.nombres,
            "apellidos": usuario.apellidos,
            "roles": [rol.codigo for rol in usuario.roles],
        },
    }


# ---------- REVISAR EL TOKEN (lo usan logout y /me) ----------

# HTTPBearer lee el header "Authorization: Bearer <token>".
# auto_error=False: si no viene, nos deja responder 401 nosotros (y no 403).
_bearer = HTTPBearer(auto_error=False)


def _no_autenticado(mensaje: str):
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=mensaje,
        headers={"WWW-Authenticate": "Bearer"},
    )


def obtener_sesion_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> SesionToken:
    # 1. ¿Mandó el token?
    if credenciales is None:
        raise _no_autenticado("Falta el token de autenticación")
    token = credenciales.credentials

    # 2. ¿La firma es válida y no ha vencido?
    payload = verificar_token(token)
    if payload is None:
        raise _no_autenticado("Token inválido o vencido")

    # 3. ¿La sesión existe en la base y no fue cerrada con logout?
    sesion = (
        db.query(SesionToken)
        .filter(SesionToken.token_hash == hash_token(token), SesionToken.revocado_en.is_(None))
        .first()
    )
    if sesion is None:
        raise _no_autenticado("La sesión no existe o ya fue cerrada")

    # 4. ¿El usuario sigue activo y no fue eliminado?
    usuario = db.get(Usuario, sesion.usuario_id)
    if usuario is None or not usuario.activo or usuario.eliminado_en is not None:
        raise _no_autenticado("El usuario no está activo")

    return sesion


# ---------- LOGOUT ----------

@router.post("/logout")
def logout(
    sesion: SesionToken = Depends(obtener_sesion_actual),
    db: Session = Depends(get_db),
):
    # Marca la sesión como cerrada. Desde ahora ese token responde 401, aunque no haya vencido.
    sesion.revocado_en = _ahora_utc()
    db.commit()
    return {"mensaje": "Sesión cerrada"}


# ---------- /me ----------

@me_router.get("/me")
def me(
    sesion: SesionToken = Depends(obtener_sesion_actual),
    db: Session = Depends(get_db),
):
    usuario = db.get(Usuario, sesion.usuario_id)

    # Permisos de todos sus roles, sin repetir y ordenados (por ejemplo: users.read).
    permisos = sorted({p.codigo for rol in usuario.roles for p in rol.permisos})

    return {
        "id": usuario.id,
        "correo": usuario.correo,
        "nombres": usuario.nombres,
        "apellidos": usuario.apellidos,
        "activo": usuario.activo,
        "roles": [rol.codigo for rol in usuario.roles],
        "permisos": permisos,
        # Nunca se devuelve hash_contrasena.
    }
