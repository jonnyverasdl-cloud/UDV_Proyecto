"""
g4_inbox — Backend del Grupo 4 (Inbox y entregas docentes)
Proyecto integrador de API REST y workflow docente — UDV

Cómo correr esto:
    pip install -r requirements.txt
    uvicorn main:app --reload

Luego:
    - http://127.0.0.1:8000/docs           → probar los 13 endpoints
    - http://127.0.0.1:8000/static/inbox.html → la pantalla real del inbox

IMPORTANTE — cosas temporales que hay que reemplazar más adelante:
1. No hay base de datos real todavía (G1). Los datos combinan
   datos_ejemplo.py (del inbox) con DETALLE_EXTRA (de abajo), en memoria.
2. No hay autenticación real todavía (G2). Usamos encabezados HTTP simples
   (X-User, X-Role) para simular quién está llamando.
3. El servicio de transiciones de G3 (g3_workflow) todavía no existe.
   ejecutar_transicion_g3(), más abajo, es un STUB que imita su
   comportamiento usando la misma tabla de transiciones del contrato.
"""

from datetime import date
from typing import List, Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .datos_ejemplo import asignaciones_ejemplo
from .inbox import Asignacion, ErrorValidacion, listar_inbox, resumen_inbox

app = FastAPI(title="g4_inbox", version="0.2.0")

# CORS: por defecto el navegador bloquea que una página le hable a este
# servidor. Esto se lo permite. "allow_origins=["*"]" es a propósito muy
# permisivo porque estamos en desarrollo local.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sirve la carpeta static/ en http://127.0.0.1:8000/static/... — así se
# puede abrir inbox.html ya hablándole a este mismo servidor, sin CORS.
app.mount("/static", StaticFiles(directory="g4_inbox/static"), name="static")

# Sirve grupos/udv-styles en http://127.0.0.1:8000/udv-styles/... — así el
# HTML del inbox y el de detalle encuentran udv.css con su ruta relativa
# (../../../udv-styles/...). Corre esto desde dentro de
# grupos/grupo-4-inbox-entregas, como dice el README.
app.mount("/udv-styles", StaticFiles(directory="../udv-styles"), name="udv-styles")


# ============================================================================
# "BASE DE DATOS" EN MEMORIA (reemplaza temporalmente a G1)
# ============================================================================

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
    """Une datos_ejemplo.py (del inbox) con DETALLE_EXTRA (de arriba)."""
    base = [a.to_dict() for a in asignaciones_ejemplo()]
    for item in base:
        item.update(DETALLE_EXTRA.get(item["id"], {}))
        item["history"] = [{"action": "publish", "new_status": "assigned", "actor": "coordinacion"}]
    return base


DB: List[dict] = _construir_db()


def buscar_asignacion(assignment_id: int) -> Optional[dict]:
    for a in DB:
        if a["id"] == assignment_id:
            return a
    return None


def _asignaciones_para_inbox() -> List[Asignacion]:
    """Reconstruye objetos Asignacion desde DB — inbox.py los exige así.

    Se recrean en cada pedido (no se guardan aparte) para que el inbox
    siempre refleje el estado más reciente después de una transición.
    """
    return [
        Asignacion(
            id=d["id"], assignee_id=d["assignee_id"], title=d["title"],
            task_type=d["task_type"], status=d["status"], priority=d["priority"],
            due_at=date.fromisoformat(d["due_at"]) if d["due_at"] else None,
        )
        for d in DB
    ]


# ============================================================================
# STUB DEL SERVICIO DE TRANSICIONES DE G3 (g3_workflow)
# ============================================================================
TABLA_TRANSICIONES = {
    ("assigned", "start"):       {"nuevo_estado": "in_progress", "actor": "docente"},
    ("in_progress", "submit"):   {"nuevo_estado": "submitted",   "actor": "docente"},
    ("returned", "resubmit"):    {"nuevo_estado": "submitted",   "actor": "docente"},
    ("submitted", "review"):     {"nuevo_estado": "under_review", "actor": "revisor"},
    ("under_review", "return"):  {"nuevo_estado": "returned",    "actor": "revisor"},
    ("under_review", "approve"): {"nuevo_estado": "approved",    "actor": "revisor"},
}


def ejecutar_transicion_g3(asignacion: dict, accion: str, rol_usuario: str,
                            comentario: Optional[str] = None) -> dict:
    clave = (asignacion["status"], accion)
    regla = TABLA_TRANSICIONES.get(clave)
    if regla is None:
        raise HTTPException(status_code=409, detail="Transición no permitida desde este estado")
    if regla["actor"] != rol_usuario:
        raise HTTPException(status_code=403, detail=f"Esta acción le corresponde al rol '{regla['actor']}'")
    if accion == "return" and not comentario:
        raise HTTPException(status_code=422, detail="La observación es obligatoria para devolver")
    asignacion["status"] = regla["nuevo_estado"]
    if comentario:
        asignacion["comments"].append({"author": rol_usuario, "text": comentario})
    asignacion["history"].append({"action": accion, "new_status": regla["nuevo_estado"], "actor": rol_usuario})
    return asignacion


def acciones_permitidas(asignacion: dict) -> List[str]:
    return [accion for (estado, accion) in TABLA_TRANSICIONES if estado == asignacion["status"]]


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


class DevolucionIn(BaseModel):
    comment: str


# ============================================================================
# 1-2. INBOX — usa la lógica real de inbox.py (compañero)
# ============================================================================
@app.get("/api/v1/inbox")
def inbox(q: str = "", status: Optional[str] = None, page: int = 1,
          per_page: int = 20, x_user: int = Header(default=1)):
    try:
        return listar_inbox(_asignaciones_para_inbox(), x_user,
                             q=q, status=status, page=page, per_page=per_page)
    except ErrorValidacion as e:
        raise HTTPException(status_code=422, detail=e.details)


@app.get("/api/v1/inbox/summary")
def inbox_summary(x_user: int = Header(default=1)):
    return resumen_inbox(_asignaciones_para_inbox(), x_user)


# ============================================================================
# 3. DETALLE — base propia
# ============================================================================
@app.get("/api/v1/assignments/{assignment_id}")
def detalle_asignacion(assignment_id: int):
    a = buscar_asignacion(assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    return {**a, "allowed_actions": acciones_permitidas(a)}


# ============================================================================
# 4. BORRADOR
# ============================================================================
@app.put("/api/v1/assignments/{assignment_id}/submission-draft")
def guardar_borrador(assignment_id: int, borrador: BorradorIn):
    a = buscar_asignacion(assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    a["draft_comment"] = borrador.comment
    return {"status": "borrador guardado", "draft_comment": a["draft_comment"]}


# ============================================================================
# 5-6. COMENTARIOS
# ============================================================================
@app.get("/api/v1/assignments/{assignment_id}/comments")
def listar_comentarios(assignment_id: int):
    a = buscar_asignacion(assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    return a["comments"]


@app.post("/api/v1/assignments/{assignment_id}/comments")
def crear_comentario(assignment_id: int, comentario: ComentarioIn,
                      x_user: int = Header(default=1)):
    a = buscar_asignacion(assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    nuevo = {"author": str(x_user), "text": comentario.text}
    a["comments"].append(nuevo)
    return nuevo


# ============================================================================
# 7. VINCULAR ARCHIVO
# ============================================================================
@app.post("/api/v1/assignments/{assignment_id}/files")
def vincular_archivo(assignment_id: int, archivo: ArchivoIn):
    a = buscar_asignacion(assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    a["files"].append({"file_id": archivo.file_id, "name": archivo.name})
    return {"status": "archivo vinculado", "files": a["files"]}


# ============================================================================
# 8-13. TRANSICIONES
# ============================================================================
def _transicionar(assignment_id: int, accion: str, rol_usuario: str,
                   comentario: Optional[str] = None) -> dict:
    a = buscar_asignacion(assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    return ejecutar_transicion_g3(a, accion, rol_usuario, comentario)


@app.post("/api/v1/assignments/{assignment_id}/start")
def iniciar(assignment_id: int, x_role: str = Header(default="docente")):
    return _transicionar(assignment_id, "start", x_role)


@app.post("/api/v1/assignments/{assignment_id}/submit")
def entregar(assignment_id: int, x_role: str = Header(default="docente")):
    a = buscar_asignacion(assignment_id)
    if a and not a.get("files"):
        raise HTTPException(status_code=422, detail="Falta adjuntar evidencia antes de entregar")
    return _transicionar(assignment_id, "submit", x_role)


@app.post("/api/v1/assignments/{assignment_id}/resubmit")
def reenviar(assignment_id: int, x_role: str = Header(default="docente")):
    return _transicionar(assignment_id, "resubmit", x_role)


@app.post("/api/v1/assignments/{assignment_id}/review")
def tomar_revision(assignment_id: int, x_role: str = Header(default="revisor")):
    return _transicionar(assignment_id, "review", x_role)


@app.post("/api/v1/assignments/{assignment_id}/return")
def devolver(assignment_id: int, cuerpo: DevolucionIn, x_role: str = Header(default="revisor")):
    return _transicionar(assignment_id, "return", x_role, cuerpo.comment)


@app.post("/api/v1/assignments/{assignment_id}/approve")
def aprobar(assignment_id: int, x_role: str = Header(default="revisor")):
    return _transicionar(assignment_id, "approve", x_role)
