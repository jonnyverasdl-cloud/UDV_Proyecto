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
