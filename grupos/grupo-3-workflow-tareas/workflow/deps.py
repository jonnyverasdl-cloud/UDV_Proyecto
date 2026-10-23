"""Dependencias compartidas de la capa HTTP (conexión a la base)."""
from .db import connect, get_database_url


def get_conn():
    """Una conexión por petición, tomada de DATABASE_URL (.env). Se cierra al terminar."""
    conn = connect(get_database_url())
    try:
        yield conn
    finally:
        conn.close()
