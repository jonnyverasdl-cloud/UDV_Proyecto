# Configuración del Grupo 4: lee las variables del archivo .env.
# Mismo patrón que g2_api/config.py, para no inventar una forma distinta.
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev_g4.db")
