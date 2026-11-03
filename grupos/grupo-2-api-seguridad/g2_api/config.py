# Configuracion del Grupo 2: lee las variables del archivo .env (Persona 5).
import os
from dotenv import load_dotenv

load_dotenv()

def _lista(valor: str):
    return [v.strip() for v in valor.split(",") if v.strip()]

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
SECRET_KEY = os.getenv("SECRET_KEY", "7a798a51457d0d2a4657ad00a9af948e73c31ee4de77c59bc7c0b2e8ade3f7f4")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES= int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
CORS_ORIGINS = _lista(os.getenv("CORS_ORIGINS", "http://localhost:5500"))
LOGIN_MAX_INTENTOS = int(os.getenv("LOGIN_MAX_INTENTOS", "5"))
LOGIN_BLOQUEO_MINUTOS = int(os.getenv("LOGIN_BLOQUEO_MINUTOS", "15"))
CONTRASENA_MIN = int(os.getenv("CONTRASENA_MIN", "8")) # largo minimo de la contraseña (Persona 1).
CONTRASENA_MAX = int(os.getenv("CONTRASENA_MAX", "64")) # largo maximo de la contraseña (Persona 1).
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "almacen_archivos") # Carpeta donde files.py guarda los archivos (Persona 4).

if not SECRET_KEY:
    raise RuntimeError("Falta SECRET_KEY: copia .env.example a .env y define un valor.")
