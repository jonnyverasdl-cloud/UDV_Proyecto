# Conexión a la base de datos (Persona 5).
# Motor oficial: MySQL 8 con el driver PyMySQL. La URL viene siempre de DATABASE_URL (.env).
# Regla del PM: El esquema lo crea el Grupo 1 (db_udv_completo.sql). Aquí No se crean tablas.
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from g2_api import config

# SQLite (solo pruebas locales) necesita este argumento extra para usarse con FastAPI.
_es_sqlite = config.DATABASE_URL.startswith("sqlite")
_connect_args = {"check_same_thread": False} if _es_sqlite else {}

# El engine es el "enchufe" a la base: Guarda un grupo de conexiones y las reutiliza.
# pool_pre_ping=True prueba la conexión antes de usarla (Evita errores si MySQL cerró una inactiva).
# pool_recycle evita que MySQL corte conexiones viejas (wait_timeout).
engine = create_engine(
    config.DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,
    pool_recycle=1800,
)

# SessionLocal fabrica sesiones: Una sesión es una "conversación" con la base (consultas y cambios).
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Base es la clase madre de todos los modelos de models.py.
Base = declarative_base()

def get_db():
    # Dependencia de FastAPI: abre una sesión por petición y siempre la cierra al terminar.
    # Uso en un router: def mi_endpoint(db: Session = Depends(get_db)).
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def probar_conexion():
    # Devuelve True si la base responde. Sirve para diagnóstico (no crea ni cambia nada).
    from sqlalchemy import text

    try:
        with engine.connect() as conexion:
            conexion.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
