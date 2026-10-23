"""Eventos para el Grupo 6 (notificaciones).

El Grupo 3 solo los deja disponibles en la tabla `events`, dentro de la misma
transacción que el cambio de estado. El Grupo 6 los lee con list_events()
o con GET /api/v1/events?after_id=N.

Tipos emitidos:
    assignment.status_changed  cada transición (incluye la creación al publicar)
    task.published             al publicar una tarea
    task.cancelled             al cancelar una tarea
"""
import json

from .db import utcnow


def emit(conn, event_type, task_id, assignment_id=None, payload=None):
    conn.execute(
        "INSERT INTO events(event_type, task_id, assignment_id, payload, created_at)"
        " VALUES (?,?,?,?,?)",
        (event_type, task_id, assignment_id, json.dumps(payload or {}), utcnow()),
    )


def list_events(conn, after_id=0, limit=100):
    rows = conn.execute(
        "SELECT * FROM events WHERE id > ? ORDER BY id LIMIT ?", (after_id, limit)
    ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["payload"] = json.loads(d["payload"])
        out.append(d)
    return out
