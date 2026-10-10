import sys

from . import tasks, transitions
from .db import connect, init_db, utcnow

TASK_TYPES = [
    ("update_program",   "Actualizar programa de curso", 1, "documento", "standard"),
    ("upload_cv",        "Subir CV",                     1, "documento", "standard"),
    ("deliver_invoice",  "Entregar factura",             1, "documento", "standard"),
    ("confirm_activity", "Confirmar actividad",          0, None,        "short"),
    ("upload_evidence",  "Cargar evidencia",             1, "archivo",   "standard"),
]


def _user(conn, name, role, campus=None, unit=None, active=1):
    return conn.execute("INSERT INTO users(name, role, campus, unit, active) VALUES (?,?,?,?,?)",
                        (name, role, campus, unit, active)).lastrowid


def seed_base(conn):
    """Usuarios y catálogo de tipos. Devuelve un dict con los ids."""
    ids = {
        "coord": _user(conn, "Ana Coordinadora", "coordinator", "Central", "Ingeniería"),
        "coord2": _user(conn, "Luis Coordinador", "coordinator", "Central", "Humanidades"),
        "reviewer": _user(conn, "Roberto Revisor", "reviewer"),
        "reviewer2": _user(conn, "Rosa Revisora", "reviewer"),
        "authority": _user(conn, "Decano", "authority"),
        "system": _user(conn, "Sistema", "system"),
    }
    teachers = [
        _user(conn, "Docente 1", "teacher", "Central", "Ingeniería"),
        _user(conn, "Docente 2", "teacher", "Central", "Ingeniería"),
        _user(conn, "Docente 3", "teacher", "Norte", "Ingeniería"),
        _user(conn, "Docente 4", "teacher", "Norte", "Humanidades"),
        _user(conn, "Docente 5", "teacher", "Sur", "Humanidades"),
    ]
    ids["teachers"] = teachers
    ids["inactive_teacher"] = _user(conn, "Docente baja", "teacher", "Central", "Ingeniería", 0)
    ids["types"] = {}
    for code, name, ev, ev_type, flow in TASK_TYPES:
        ids["types"][code] = conn.execute(
            "INSERT INTO task_types(code, name, requires_evidence, evidence_type, flow, created_at)"
            " VALUES (?,?,?,?,?,?)", (code, name, ev, ev_type, flow, utcnow())).lastrowid
    return ids


def seed_scenario(conn, ids):
    """Tarea individual + tarea masiva (ambas publicadas) + un borrador."""
    coord = transitions.get_actor(conn, ids["coord"])
    t_ind = tasks.create_task(conn, coord, {
        "type_id": ids["types"]["upload_cv"], "title": "Subir CV actualizado",
        "description": "Cargue su CV en PDF.", "priority": "medium",
        "due_date": "2026-11-15", "reviewer_id": ids["reviewer"]})
    tasks.set_recipients(conn, coord, t_ind["id"],
                         {"mode": "users", "user_ids": [ids["teachers"][0]]})
    tasks.publish_task(conn, coord, t_ind["id"])

    t_mass = tasks.create_task(conn, coord, {
        "type_id": ids["types"]["update_program"], "title": "Actualizar programa del curso",
        "description": "Revise y actualice el programa vigente.", "priority": "high",
        "due_date": "2026-10-30", "reviewer_id": ids["reviewer"]})
    tasks.set_recipients(conn, coord, t_mass["id"], {"mode": "all"})
    tasks.publish_task(conn, coord, t_mass["id"])

    draft = tasks.create_task(conn, coord, {
        "type_id": ids["types"]["confirm_activity"], "title": "Confirmar jornada de inducción",
        "due_date": "2026-12-01"})

    first = conn.execute("SELECT id FROM assignments WHERE task_id = ? ORDER BY id LIMIT 2",
                         (t_mass["id"],)).fetchall()
    t1 = transitions.get_actor(conn, ids["teachers"][0])
    transitions.perform(conn, first[0]["id"], "start", t1)
    transitions.perform(conn, first[0]["id"], "submit", t1)
    transitions.perform(conn, first[1]["id"], "start",
                        transitions.get_actor(conn, ids["teachers"][1]))
    return {"individual_task": t_ind["id"], "mass_task": t_mass["id"], "draft_task": draft["id"]}


def seed(conn):
    ids = seed_base(conn)
    ids.update(seed_scenario(conn, ids))
    return ids


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "workflow.db"
    conn = connect(path)
    init_db(conn)
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
        sys.exit(f"{path} ya tiene datos; bórrala para volver a sembrar.")
    print("Semilla creada:", seed(conn))
