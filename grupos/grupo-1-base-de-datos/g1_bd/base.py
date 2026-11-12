"""Conexión y ejecución de los scripts SQL del Grupo 1."""
import os
from urllib.parse import unquote, urlparse

import pymysql

CARPETA_SQL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Docs", "sql")


def conectar(host=None, port=3306, user="root", password="", database=None):
    """Abre la conexión. Si no se pasa host, usa DATABASE_URL."""
    url = os.environ.get("DATABASE_URL")
    if url and not host:
        u = urlparse(url)
        host, port = u.hostname, u.port or 3306
        user, password = unquote(u.username or ""), unquote(u.password or "")
    return pymysql.connect(host=host or "localhost", port=port, user=user, password=password,
                           database=database, charset="utf8mb4", autocommit=True)


def separar_sentencias(texto):
    """Divide un script en sentencias, respetando DELIMITER, comentarios y textos entre comillas.

    El cliente mysql entiende DELIMITER pero el driver no, así que se resuelve aquí.
    """
    sentencias, actual = [], []
    delimitador = ";"
    i, n = 0, len(texto)
    inicio_linea = True
    while i < n:
        if inicio_linea and not "".join(actual).strip():
            fin = texto.find("\n", i)
            fin = n if fin == -1 else fin
            linea = texto[i:fin].strip()
            if linea.upper().startswith("DELIMITER "):
                delimitador = linea.split(None, 1)[1].strip()
                actual = []
                i = fin + 1
                continue
        c = texto[i]
        inicio_linea = c == "\n"
        if c in "'\"`":
            j = i + 1
            while j < n:
                if texto[j] == "\\" and c != "`":
                    j += 2
                    continue
                if texto[j] == c:
                    if j + 1 < n and texto[j + 1] == c:
                        j += 2
                        continue
                    break
                j += 1
            actual.append(texto[i:j + 1])
            i = j + 1
            continue
        if texto.startswith("--", i) and (i + 2 >= n or texto[i + 2] in " \t\r\n") or c == "#":
            fin = texto.find("\n", i)
            i = n if fin == -1 else fin
            continue
        if texto.startswith("/*", i):
            fin = texto.find("*/", i + 2)
            i = n if fin == -1 else fin + 2
            continue
        if texto.startswith(delimitador, i):
            sentencia = "".join(actual).strip()
            if sentencia:
                sentencias.append(sentencia)
            actual = []
            i += len(delimitador)
            continue
        actual.append(c)
        i += 1
    resto = "".join(actual).strip()
    if resto:
        sentencias.append(resto)
    return sentencias


def ejecutar_script(conexion, nombre):
    """Ejecuta un archivo de Docs/sql. Devuelve las filas del último SELECT que devolvió datos."""
    ruta = nombre if os.path.isabs(nombre) else os.path.join(CARPETA_SQL, nombre)
    with open(ruta, encoding="utf-8") as f:
        sentencias = separar_sentencias(f.read())
    ultimo = None
    with conexion.cursor() as cur:
        for sentencia in sentencias:
            cur.execute(sentencia)
            if cur.description:
                filas = cur.fetchall()
                if filas:
                    ultimo = ([d[0] for d in cur.description], filas)
            while cur.nextset():
                pass
    return len(sentencias), ultimo
