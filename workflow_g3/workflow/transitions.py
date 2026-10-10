from . import events
from .db import transaction, utcnow
from .errors import Conflict, Forbidden, NotFound, ValidationFailed
from .matrix import ACTIONS, FLOWS


def get_actor(conn, actor_id):
    row = conn.execute("SELECT * FROM users WHERE id = ?", (actor_id,)).fetchone()
    if row is None or not row["active"]:
        raise Forbidden("Usuario inexistente o inactivo")
    return dict(row)


def get_rule(flow, state, action):
    rule = FLOWS[flow].get((state, action))
    if rule is None:
        raise Conflict(
            f"La acción '{action}' no es válida desde el estado '{state}'",
            details={"state": state, "action": action}, code="invalid_transition")
    return rule


def authorize(rule, actor, task, assignee_id=None):
    """Verifica rol y alcance. `task` es un dict/Row con created_by, responsible_id, reviewer_id."""
    if actor["role"] not in rule.roles:
        raise Forbidden(f"El rol '{actor['role']}' no puede ejecutar '{rule.action}'")
    if rule.scope is None or actor["role"] in rule.unscoped_roles:
        return
    if rule.scope == "assignee":
        if actor["id"] != assignee_id:
            raise Forbidden("Solo el docente destinatario puede ejecutar esta acción")
    elif rule.scope == "task_reviewer":
        if task["reviewer_id"] is not None and task["reviewer_id"] != actor["id"]:
            raise Forbidden("No eres el revisor designado de esta tarea")
    elif rule.scope == "task_coordinator":
        if actor["id"] not in (task["created_by"], task["responsible_id"]):
            raise Forbidden("No eres el coordinador autorizado de esta tarea")


def record_transition(conn, assignment_id, actor_id, action, from_state, to_state,
                      comment, now=None):
    conn.execute(
        "INSERT INTO assignment_transitions"
        "(assignment_id, actor_id, action, from_status, to_status, comment, created_at)"
        " VALUES (?,?,?,?,?,?,?)",
        (assignment_id, actor_id, action, from_state, to_state, comment, now or utcnow()))


def emit_status_changed(conn, task, assignment_id, assignee_id, actor_id, action,
                        from_state, to_state, comment):
    events.emit(conn, "assignment.status_changed", task["id"], assignment_id, {
        "assignment_id": assignment_id, "task_id": task["id"], "task_title": task["title"],
        "recipient_id": assignee_id, "actor_id": actor_id, "action": action,
        "from_status": from_state, "to_status": to_state, "comment": comment,
        "due_date": task["due_date"], "reviewer_id": task["reviewer_id"],
    })


def perform(conn, assignment_id, action, actor, comment=None):
    """Ejecuta una acción sobre una asignación. Devuelve la asignación actualizada."""
    if action not in ACTIONS:
        raise ValidationFailed(f"Acción desconocida: '{action}'", details={"valid": list(ACTIONS)})
    comment = (comment or "").strip() or None

    with transaction(conn):
        row = conn.execute(
            "SELECT a.*, t.title, t.created_by, t.responsible_id, t.reviewer_id, ty.flow,"
            "       t.id AS tid"
            " FROM assignments a JOIN tasks t ON t.id = a.task_id"
            " JOIN task_types ty ON ty.id = t.type_id WHERE a.id = ?", (assignment_id,)
        ).fetchone()
        if row is None:
            raise NotFound(f"Asignación {assignment_id} no existe")

        rule = get_rule(row["flow"], row["status"], action)           # 409
        authorize(rule, actor, row, row["assignee_id"])                # 403
        if rule.comment_required and not comment:                      # 422
            raise ValidationFailed(f"La acción '{action}' requiere un comentario",
                                   details={"field": "comment"})

        now = utcnow()
        cur = conn.execute(
            "UPDATE assignments SET status = ?, updated_at = ? WHERE id = ? AND status = ?",
            (rule.to_state, now, assignment_id, row["status"]))
        if cur.rowcount != 1:                                          # carrera concurrente
            raise Conflict("La asignación cambió de estado mientras se procesaba",
                           code="concurrent_update")

        record_transition(conn, assignment_id, actor["id"], action, row["status"],
                          rule.to_state, comment, now)
        task = {"id": row["tid"], "title": row["title"], "due_date": row["due_date"],
                "reviewer_id": row["reviewer_id"]}
        emit_status_changed(conn, task, assignment_id, row["assignee_id"], actor["id"],
                            action, row["status"], rule.to_state, comment)

        return dict(conn.execute("SELECT * FROM assignments WHERE id = ?",
                                 (assignment_id,)).fetchone())
