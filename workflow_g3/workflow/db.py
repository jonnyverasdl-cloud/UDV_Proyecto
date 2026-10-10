import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

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


def connect(path: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)


@contextmanager
def transaction(conn: sqlite3.Connection):
    """Transacción atómica. Si ya hay una abierta, participa en ella (anidable)."""
    if conn.in_transaction:
        yield conn
        return
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")
