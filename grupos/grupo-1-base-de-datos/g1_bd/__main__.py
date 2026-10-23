"""Comandos del Grupo 1: python -m g1_bd crear | verificar"""
import argparse
import sys

from g1_bd.base import conectar, ejecutar_script

CONTEO = """
SELECT (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'db_udv' AND table_type = 'BASE TABLE'),
       (SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'db_udv'),
       (SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema = 'db_udv'),
       (SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema = 'db_udv')"""


def crear(con):
    for archivo in ("01_schema.sql", "02_seed.sql"):
        n, _ = ejecutar_script(con, archivo)
        print(f"{archivo}: {n} sentencias")
    with con.cursor() as cur:
        cur.execute(CONTEO)
        tablas, vistas, triggers, rutinas = cur.fetchone()
    print(f"db_udv creada: {tablas} tablas, {vistas} vistas, {triggers} triggers, {rutinas} procedimientos y funciones")
    return 0


def verificar(con):
    con.select_db("db_udv")
    _, resultado = ejecutar_script(con, "verificacion.sql")
    if not resultado:
        print("verificacion.sql no devolvió resultados")
        return 1
    columnas, filas = resultado
    i_res, i_prueba, i_msg = columnas.index("resultado"), columnas.index("prueba"), columnas.index("mensaje")
    fallas = [f for f in filas[1:] if f[i_res] == "FALLA"]
    for f in fallas:
        print(f"FALLA  {f[i_prueba]}  {f[i_msg] or ''}")
    print(filas[0][i_res])
    return 1 if fallas else 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m g1_bd", description="Crea y verifica la base db_udv.")
    p.add_argument("comando", choices=["crear", "verificar"])
    p.add_argument("--host", help="Si no se indica, se usa DATABASE_URL o localhost")
    p.add_argument("--port", type=int, default=3306)
    p.add_argument("--user", default="root")
    p.add_argument("--password", default="")
    a = p.parse_args(argv)
    con = conectar(a.host, a.port, a.user, a.password)
    try:
        return crear(con) if a.comando == "crear" else verificar(con)
    finally:
        con.close()


if __name__ == "__main__":
    sys.exit(main())
