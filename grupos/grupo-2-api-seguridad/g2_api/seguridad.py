# Las usan: routers/auth.py (login, logout, /me) y middleware/auth_middleware.py (Randy).

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from g2_api import config


# ---------- Contraseñas (bcrypt) ----------

def hashear_contrasena(contrasena: str) -> str:
    # Convierte la contraseña en un hash bcrypt. Es de una sola vía: no se puede "deshacer".
    # gensalt() agrega una sal aleatoria: dos usuarios con la misma clave tienen hashes distintos.
    return bcrypt.hashpw(contrasena.encode(), bcrypt.gensalt()).decode()


def verificar_contrasena(contrasena: str, hash_guardado: str) -> bool:
    # Compara la contraseña escrita con el hash de la base. True si coinciden.
    try:
        return bcrypt.checkpw(contrasena.encode(), hash_guardado.encode())
    except ValueError:
        # El hash guardado no es un hash bcrypt válido.
        return False


# ---------- Tokens (JWT con PyJWT) ----------

def crear_token(usuario_id: int) -> tuple[str, datetime]:
    # Arma un token JWT firmado con la SECRET_KEY del .env.
    # Devuelve el token y la fecha en que expira.
    ahora = datetime.now(timezone.utc)
    expira = ahora + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)

    # El "payload" son los datos que viajan dentro del token (se pueden leer, NO son secretos).
    payload = {
        "sub": str(usuario_id),          # sub = "subject": de quién es el token. PyJWT exige texto.
        "iat": ahora,                    # iat = "issued at": cuándo se creó.
        "exp": expira,                   # exp = "expiration": cuándo vence. PyJWT lo revisa solo.
        "jti": secrets.token_hex(16),    # jti = id único: dos logins seguidos nunca dan el mismo token.
        "tipo": "access",
    }

    token = jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return token, expira


def verificar_token(token: str) -> dict | None:
    # Revisa que el token tenga una firma válida y que no haya vencido.
    # Devuelve el payload si está bien, o None si está alterado, vencido o mal formado.
    try:
        return jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
    except jwt.InvalidTokenError:
        # Incluye ExpiredSignatureError (vencido) e InvalidSignatureError (alterado).
        return None


def hash_token(token: str) -> str:
    # SHA-256 del token: es lo que se guarda en sesion_token.token_hash (CHAR(64)).
    # Nunca guardamos el token tal cual: si alguien roba la base, no puede usar los tokens.
    return hashlib.sha256(token.encode()).hexdigest()
