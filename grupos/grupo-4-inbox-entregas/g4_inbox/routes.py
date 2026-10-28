"""
g4_inbox.routes — El APIRouter real del Grupo 4 (solo bandeja/inbox y detalle)

Esto es lo único que se monta en la aplicación raíz del proyecto. Las 6
acciones de transición (start, submit, review...) YA NO viven aquí desde
el 21/10 — pasaron a ser de G3 (ver acciones.py para la versión que G4
sigue usando solo en pruebas locales).

Para correr y probar G4 solo, ver main.py de esta misma carpeta.

IMPORTANTE:
1. Base de datos: con G4_USAR_MYSQL=1 lee de MySQL real (database.py);
   si no, usa datos en memoria (datos_ejemplo.py + DETALLE_EXTRA).
2. Autenticación REAL, desde el 24/10 — ya no se simula con X-User. Se
   usa obtener_usuario_actual de g2_api, que exige un token Bearer
   válido y devuelve el Usuario real de la base. Esto es una dependencia
   dura: g4_inbox YA NO CORRE sin que g2_api esté disponible en el
   PYTHONPATH (antes el import de G2 era opcional; para autenticación,
   que sea opcional sería un hueco de seguridad — GET /inbox nunca debe
   poder responder sin un token válido).
"""

import os
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from g2_api.routers.auth import obtener_usuario_actual
from g2_api.models import Usuario

from .acciones import acciones_permitidas
from .datos_ejemplo import asignaciones_ejemplo
from .inbox import Asignacion, ErrorValidacion, listar_inbox, resumen_inbox

USAR_MYSQL = os.environ.get("G4_USAR_MYSQL") == "1"
if USAR_MYSQL:
    from . import database

router = APIRouter(prefix="/api/v1", tags=["G4 - Inbox y entregas"])


# ============================================================================
# "BASE DE DATOS" EN MEMORIA (reemplaza temporalmente a G1 si USAR_MYSQL=0)
# ============================================================================
REQUIERE_ARCHIVO_POR_TIPO = {
    "Actualizar programa": False,
    "Subir ficha o CV": True,
    "Entregar factura": True,
    "Confirmar actividad": False,
    "Cargar evidencia": True,
}

DETALLE_EXTRA = {
    1: {"instructions": "Completar el formulario del programa por secciones.",
        "program_version_id": 32, "files": [], "comments": [], "draft_comment": None},
    2: {"instructions": "Adjuntar el CV en PDF con vigencia no mayor a 6 meses.",
        "program_version_id": None, "files": [], "comments": [], "draft_comment": None},
    3: {"instructions": "Adjuntar factura con número, fecha y monto correctos.",
        "program_version_id": None,
        "files": [{"file_id": "f-001", "name": "factura_sept.pdf"}],
        "comments": [{"author": "revisor1", "text": "El monto no coincide. Verificar y reenviar."}],
        "draft_comment": "Factura corregida con el monto correcto."},
    4: {"instructions": "Adjuntar evidencia fotográfica o documento del laboratorio.",
        "program_version_id": None,
        "files": [{"file_id": "f-002", "name": "evidencia_lab1.pdf"}],
        "comments": [], "draft_comment": None},
    5: {"instructions": "Confirmar asistencia al claustro de este ciclo.",
        "program_version_id": None, "files": [], "comments": [], "draft_comment": None},
    6: {"instructions": "Confirmar el horario de tutorías para este ciclo.",
        "program_version_id": None, "files": [], "comments": [], "draft_comment": None},
    7: {"instructions": "Evidencia ya aprobada del proyecto integrador.",
        "program_version_id": None,
        "files": [{"file_id": "f-003", "name": "evidencia_proyecto.pdf"}],
        "comments": [], "draft_comment": None},
    8: {"instructions": "Completar el formulario del programa de Bases de Datos.",
        "program_version_id": 40, "files": [], "comments": [], "draft_comment": None},
    9: {"instructions": "Factura privada del docente 2 — no debe verla el docente 1.",
        "program_version_id": None, "files": [], "comments": [], "draft_comment": None},
    10: {"instructions": "CV del docente 2 — no debe verlo el docente 1.",
         "program_version_id": None, "files": [], "comments": [], "draft_comment": None},
}


def _construir_db() -> List[dict]:
    base = [a.to_dict() for a in asignaciones_ejemplo()]
    for item in base:
        item.update(DETALLE_EXTRA.get(item["id"], {}))
        item["requiere_archivo"] = REQUIERE_ARCHIVO_POR_TIPO.get(item["task_type"], True)
        item["history"] = [{"action": "publish", "new_status": "assigned", "actor": "coordinacion"}]
    return base


DB: List[dict] = _construir_db()


def buscar_asignacion(assignment_id: int) -> Optional[dict]:
    if USAR_MYSQL:
        return database.fetch_detalle_asignacion(assignment_id)
    for a in DB:
        if a["id"] == assignment_id:
            return a
    return None


def _asignaciones_para_inbox() -> List[Asignacion]:
    if USAR_MYSQL:
        return database.fetch_asignaciones_inbox()
    return [
        Asignacion(
            id=d["id"], assignee_id=d["assignee_id"], title=d["title"],
            task_type=d["task_type"], status=d["status"], priority=d["priority"],
            due_at=date.fromisoformat(d["due_at"]) if d["due_at"] else None,
        )
        for d in DB
    ]


# ============================================================================
# MODELOS DE ENTRADA
# ============================================================================
class BorradorIn(BaseModel):
    comment: Optional[str] = None


class ComentarioIn(BaseModel):
    text: str


class ArchivoIn(BaseModel):
    file_id: str
    name: str


# ============================================================================
# 1-2. INBOX — ahora exige token real y filtra por el usuario del token,
# nunca por un header que cualquiera podía escribir.
# ============================================================================
@router.get("/inbox")
def inbox(q: str = "", status: Optional[str] = None, page: int = 1, per_page: int = 20,
           usuario: Usuario = Depends(obtener_usuario_actual)):
    try:
        return listar_inbox(_asignaciones_para_inbox(), usuario.id,
                             q=q, status=status, page=page, per_page=per_page)
    except ErrorValidacion as e:
        raise HTTPException(status_code=422, detail=e.details)


@router.get("/inbox/summary")
def inbox_summary(usuario: Usuario = Depends(obtener_usuario_actual)):
    return resumen_inbox(_asignaciones_para_inbox(), usuario.id)


# ============================================================================
# 3. DETALLE
# ============================================================================
@router.get("/assignments/{assignment_id}")
def detalle_asignacion(assignment_id: int, usuario: Usuario = Depends(obtener_usuario_actual)):
    a = buscar_asignacion(assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    return {**a, "allowed_actions": acciones_permitidas(a)}


# ============================================================================
# 4. BORRADOR
# ============================================================================
@router.put("/assignments/{assignment_id}/submission-draft")
def guardar_borrador(assignment_id: int, borrador: BorradorIn,
                      usuario: Usuario = Depends(obtener_usuario_actual)):
    a = buscar_asignacion(assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    a["draft_comment"] = borrador.comment
    return {"status": "borrador guardado", "draft_comment": a["draft_comment"]}


# ============================================================================
# 5-6. COMENTARIOS
# ============================================================================
@router.get("/assignments/{assignment_id}/comments")
def listar_comentarios(assignment_id: int, usuario: Usuario = Depends(obtener_usuario_actual)):
    a = buscar_asignacion(assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    return a["comments"]


@router.post("/assignments/{assignment_id}/comments")
def crear_comentario(assignment_id: int, comentario: ComentarioIn,
                      usuario: Usuario = Depends(obtener_usuario_actual)):
    a = buscar_asignacion(assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    nuevo = {"author": str(usuario.id), "text": comentario.text}
    a["comments"].append(nuevo)
    return nuevo


# ============================================================================
# 7. VINCULAR ARCHIVO
# ============================================================================
@router.post("/assignments/{assignment_id}/files")
def vincular_archivo(assignment_id: int, archivo: ArchivoIn,
                      usuario: Usuario = Depends(obtener_usuario_actual)):
    a = buscar_asignacion(assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    a["files"].append({"file_id": archivo.file_id, "name": archivo.name})
    return {"status": "archivo vinculado", "files": a["files"]}
