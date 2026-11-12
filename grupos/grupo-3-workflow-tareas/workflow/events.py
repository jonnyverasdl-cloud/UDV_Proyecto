"""Eventos para el Grupo 6 (notificaciones).

SQLite (tests): el Grupo 3 los deja en la tabla `events`, dentro de la misma transacción
que el cambio de estado.
MySQL (G1): los eventos los crean los triggers de la base (trg_tt_evento, trg_tarea_evento)
en la tabla `evento`, con sus propios nombres y `clave_unica`. Por eso emit() NO hace nada
en MySQL y list_events() lee `evento` devolviendo los mismos campos de siempre.

Tipos en MySQL: assignment.submitted, assignment.returned, assignment.approved,
task.published, task.cancelled, assignment.due_soon, program.authorized.
Tipos en SQLite: assignment.status_changed, task.published, task.cancelled.
"""
import json

from .db import MySQLConn, utcnow


def emit(conn, event_type, task_id, assignment_id=None, payload=None):
    if isinstance(conn, MySQLConn):
        return          # lo hacen los triggers de G1
    conn.execute(
        "INSERT INTO events(event_type, task_id, assignment_id, payload, created_at)"
        " VALUES (?,?,?,?,?)",
        (event_type, task_id, assignment_id, json.dumps(payload or {}), utcnow()),
    )


def list_events(conn, after_id=0, limit=100):
    if isinstance(conn, MySQLConn):
        rows = conn.execute(
            "SELECT id, nombre AS event_type, tarea_id AS task_id,"
            " tarea_destinatario_id AS assignment_id, actor_id, payload,"
            " CAST(creado_en AS CHAR) AS created_at"
            " FROM evento WHERE id > ? ORDER BY id LIMIT ?", (after_id, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM events WHERE id > ? ORDER BY id LIMIT ?", (after_id, limit)
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["payload"] = json.loads(d["payload"]) if d["payload"] else {}
        out.append(d)
    return out