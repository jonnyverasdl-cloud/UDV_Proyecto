# Conexion a la base de datos (Persona 5). SQLite local hasta que el Grupo 1 entregue la real.
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from g2_api import config

_connect_args = {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(config.DATABASE_URL, connect_args=_connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db():
    # Dependencia de FastAPI: una sesion por peticion.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Crea las tablas si no existen.
    from g2_api import models  # noqa: F401  (registra las tablas en Base)

    Base.metadata.create_all(bind=engine)
