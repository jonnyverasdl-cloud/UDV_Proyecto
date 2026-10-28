"""Genera diccionario_db_udv.html leyendo la estructura de la base db_udv.

Lee tablas, vistas, columnas, llaves, restricciones, índices y triggers de
information_schema, les agrega las descripciones de descripciones.py y
escribe el HTML con plantilla.html.

Uso (desde esta carpeta, con la base ya montada):

    pip install -r ../../requirements.txt
    python generar_diccionario.py
    python generar_diccionario.py --host localhost --port 3307 --user root --password xxx

Si existe la variable DATABASE_URL (mysql+pymysql://usuario:clave@host:puerto/db_udv)
se usa esa conexión. Funciona con MySQL 8 y con MariaDB.
"""
import argparse
import json
import os
import sys
from urllib.parse import unquote, urlparse

import pymysql

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from descripciones import COLUMNAS, COMUNES, TABLAS, VISTAS_COL  # noqa: E402

BASE = "db_udv"

DESC_TRIGGERS = {
    "trg_tt_valida": "Valida cada transición: parte del estado actual, existe en el workflow, la inicial no se repite y la devolución exige comentario.",
    "trg_tt_evento": "Crea el evento de entrega, devolución o aprobación.",
    "trg_pv_inmutable": "Una versión autorizada no se modifica; cambios de estado según flujo_programa; evaluaciones al 100 % para enviar; autorizar exige quién y cuándo.",
    "trg_pv_evento": "Crea el evento program.authorized al autorizar.",
    "trg_tarea_evento": "Crea los eventos task.published y task.cancelled.",
    "trg_aprobacion_valida": "Una devolución del programa exige comentario.",
    "trg_archivo_eliminacion_audit": "Al eliminar lógicamente un archivo guarda su metadato en auditoría.",
    "trg_evaluacion_bi": "Bloqueo de versión autorizada y el total no pasa de 100.",
    "trg_evaluacion_bu": "Bloqueo de versión autorizada y el total no pasa de 100.",
    "trg_unidad_item_bi": "Bloqueo de versión autorizada; la competencia debe ser de la misma versión.",
    "trg_unidad_item_bu": "Bloqueo de versión autorizada; la competencia debe ser de la misma versión.",
    "trg_programa_pdf_bi": "Solo se registra PDF de una versión autorizada.",
    "trg_entrega_borrador_bi": "Solo se guarda borrador si la asignación está pendiente.",
    "trg_entrega_borrador_bu": "Solo se guarda borrador si la asignación está pendiente.",
    "trg_evento_bu": "Solo se permite marcar procesado_en una vez.",
}


def desc_trigger(nombre):
    if nombre in DESC_TRIGGERS:
        return DESC_TRIGGERS[nombre]
    if nombre.endswith("_no_update"):
        return "No se permite modificar registros (historial inmutable)."
    if nombre.endswith("_no_delete"):
        return "No se permite DELETE físico (eliminación lógica o historial)."
    if "_audit_" in nombre:
        return "Registra altas y cambios en auditoría con @actor_id."
    if nombre.endswith(("_bi", "_bu", "_bd")):
        return "Bloquea cambios si la versión del programa está autorizada."
    return ""


def conectar(args):
    url = os.environ.get("DATABASE_URL")
    if url and not args.host:
        u = urlparse(url)
        return pymysql.connect(host=u.hostname, port=u.port or 3306, user=unquote(u.username or ""),
                               password=unquote(u.password or ""), database=BASE, charset="utf8mb4")
    return pymysql.connect(host=args.host or "localhost", port=args.port, user=args.user,
                           password=args.password, database=BASE, charset="utf8mb4")


def consultar(cur, sql):
    cur.execute(sql, {"base": BASE})
    return cur.fetchall()


def leer_estructura(cur):
    tipos = dict(consultar(cur, """
        SELECT table_name, table_type FROM information_schema.tables
        WHERE table_schema = %(base)s AND table_name NOT LIKE 'tmp\\_%%'"""))
    columnas = {}
    for t, c, ty, nul, de, key, ex, gen, pos in consultar(cur, """
        SELECT table_name, column_name, column_type, is_nullable, column_default,
               column_key, extra, IFNULL(generation_expression, ''), ordinal_position
        FROM information_schema.columns WHERE table_schema = %(base)s"""):
        if de is not None:
            de = str(de)
            if de.upper() == "NULL":
                de = None
            else:
                de = de.strip("'")
        columnas.setdefault(t, []).append(dict(n=c, t=ty, nul=nul == "YES", d=de, k=key, x=ex or "", g=gen, p=int(pos)))
    fks = {(t, c): f"{rt}.{rc}" for t, c, rt, rc in consultar(cur, """
        SELECT table_name, column_name, referenced_table_name, referenced_column_name
        FROM information_schema.key_column_usage
        WHERE table_schema = %(base)s AND referenced_table_name IS NOT NULL""")}
    unicos = {}
    for t, cn, cl in consultar(cur, """
        SELECT tc.table_name, tc.constraint_name,
               GROUP_CONCAT(k.column_name ORDER BY k.ordinal_position SEPARATOR ', ')
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage k
          ON k.constraint_schema = tc.constraint_schema AND k.table_name = tc.table_name
         AND k.constraint_name = tc.constraint_name
        WHERE tc.table_schema = %(base)s AND tc.constraint_type = 'UNIQUE'
        GROUP BY tc.table_name, tc.constraint_name"""):
        unicos.setdefault(t, []).append((cn, cl))
    # MySQL 8 no tiene table_name en check_constraints: se toma de table_constraints.
    checks = {}
    for t, cn, cl in consultar(cur, """
        SELECT tc.table_name, cc.constraint_name, cc.check_clause
        FROM information_schema.check_constraints cc
        JOIN information_schema.table_constraints tc
          ON tc.constraint_schema = cc.constraint_schema AND tc.constraint_name = cc.constraint_name
         AND tc.constraint_type = 'CHECK'
        WHERE cc.constraint_schema = %(base)s"""):
        checks.setdefault(t, []).append((cn, " ".join(str(cl).split()).replace("`", "")))
    indices = {}
    for t, cn, cl in consultar(cur, """
        SELECT table_name, index_name, GROUP_CONCAT(column_name ORDER BY seq_in_index SEPARATOR ', ')
        FROM information_schema.statistics
        WHERE table_schema = %(base)s AND index_name LIKE 'ix\\_%%'
        GROUP BY table_name, index_name"""):
        indices.setdefault(t, []).append((cn, cl))
    triggers = {}
    for t, cn in consultar(cur, """
        SELECT event_object_table, trigger_name FROM information_schema.triggers
        WHERE trigger_schema = %(base)s ORDER BY trigger_name"""):
        triggers.setdefault(t, []).append(cn)
    return tipos, columnas, fks, unicos, checks, indices, triggers


def describir_columna(tabla, col, es_vista, fks):
    desc = (COLUMNAS.get(tabla, {}).get(col)
            or (VISTAS_COL.get(col) if es_vista else None)
            or COMUNES.get(col) or VISTAS_COL.get(col))
    if not desc and es_vista:
        for origen in ("tarea_destinatario", "tarea", "programa_version", "evento", "programa_curso"):
            if col in COLUMNAS.get(origen, {}):
                return COLUMNAS[origen][col]
    if not desc and col.endswith("_id") and (tabla, col) in fks:
        desc = "Referencia a " + fks[(tabla, col)].split(".")[0] + "."
    return desc


def armar_datos(estructura):
    tipos, columnas, fks, unicos, checks, indices, triggers = estructura
    datos, sin_descripcion = [], []
    for t, (bloque, api, d) in TABLAS.items():
        if t not in tipos:
            print(f"Aviso: {t} está en descripciones.py pero no existe en la base")
            continue
        es_vista = tipos[t] == "VIEW"
        cols = []
        for c in sorted(columnas.get(t, []), key=lambda c: c["p"]):
            desc = describir_columna(t, c["n"], es_vista, fks)
            if not desc:
                sin_descripcion.append(f"{t}.{c['n']}")
            cols.append(dict(n=c["n"], t=c["t"], nul=c["nul"], d=c["d"], pk=c["k"] == "PRI",
                             fk=fks.get((t, c["n"])), gen=bool(c["g"]),
                             ai="auto_increment" in c["x"], desc=desc or ""))
        reglas = [dict(k="Único", n=cn, v=cl) for cn, cl in unicos.get(t, [])]
        reglas += [dict(k="Check", n=cn, v=cl) for cn, cl in checks.get(t, [])]
        reglas += [dict(k="Índice", n=cn, v=cl) for cn, cl in indices.get(t, [])]
        reglas += [dict(k="Trigger", n=n, v=desc_trigger(n)) for n in triggers.get(t, [])]
        datos.append(dict(t=t, b=bloque, api=api, d=d, v=es_vista, c=cols, r=reglas))
    nuevas = sorted(set(tipos) - set(TABLAS))
    if nuevas:
        print("Aviso: estas tablas o vistas no tienen descripción en descripciones.py:", ", ".join(nuevas))
    if sin_descripcion:
        print("Aviso: columnas sin descripción:", ", ".join(sin_descripcion))
    return datos


def main():
    p = argparse.ArgumentParser(description="Genera el diccionario de datos de db_udv en HTML.")
    p.add_argument("--host")
    p.add_argument("--port", type=int, default=3306)
    p.add_argument("--user", default="root")
    p.add_argument("--password", default="")
    p.add_argument("--salida", default=os.path.join(AQUI, "diccionario_db_udv.html"))
    args = p.parse_args()

    con = conectar(args)
    try:
        with con.cursor() as cur:
            datos = armar_datos(leer_estructura(cur))
    finally:
        con.close()

    plantilla = open(os.path.join(AQUI, "plantilla.html"), encoding="utf-8").read()
    html = plantilla.replace("__DATA__", json.dumps(datos, ensure_ascii=False))
    with open(args.salida, "w", encoding="utf-8") as f:
        f.write(html)
    n_tablas = sum(1 for t in datos if not t["v"])
    print(f"Listo: {args.salida} ({n_tablas} tablas, {len(datos) - n_tablas} vistas)")


if __name__ == "__main__":
    main()
