"""Acceso a base de datos: SQLite (tests) y MySQL (sistema real), según DATABASE_URL.

    DATABASE_URL=mysql+pymysql://usuario:clave@localhost:3306/nombre_bd    -> MySQL (G1)
    DATABASE_URL=sqlite:///workflow.db                                     -> SQLite local
    connect(":memory:")  /  connect("ruta.db")                             -> SQLite (tests)

El resto del código usa solo `conn.execute(sql, params)` con placeholders `?`; aquí se
traduce a `%s` para MySQL. Las filas se pueden leer por nombre (row["id"]) o por posición
(row[0]) y convertir con dict(row), igual que sqlite3.Row.

PENDIENTE (depende del esquema final del Grupo 1): los nombres de tablas y columnas que se
usan en tasks.py / transitions.py / events.py siguen siendo los del modelo propio
(tasks, assignments, assignment_transitions, users...). Equivalencias con G1:
    tarea              -> tasks
    tarea_destinatario -> assignments
    tarea_transicion   -> assignment_transitions
El SCHEMA de abajo solo se usa con SQLite (tests); en MySQL las tablas ya existen.
"""
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from urllib.parse import unquote, urlparse

try:                                    # lee el .env si python-dotenv está instalado
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:                     # pragma: no cover
    pass

DEFAULT_URL = "sqlite:///workflow.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id      INTEGER PRIMARY KEY,
    name    TEXT NOT NULL,
    role    TEXT NOT NULL CHECK (role IN ('coordinator','teacher','reviewer','authority','system')),
    campus  TEXT,
    unit    TEXT,
    active  INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS task_types (
    id                INTEGER PRIMARY KEY,
    code              TEXT NOT NULL UNIQUE,
    name              TEXT NOT NULL,
    requires_evidence INTEGER NOT NULL DEFAULT 0,
    evidence_type     TEXT,
    flow              TEXT NOT NULL DEFAULT 'standard' CHECK (flow IN ('standard','short')),
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id             INTEGER PRIMARY KEY,
    type_id        INTEGER NOT NULL REFERENCES task_types(id),
    title          TEXT NOT NULL,
    description    TEXT NOT NULL DEFAULT '',
    priority       TEXT NOT NULL CHECK (priority IN ('low','medium','high')),
    due_date       TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','published','cancelled')),
    created_by     INTEGER NOT NULL REFERENCES users(id),
    responsible_id INTEGER REFERENCES users(id),
    reviewer_id    INTEGER REFERENCES users(id),
    recipient_rule TEXT,
    published_at   TEXT,
    cancelled_at   TEXT,
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assignments (
    id          INTEGER PRIMARY KEY,
    task_id     INTEGER NOT NULL REFERENCES tasks(id),
    assignee_id INTEGER NOT NULL REFERENCES users(id),
    status      TEXT NOT NULL CHECK (status IN
                ('assigned','in_progress','submitted','under_review',
                 'returned','approved','closed','cancelled')),
    priority    TEXT NOT NULL,
    due_date    TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    UNIQUE (task_id, assignee_id)          -- red de seguridad contra duplicados
);
CREATE INDEX IF NOT EXISTS idx_assignments_assignee ON assignments(assignee_id, status);

CREATE TABLE IF NOT EXISTS assignment_transitions (
    id            INTEGER PRIMARY KEY,
    assignment_id INTEGER NOT NULL REFERENCES assignments(id),
    actor_id      INTEGER NOT NULL REFERENCES users(id),
    action        TEXT NOT NULL,
    from_status   TEXT NOT NULL,
    to_status     TEXT NOT NULL,
    comment       TEXT,
    created_at    TEXT NOT NULL
);

-- Historial inmutable: ni se edita ni se borra, ni siquiera al cancelar.
CREATE TRIGGER IF NOT EXISTS transitions_no_update
BEFORE UPDATE ON assignment_transitions
BEGIN SELECT RAISE(ABORT, 'assignment_transitions es append-only'); END;

CREATE TRIGGER IF NOT EXISTS transitions_no_delete
BEFORE DELETE ON assignment_transitions
BEGIN SELECT RAISE(ABORT, 'assignment_transitions es append-only'); END;

-- Bandeja de eventos (outbox) que consumirá el Grupo 6.
CREATE TABLE IF NOT EXISTS events (
    id            INTEGER PRIMARY KEY,
    event_type    TEXT NOT NULL,
    task_id       INTEGER NOT NULL,
    assignment_id INTEGER,
    payload       TEXT NOT NULL,
    created_at    TEXT NOT NULL
);
"""


def utcnow() -> str:
    """Fecha ISO 8601 en UTC."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_URL)


# ------------------------------------------------------------------ MySQL
class Row:
    """Fila de MySQL con la misma interfaz práctica que sqlite3.Row."""

    def __init__(self, columns, values):
        self._columns = list(columns)
        self._values = tuple(values)
        self._index = {c: i for i, c in enumerate(self._columns)}

    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return self._values[key]
        return self._values[self._index[key]]

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)

    def keys(self):
        return list(self._columns)


class _Cursor:
    def __init__(self, cur):
        self._cur = cur
        self._columns = [d[0] for d in (cur.description or [])]

    @property
    def lastrowid(self):
        return self._cur.lastrowid

    @property
    def rowcount(self):
        return self._cur.rowcount

    def fetchone(self):
        values = self._cur.fetchone()
        return None if values is None else Row(self._columns, values)

    def fetchall(self):
        return [Row(self._columns, v) for v in self._cur.fetchall()]

    def __iter__(self):
        return iter(self.fetchall())


class MySQLConn:
    """Envoltorio mínimo sobre una conexión pymysql (autocommit; transacciones explícitas)."""

    def __init__(self, raw):
        self._raw = raw
        self.in_transaction = False

    def execute(self, sql, params=()):
        cur = self._raw.cursor()
        cur.execute(sql.replace("%", "%%").replace("?", "%s"), tuple(params))
        return _Cursor(cur)

    def begin(self):
        self._raw.cursor().execute("START TRANSACTION")
        self.in_transaction = True

    def commit(self):
        self._raw.commit()
        self.in_transaction = False

    def rollback(self):
        self._raw.rollback()
        self.in_transaction = False

    def close(self):
        self._raw.close()


def _connect_mysql(url: str) -> MySQLConn:
    import pymysql                      # import perezoso: solo hace falta con MySQL
    u = urlparse(url)
    raw = pymysql.connect(
        host=u.hostname or "localhost", port=u.port or 3306,
        user=unquote(u.username or ""), password=unquote(u.password or ""),
        database=u.path.lstrip("/"), charset="utf8mb4", autocommit=True)
    return MySQLConn(raw)


# ------------------------------------------------------------------ API pública
def connect(target: str = None):
    """Abre una conexión. `target` puede ser una URL (mysql+pymysql://..., sqlite:///...)
    o una ruta SQLite / ":memory:". Sin argumento usa DATABASE_URL."""
    target = target or get_database_url()
    if target.startswith("mysql"):
        return _connect_mysql(target)
    path = target[len("sqlite:///"):] if target.startswith("sqlite:///") else target
    conn = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn) -> None:
    """Crea las tablas propias. SOLO SQLite (tests); en MySQL las tablas son las de G1."""
    if isinstance(conn, MySQLConn):
        raise RuntimeError("init_db es solo para SQLite: en MySQL las tablas ya las creó G1")
    conn.executescript(SCHEMA)


def set_actor(conn, actor_id) -> None:
    """Deja `@actor_id` en la sesión MySQL para que la auditoría de G1 registre quién
    hizo el cambio. Debe llamarse ya identificado el usuario y ANTES de escribir, en la
    misma conexión. En SQLite (tests) no hace nada."""
    if isinstance(conn, MySQLConn):
        conn.execute("SET @actor_id = ?", (int(actor_id),))


def _begin(conn):
    if isinstance(conn, MySQLConn):
        conn.begin()
    else:
        conn.execute("BEGIN IMMEDIATE")


def _end(conn, ok: bool):
    if isinstance(conn, MySQLConn):
        conn.commit() if ok else conn.rollback()
    else:
        conn.execute("COMMIT" if ok else "ROLLBACK")


@contextmanager
def transaction(conn):
    """Transacción atómica. Si ya hay una abierta, participa en ella (anidable)."""
    if conn.in_transaction:
        yield conn
        return
    _begin(conn)
    try:
        yield conn
    except BaseException:
        _end(conn, False)
        raise
    else:
        _end(conn, True)
