# POST /api/v1/auth/login: valida correo y contraseña contra la base del Grupo 1 y entrega un token JWT.

import json
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from g2_api import config
from g2_api.database import get_db
from g2_api.models import SesionToken, Usuario
from g2_api.seguridad import crear_token, hash_token, verificar_contrasena

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticacion"])


# TEMPORAL: users.py y auth_middleware.py (Randy) todavía importan esta lista.
# El login YA NO la usa. Se borra cuando users y el middleware pasen a la base (semana 2).
_ruta_json = os.path.join(os.path.dirname(__file__), "..", "datos_prueba", "usuarios_prueba.json")
with open(_ruta_json, "r", encoding="utf-8") as _archivo:
    usuarios = json.load(_archivo)["usuarios"]


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
    #    Sirve para el logout: se marca revocado_en y ese token deja de servir.
    #    MySQL guarda DATETIME sin zona, por eso se quita tzinfo (queda en UTC).
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
    usuario.ultimo_acceso_en = datetime.now(timezone.utc).replace(tzinfo=None)
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
