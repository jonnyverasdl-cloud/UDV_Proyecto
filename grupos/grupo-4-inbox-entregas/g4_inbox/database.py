"""
g4_inbox.database — Conexión real a MySQL (reemplaza datos_ejemplo.py / DETALLE_EXTRA)

Lee de las vistas que ya publicó G1: v_inbox, v_panel_tarea, v_historial_tarea,
más las tablas base (tarea, tarea_destinatario, entrega_borrador, comentario,
archivo, entrega) para el detalle completo.

"""

from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from .config import DATABASE_URL
from .inbox import Asignacion

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=1800)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

_ACCION_POR_TRANSICION = {
    ("assigned", "in_progress"): "start",
    ("in_progress", "submitted"): "submit",
    ("returned", "submitted"): "resubmit",
    ("submitted", "under_review"): "review",
    ("under_review", "returned"): "return",
    ("under_review", "approved"): "approve",
}


def _sesion(actor_id: Optional[int] = None):
    sesion = SessionLocal()
    if actor_id is not None:
        sesion.execute(text("SET @actor_id = :actor_id"), {"actor_id": actor_id})
    return sesion


def fetch_asignaciones_inbox(usuario_id: Optional[int] = None) -> List[Asignacion]:
    sql = """
        SELECT asignacion_id, usuario_id, tarea_id, titulo, tipo_codigo,
               estado_codigo, prioridad, fecha_limite
        FROM v_inbox
    """
    parametros = {}
    if usuario_id is not None:
        sql += " WHERE usuario_id = :usuario_id"
        parametros["usuario_id"] = usuario_id

    sesion = _sesion()
    try:
        filas = sesion.execute(text(sql), parametros).mappings().all()
    finally:
        sesion.close()

    resultado = []
    for fila in filas:
        fecha = fila["fecha_limite"]
        due_at = fecha.date() if isinstance(fecha, (date, datetime)) else None
        resultado.append(Asignacion(
            id=fila["asignacion_id"],
            assignee_id=fila["usuario_id"],
            title=fila["titulo"],
            task_type=fila["tipo_codigo"],
            status=fila["estado_codigo"],
            priority=fila["prioridad"],
            due_at=due_at,
        ))
    return resultado


def fetch_detalle_asignacion(assignment_id: int) -> Optional[dict]:
    sesion = _sesion()
    try:
        cabecera = sesion.execute(text("""
            SELECT td.id AS asignacion_id, td.usuario_id, td.estado_codigo,
                   t.id AS tarea_id, t.titulo, t.descripcion, t.prioridad,
                   t.programa_version_id,
                   COALESCE(td.fecha_limite, t.fecha_limite) AS fecha_limite
            FROM tarea_destinatario td
            JOIN tarea t ON t.id = td.tarea_id
            WHERE td.id = :id
        """), {"id": assignment_id}).mappings().first()
        if cabecera is None:
            return None

        borrador = sesion.execute(text("""
            SELECT contenido_texto FROM entrega_borrador
            WHERE tarea_destinatario_id = :id
        """), {"id": assignment_id}).mappings().first()

        comentarios = sesion.execute(text("""
            SELECT autor_id AS author, contenido AS text
            FROM comentario
            WHERE tarea_destinatario_id = :id AND eliminado_en IS NULL
            ORDER BY creado_en
        """), {"id": assignment_id}).mappings().all()

        archivos = sesion.execute(text("""
            SELECT a.id AS file_id, a.nombre_original AS name
            FROM archivo a
            JOIN entrega e ON e.id = a.entrega_id
            WHERE e.tarea_destinatario_id = :id AND a.eliminado_en IS NULL
        """), {"id": assignment_id}).mappings().all()

        historial = sesion.execute(text("""
            SELECT estado_anterior, estado_nuevo, actor, comentario, creado_en
            FROM v_historial_tarea
            WHERE asignacion_id = :id
            ORDER BY creado_en
        """), {"id": assignment_id}).mappings().all()
    finally:
        sesion.close()

    fecha = cabecera["fecha_limite"]
    due_at = fecha.isoformat() if isinstance(fecha, (date, datetime)) else None

    return {
        "id": cabecera["asignacion_id"],
        "assignee_id": cabecera["usuario_id"],
        "title": cabecera["titulo"],
        "task_type": None,
        "status": cabecera["estado_codigo"],
        "priority": cabecera["prioridad"],
        "due_at": due_at,
        "instructions": cabecera["descripcion"] or "",
        "program_version_id": cabecera["programa_version_id"],
        "draft_comment": borrador["contenido_texto"] if borrador else None,
        "comments": [{"author": str(c["author"]), "text": c["text"]} for c in comentarios],
        "files": [{"file_id": str(f["file_id"]), "name": f["name"]} for f in archivos],
        "history": [
            {
                "action": _ACCION_POR_TRANSICION.get((h["estado_anterior"], h["estado_nuevo"])),
                "new_status": h["estado_nuevo"],
                "actor": h["actor"],
            }
            for h in historial
        ],
    }


def probar_conexion() -> bool:
    try:
        sesion = _sesion()
        sesion.execute(text("SELECT 1"))
        sesion.close()
        return True
    except Exception:
        return False
