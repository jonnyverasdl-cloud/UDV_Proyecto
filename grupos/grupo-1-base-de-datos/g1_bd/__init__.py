"""g1_bd: crea y verifica la base db_udv con los scripts SQL del Grupo 1.

    python -m g1_bd crear       borra y crea db_udv (01_schema.sql + 02_seed.sql)
    python -m g1_bd verificar   corre verificacion.sql y muestra el resultado

La conexión sale de DATABASE_URL (mysql+pymysql://usuario:clave@host:puerto/db_udv)
o de --host, --port, --user y --password.
"""
from g1_bd.base import conectar, ejecutar_script, separar_sentencias  # noqa: F401
