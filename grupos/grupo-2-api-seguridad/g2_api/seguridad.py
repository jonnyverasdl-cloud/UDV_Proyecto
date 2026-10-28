# Las usan: routers/auth.py (login, logout, /me) y middleware/auth_middleware.py (Randy).

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from g2_api import config


# Contraseñas (bcrypt)

def hashear_contrasena(contrasena: str) -> str:
    # Convierte la contraseña en un hash bcrypt.
    return bcrypt.hashpw(contrasena.encode(), bcrypt.gensalt()).decode()


def verificar_contrasena(contrasena: str, hash_guardado: str) -> bool:
    # Compara la contraseña escrita con el hash de la base. True es es correcto
    try:
        return bcrypt.checkpw(contrasena.encode(), hash_guardado.encode())
    except ValueError:
        return False


# Tokens (JWT con PyJWT)

def crear_token(usuario_id: int) -> tuple[str, datetime]:
    # Arma un token JWT firmado con la SECRET_KEY del .env.
    # Devuelve el token y la fecha
    ahora = datetime.now(timezone.utc)
    expira = ahora + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(usuario_id),         
        "iat": ahora,                    
        "exp": expira,                   
        "jti": secrets.token_hex(16),    
        "tipo": "access",
    }

    token = jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return token, expira


def verificar_token(token: str) -> dict | None:
    # Revisa que el token tenga una firma válida
    try:
        return jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
    except jwt.InvalidTokenError:
        # Incluye ExpiredSignatureError (vencido) e InvalidSignatureError (alterado).
        return None


def hash_token(token: str) -> str:
    # Nunca guardamos el token tal cual
    return hashlib.sha256(token.encode()).hexdigest()
