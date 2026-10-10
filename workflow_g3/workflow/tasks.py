import json
from datetime import date

from . import events, transitions
from .db import transaction, utcnow
from .errors import Conflict, Forbidden, NotFound, ValidationFailed
from .matrix import AUTHORITY, COORDINATOR, FLOWS, REVIEWER, STATES, TEACHER

PRIORITIES = ("low", "medium", "high")
EDITABLE_FIELDS = ("type_id", "title", "description", "priority", "due_date",
                   "responsible_id", "reviewer_id")


# ----------------------------------------------------------------- utilidades
def paginate(page, page_size):
    if not isinstance(page, int) or page < 1:
        raise ValidationFailed("page debe ser un entero >= 1")
    if not isinstance(page_size, int) or not 1 <= page_size <= 100:
        raise ValidationFailed("page_size debe estar entre 1 y 100")
    return page_size, (page - 1) * page_size


def _paged(conn, select, frm, params, order, page, page_size):
    limit, offset = paginate(page, page_size)
    total = conn.execute(f"SELECT COUNT(*) {frm}", params).fetchone()[0]
    rows = conn.execute(f"{select} {frm} ORDER BY {order} LIMIT ? OFFSET ?",
                        [*params, limit, offset]).fetchall()
    return {"items": [dict(r) for r in rows], "page": page,
            "page_size": page_size, "total": total}


def _task_out(row):
    d = dict(row)
    d["recipient_rule"] = json.loads(d["recipient_rule"]) if d.get("recipient_rule") else None
    return d


def _load_task(conn, task_id):
    row = conn.execute(
        "SELECT t.*, ty.flow AS flow FROM tasks t JOIN task_types ty ON ty.id = t.type_id"
        " WHERE t.id = ?", (task_id,)).fetchone()
    if row is None:
        raise NotFound(f"Tarea {task_id} no existe")
    return row


def _can_manage(actor, task):
    return actor["role"] == COORDINATOR and actor["id"] in (task["created_by"],
                                                            task["responsible_id"])


def _can_view(actor, task):
    if actor["role"] == AUTHORITY:
        return True
    if actor["role"] == COORDINATOR:
        return _can_manage(actor, task)
    if actor["role"] == REVIEWER:
        return task["status"] != "draft" and task["reviewer_id"] == actor["id"]
    return False


def _parse_due_date(value):
    try:
        return date.fromisoformat(str(value)).isoformat()
    except ValueError:
        raise ValidationFailed("due_date debe ser una fecha ISO 8601 (YYYY-MM-DD)",
                               details={"field": "due_date"})


def _require_user(conn, user_id, field, role=None):
    row = conn.execute("SELECT * FROM users WHERE id = ? AND active = 1", (user_id,)).fetchone()
    if row is None or (role and row["role"] != role):
        raise ValidationFailed(f"{field} no corresponde a un usuario válido",
                               details={"field": field})


# ---------------------------------------------------------------- task types
def create_task_type(conn, actor, data):
    if actor["role"] not in (COORDINATOR, AUTHORITY):
        raise Forbidden("Solo coordinación o autoridad pueden crear tipos de tarea")
    code = (data.get("code") or "").strip()
    name = (data.get("name") or "").strip()
    flow = data.get("flow", "standard")
    if not code or not name:
        raise ValidationFailed("code y name son obligatorios")
    if flow not in FLOWS:
        raise ValidationFailed("flow inválido", details={"valid": list(FLOWS)})
    with transaction(conn):
        if conn.execute("SELECT 1 FROM task_types WHERE code = ?", (code,)).fetchone():
            raise Conflict(f"Ya existe un tipo con code '{code}'")
        cur = conn.execute(
            "INSERT INTO task_types(code, name, requires_evidence, evidence_type, flow, created_at)"
            " VALUES (?,?,?,?,?,?)",
            (code, name, int(bool(data.get("requires_evidence"))),
             data.get("evidence_type"), flow, utcnow()))
        return dict(conn.execute("SELECT * FROM task_types WHERE id = ?",
                                 (cur.lastrowid,)).fetchone())


def list_task_types(conn, page=1, page_size=20):
    return _paged(conn, "SELECT *", "FROM task_types", [], "id", page, page_size)


# --------------------------------------------------------------------- tasks
def _validate_fields(conn, data):
    if "title" in data and not (data["title"] or "").strip():
        raise ValidationFailed("title no puede estar vacío", details={"field": "title"})
    if "priority" in data and data["priority"] not in PRIORITIES:
        raise ValidationFailed("priority inválida", details={"valid": list(PRIORITIES)})
    if "due_date" in data:
        data["due_date"] = _parse_due_date(data["due_date"])
    if "type_id" in data and conn.execute(
            "SELECT 1 FROM task_types WHERE id = ?", (data["type_id"],)).fetchone() is None:
        raise ValidationFailed("type_id no existe", details={"field": "type_id"})
    if data.get("responsible_id") is not None:
        _require_user(conn, data["responsible_id"], "responsible_id", COORDINATOR)
    if data.get("reviewer_id") is not None:
        _require_user(conn, data["reviewer_id"], "reviewer_id", REVIEWER)


def create_task(conn, actor, data):
    if actor["role"] != COORDINATOR:
        raise Forbidden("Solo un coordinador puede crear tareas")
    data = dict(data)
    unknown = set(data) - set(EDITABLE_FIELDS)
    if unknown:
        raise ValidationFailed("Campos desconocidos", details={"fields": sorted(unknown)})
    for required in ("type_id", "title", "due_date"):
        if data.get(required) in (None, ""):
            raise ValidationFailed(f"{required} es obligatorio", details={"field": required})
    data.setdefault("priority", "medium")
    data.setdefault("description", "")
    with transaction(conn):
        _validate_fields(conn, data)
        now = utcnow()
        cur = conn.execute(
            "INSERT INTO tasks(type_id, title, description, priority, due_date, status,"
            " created_by, responsible_id, reviewer_id, created_at, updated_at)"
            " VALUES (?,?,?,?,?, 'draft', ?,?,?,?,?)",
            (data["type_id"], data["title"].strip(), data["description"], data["priority"],
             data["due_date"], actor["id"], data.get("responsible_id"),
             data.get("reviewer_id"), now, now))
        return _task_out(_load_task(conn, cur.lastrowid))


def get_task(conn, actor, task_id):
    task = _load_task(conn, task_id)
    if not _can_view(actor, task):
        raise Forbidden("No tienes acceso a esta tarea")
    return _task_out(task)


def list_tasks(conn, actor, status=None, page=1, page_size=20):
    where, params = [], []
    if actor["role"] == COORDINATOR:
        where.append("(t.created_by = ? OR t.responsible_id = ?)")
        params += [actor["id"], actor["id"]]
    elif actor["role"] == REVIEWER:
        where.append("t.status != 'draft' AND t.reviewer_id = ?")
        params.append(actor["id"])
    elif actor["role"] != AUTHORITY:
        raise Forbidden("Tu rol no puede listar tareas")
    if status:
        if status not in ("draft", "published", "cancelled"):
            raise ValidationFailed("status inválido")
        where.append("t.status = ?")
        params.append(status)
    clause = ("WHERE " + " AND ".join(where)) if where else ""
    res = _paged(conn, "SELECT t.*", f"FROM tasks t {clause}", params, "t.id DESC",
                 page, page_size)
    for item in res["items"]:
        item["recipient_rule"] = (json.loads(item["recipient_rule"])
                                  if item["recipient_rule"] else None)
    return res


def update_task(conn, actor, task_id, changes):
    unknown = set(changes) - set(EDITABLE_FIELDS)
    if unknown:
        raise ValidationFailed("Campos no editables", details={"fields": sorted(unknown)})
    with transaction(conn):
        task = _load_task(conn, task_id)
        if not _can_manage(actor, task):
            raise Forbidden("No eres el coordinador autorizado de esta tarea")
        if task["status"] != "draft":
            raise Conflict("Solo se puede editar una tarea en borrador", code="not_draft")
        changes = dict(changes)
        _validate_fields(conn, changes)
        if changes:
            sets = ", ".join(f"{k} = ?" for k in changes)
            conn.execute(f"UPDATE tasks SET {sets}, updated_at = ? WHERE id = ?",
                         [*changes.values(), utcnow(), task_id])
        return _task_out(_load_task(conn, task_id))


# ---------------------------------------------------------------- recipients
def _normalize_rule(conn, rule):
    mode = (rule or {}).get("mode")
    if mode == "all":
        return {"mode": "all"}
    if mode == "users":           # un docente o una lista de docentes
        ids = rule.get("user_ids")
        if not isinstance(ids, list) or not ids or not all(isinstance(i, int) for i in ids):
            raise ValidationFailed("user_ids debe ser una lista no vacía de enteros")
        ids = sorted(set(ids))
        valid = {r["id"] for r in conn.execute(
            f"SELECT id FROM users WHERE role = 'teacher' AND active = 1 "
            f"AND id IN ({','.join('?' * len(ids))})", ids)}
        invalid = [i for i in ids if i not in valid]
        if invalid:
            raise ValidationFailed("Hay usuarios que no son docentes activos",
                                   details={"invalid_user_ids": invalid})
        return {"mode": "users", "user_ids": ids}
    if mode == "filter":          # filtro institucional
        campus, unit = rule.get("campus"), rule.get("unit")
        if not campus and not unit:
            raise ValidationFailed("El filtro requiere campus (sede) y/o unit (unidad)")
        out = {"mode": "filter"}
        if campus:
            out["campus"] = campus
        if unit:
            out["unit"] = unit
        return out
    raise ValidationFailed("mode inválido", details={"valid": ["users", "all", "filter"]})


def resolve_recipients(conn, rule):
    """Docentes elegibles HOY para la regla guardada (activos, rol docente, sin duplicados)."""
    sql, params = "SELECT id FROM users WHERE role = 'teacher' AND active = 1", []
    if rule["mode"] == "users":
        sql += f" AND id IN ({','.join('?' * len(rule['user_ids']))})"
        params += rule["user_ids"]
    elif rule["mode"] == "filter":
        for col in ("campus", "unit"):
            if rule.get(col):
                sql += f" AND {col} = ?"
                params.append(rule[col])
    return [r["id"] for r in conn.execute(sql + " ORDER BY id", params)]


def set_recipients(conn, actor, task_id, rule):
    with transaction(conn):
        task = _load_task(conn, task_id)
        if not _can_manage(actor, task):
            raise Forbidden("No eres el coordinador autorizado de esta tarea")
        if task["status"] != "draft":
            raise Conflict("Los destinatarios solo se editan en borrador", code="not_draft")
        norm = _normalize_rule(conn, rule)
        eligible = resolve_recipients(conn, norm)
        if not eligible:
            raise ValidationFailed("La regla no alcanza a ningún docente elegible")
        conn.execute("UPDATE tasks SET recipient_rule = ?, updated_at = ? WHERE id = ?",
                     (json.dumps(norm), utcnow(), task_id))
        return {"task": _task_out(_load_task(conn, task_id)), "eligible_count": len(eligible)}


# ------------------------------------------------------------------- publish
def publish_task(conn, actor, task_id):
    """Crea una asignación por destinatario. Todo o nada, e idempotente (2.ª vez -> 409)."""
    with transaction(conn):
        task = _load_task(conn, task_id)
        rule = transitions.get_rule(task["flow"], "draft", "publish")
        transitions.authorize(rule, actor, task)
        if task["status"] != "draft":
            raise Conflict("La tarea ya fue publicada o cancelada", code="already_published")
        if not task["recipient_rule"]:
            raise ValidationFailed("Configura los destinatarios antes de publicar")
        ids = resolve_recipients(conn, json.loads(task["recipient_rule"]))
        if not ids:
            raise ValidationFailed("No hay docentes elegibles para publicar")

        now = utcnow()
        cur = conn.execute(
            "UPDATE tasks SET status = 'published', published_at = ?, updated_at = ?"
            " WHERE id = ? AND status = 'draft'", (now, now, task_id))
        if cur.rowcount != 1:
            raise Conflict("La tarea ya fue publicada", code="already_published")

        created = []
        for user_id in ids:
            aid = conn.execute(
                "INSERT INTO assignments(task_id, assignee_id, status, priority, due_date,"
                " created_at, updated_at) VALUES (?,?, 'assigned', ?,?,?,?)",
                (task_id, user_id, task["priority"], task["due_date"], now, now)).lastrowid
            transitions.record_transition(conn, aid, actor["id"], "publish",
                                          "draft", "assigned", None, now)
            transitions.emit_status_changed(conn, task, aid, user_id, actor["id"],
                                            "publish", "draft", "assigned", None)
            created.append(aid)
        events.emit(conn, "task.published", task_id, None, {
            "task_id": task_id, "task_title": task["title"], "actor_id": actor["id"],
            "assignments_created": len(created), "due_date": task["due_date"]})
        return {"task": _task_out(_load_task(conn, task_id)),
                "assignments_created": len(created), "assignment_ids": created}


# -------------------------------------------------------------------- cancel
def cancel_task(conn, actor, task_id, reason=None):
    """Cancela un borrador o las asignaciones aún en 'assigned'. Nunca borra historia.

    SUPUESTO: las asignaciones que ya avanzaron (in_progress en adelante) NO se cancelan
    (la matriz solo permite cancelar desde draft/assigned) y se reportan en `skipped`.
    La tarea pasa a 'cancelled' solo si no queda ninguna asignación viva.
    """
    with transaction(conn):
        task = _load_task(conn, task_id)
        transitions.authorize(transitions.get_rule(task["flow"], "draft", "cancel"), actor, task)
        if task["status"] == "cancelled":
            raise Conflict("La tarea ya está cancelada", code="already_cancelled")

        cancelled, skipped = [], []
        if task["status"] == "published":
            rows = conn.execute("SELECT id, status FROM assignments WHERE task_id = ? ORDER BY id",
                                (task_id,)).fetchall()
            cancellable = [r["id"] for r in rows if r["status"] == "assigned"]
            skipped = [{"assignment_id": r["id"], "status": r["status"]}
                       for r in rows if r["status"] not in ("assigned", "cancelled")]
            if not cancellable and skipped:
                raise Conflict("Ninguna asignación puede cancelarse en su estado actual",
                               details={"skipped": skipped}, code="nothing_to_cancel")
            for aid in cancellable:
                transitions.perform(conn, aid, "cancel", actor, reason)
                cancelled.append(aid)

        if not skipped:
            now = utcnow()
            conn.execute("UPDATE tasks SET status = 'cancelled', cancelled_at = ?, updated_at = ?"
                         " WHERE id = ?", (now, now, task_id))
            events.emit(conn, "task.cancelled", task_id, None, {
                "task_id": task_id, "task_title": task["title"], "actor_id": actor["id"],
                "reason": reason, "assignments_cancelled": len(cancelled)})
        return {"task": _task_out(_load_task(conn, task_id)),
                "cancelled_assignments": cancelled, "skipped": skipped}


# ------------------------------------------------------- seguimiento / historial
def list_task_assignments(conn, actor, task_id, status=None, page=1, page_size=20):
    task = _load_task(conn, task_id)
    if not _can_view(actor, task):
        raise Forbidden("No tienes acceso a esta tarea")
    counts = {s: 0 for s in STATES if s != "draft"}
    for r in conn.execute("SELECT status, COUNT(*) n FROM assignments WHERE task_id = ?"
                          " GROUP BY status", (task_id,)):
        counts[r["status"]] = r["n"]
    where, params = "WHERE a.task_id = ?", [task_id]
    if status:
        if status not in counts:
            raise ValidationFailed("status inválido", details={"valid": list(counts)})
        where += " AND a.status = ?"
        params.append(status)
    res = _paged(
        conn, "SELECT a.*, u.name AS assignee_name, u.campus, u.unit,"
              " (SELECT MAX(created_at) FROM assignment_transitions x"
              "  WHERE x.assignment_id = a.id) AS last_change_at",
        f"FROM assignments a JOIN users u ON u.id = a.assignee_id {where}",
        params, "a.id", page, page_size)
    res["summary"] = {"total": sum(counts.values()), "by_status": counts}
    return res


def get_history(conn, actor, assignment_id):
    row = conn.execute(
        "SELECT a.assignee_id, t.* FROM assignments a JOIN tasks t ON t.id = a.task_id"
        " WHERE a.id = ?", (assignment_id,)).fetchone()
    if row is None:
        raise NotFound(f"Asignación {assignment_id} no existe")
    if actor["id"] != row["assignee_id"] and not _can_view(actor, row):
        raise Forbidden("No tienes acceso al historial de esta asignación")
    rows = conn.execute(
        "SELECT h.*, u.name AS actor_name FROM assignment_transitions h"
        " JOIN users u ON u.id = h.actor_id WHERE h.assignment_id = ? ORDER BY h.id",
        (assignment_id,)).fetchall()
    return [dict(r) for r in rows]


def inbox(conn, actor, status=None, page=1, page_size=20):
    """Asignaciones del docente. Un borrador nunca aparece (no tiene asignaciones)."""
    if actor["role"] != TEACHER:
        raise Forbidden("Solo los docentes tienen inbox")
    where, params = "WHERE a.assignee_id = ? AND t.status != 'draft'", [actor["id"]]
    if status:
        where += " AND a.status = ?"
        params.append(status)
    return _paged(
        conn, "SELECT a.*, t.title, t.description, ty.name AS type_name,"
              " ty.requires_evidence, ty.evidence_type",
        f"FROM assignments a JOIN tasks t ON t.id = a.task_id"
        f" JOIN task_types ty ON ty.id = t.type_id {where}",
        params, "a.due_date, a.id", page, page_size)
