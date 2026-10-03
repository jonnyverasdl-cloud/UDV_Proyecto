# Configuracion del Grupo 2: lee las variables del archivo .env (Persona 5).
import os
from dotenv import load_dotenv

load_dotenv()


def _lista(valor: str):
    return [v.strip() for v in valor.split(",") if v.strip()]


DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
SECRET_KEY: str = os.getenv("SECRET_KEY", "")
ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
CORS_ORIGINS: list[str] = _lista(os.getenv("CORS_ORIGINS", "http://localhost:5500"))
LOGIN_MAX_INTENTOS: int = int(os.getenv("LOGIN_MAX_INTENTOS", "5"))
LOGIN_BLOQUEO_MINUTOS: int = int(os.getenv("LOGIN_BLOQUEO_MINUTOS", "15"))

if not SECRET_KEY:
    raise RuntimeError("Falta SECRET_KEY: copia .env.example a .env y define un valor.")
