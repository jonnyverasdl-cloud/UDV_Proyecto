# Conexión a la base de datos (Persona 5).
# Motor oficial: MySQL 8 con el driver PyMySQL. La URL viene siempre de DATABASE_URL (.env).
# Regla del PM: El esquema lo crea el Grupo 1 (db_udv_completo.sql). Aquí No se crean tablas.
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker

from g2_api import config

# SQLite (Solo pruebas locales) necesita este argumento extra para usarse con FastAPI.
_es_sqlite = config.DATABASE_URL.startswith("sqlite")
# MySQL o MariaDB (la base del Grupo 1): Solo aquí existen las variables @actor_id y @ip_origen de los triggers.
_es_mysql = config.DATABASE_URL.startswith(("mysql", "mariadb"))
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

if _es_mysql:

    @event.listens_for(engine, "connect")
    def _al_conectar(dbapi_connection, _registro):
        # Las fechas se guardan en UTC (acuerdo con el Grupo 1): Cada conexión nueva trabaja en UTC.
        cursor = dbapi_connection.cursor()
        cursor.execute("SET time_zone = '+00:00'")
        cursor.close()

    @event.listens_for(engine, "checkin")
    def _al_devolver(dbapi_connection, _registro):
        # Las variables @actor_id y @ip_origen viven en la conexión, y el pool la reutiliza en otra petición.
        # Se limpian al devolverla para que la auditoría nunca atribuya un cambio al usuario equivocado.
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("SET @actor_id = NULL, @ip_origen = NULL")
            cursor.close()
        except Exception:
            pass  # Si la conexión ya se cerró, el pool la descarta solo.


# SessionLocal fabrica sesiones: Una sesión es una "conversación" con la base (consultas y cambios).
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Base es la clase madre de todos los modelos de models.py.
Base = declarative_base()

def get_db():
    # Dependencia de FastAPI: Abre una sesión por petición y siempre la cierra al terminar.
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


def fijar_actor(db, actor_id, ip_origen=None):
    # Le dice a los triggers del Grupo 1 quién hace el cambio: Quedan en auditoria.actor_id y auditoria.ip_origen.
    # Se llama con la misma sesión que hará el INSERT, UPDATE o DELETE, justo antes de ejecutarlo.
    # Después de cada commit la conexión vuelve al pool y las variables se limpian: Hay que llamarla otra vez.
    # En SQLite (Pruebas) no hace nada, porque esas variables solo existen en MySQL y MariaDB.
    if db.get_bind().dialect.name not in ("mysql", "mariadb"):
        return
    db.execute(
        text("SET @actor_id = :actor_id, @ip_origen = :ip_origen"),
        {"actor_id": actor_id, "ip_origen": ip_origen},
    )
