"""
g4_inbox — Backend del Grupo 4 (Inbox y entregas docentes)
Proyecto integrador de API REST y workflow docente — UDV

Cómo correr esto:
    pip install -r requirements.txt
    uvicorn main:app --reload

Luego abran http://127.0.0.1:8000/docs — FastAPI genera ahí mismo una
pantalla donde pueden probar cada endpoint sin necesitar Postman.

IMPORTANTE — cosas temporales que hay que reemplazar más adelante:
1. No hay base de datos real todavía (G1). Los datos viven en la lista
   ASSIGNMENTS, en memoria. Al reiniciar el servidor, se pierden los cambios.
2. No hay autenticación real todavía (G2). Usamos encabezados HTTP simples
   (X-User, X-Role) para simular quién está llamando. Cuando G2 publique
   GET /me, estos endpoints dejan de leer encabezados y usan ese servicio.
3. El servicio de transiciones de G3 (g3_workflow) todavía no existe.
   La función ejecutar_transicion_g3(), más abajo, es un STUB que imita
   su comportamiento usando la misma tabla de transiciones del contrato.
   Es la ÚNICA función que hay que reemplazar cuando G3 esté listo — todo
   lo demás (los endpoints) ya queda igual.
"""

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List
import itertools

app = FastAPI(title="g4_inbox", version="0.1.0")


# ============================================================================
# "BASE DE DATOS" EN MEMORIA (reemplaza temporalmente a G1)
# ============================================================================
ASSIGNMENTS = [
    {
        "id": 101, "task_type": "Actualizar programa", "assignee": "docente1",
        "title": "Actualizar programa Programación Web", "status": "assigned",
        "priority": "alta", "due_date": "2026-10-10",
        "instructions": "Completar el formulario del programa por secciones.",
        "program_version_id": 32, "files": [], "comments": [],
        "draft_comment": None,
        "history": [{"action": "publish", "new_status": "assigned", "actor": "coordinacion"}],
    },
    {
        "id": 102, "task_type": "Subir ficha o CV", "assignee": "docente1",
        "title": "Actualizar CV docente 2026", "status": "in_progress",
        "priority": "media", "due_date": "2026-10-05",
        "instructions": "Adjuntar CV actualizado en PDF.",
        "program_version_id": None, "files": [], "comments": [],
        "draft_comment": None,
        "history": [
            {"action": "publish", "new_status": "assigned", "actor": "coordinacion"},
            {"action": "start", "new_status": "in_progress", "actor": "docente1"},
        ],
    },
    {
        "id": 103, "task_type": "Entregar factura", "assignee": "docente1",
        "title": "Factura de honorarios septiembre", "status": "submitted",
        "priority": "alta", "due_date": "2026-10-02",
        "instructions": "Adjuntar factura con número, fecha y monto.",
        "program_version_id": None,
        "files": [{"file_id": "f-001", "name": "factura_sept.pdf"}],
        "comments": [], "draft_comment": None,
        "history": [
            {"action": "publish", "new_status": "assigned", "actor": "coordinacion"},
            {"action": "start", "new_status": "in_progress", "actor": "docente1"},
            {"action": "submit", "new_status": "submitted", "actor": "docente1"},
        ],
    },
]

_siguiente_id = itertools.count(start=max(a["id"] for a in ASSIGNMENTS) + 1)


def buscar_asignacion(assignment_id: int) -> Optional[dict]:
    for a in ASSIGNMENTS:
        if a["id"] == assignment_id:
            return a
    return None


# ============================================================================
# STUB DEL SERVICIO DE TRANSICIONES DE G3 (g3_workflow)
# Cuando el equipo de G3 publique su servicio real, esta sección completa
# sera reemplazada por una llamada a su API/función — el resto del archivo
# no cambia, porque ya llama a ejecutar_transicion_g3() como si fuera externo.
# ============================================================================

# (estado_actual, accion) -> {nuevo_estado, actor que puede ejecutarla}
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
    """Imita el servicio real de G3: valida, cambia el estado, guarda historial."""
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
    """También saldría del servicio real de G3 cuando exista."""
    return [accion for (estado, accion) in TABLA_TRANSICIONES if estado == asignacion["status"]]


# ============================================================================
# MODELOS DE ENTRADA (lo que el frontend manda en el body)
# ============================================================================
class BorradorIn(BaseModel):
    comment: Optional[str] = None


class ComentarioIn(BaseModel):
    text: str


class ArchivoIn(BaseModel):
    file_id: str   # viene de POST /api/v1/files del Grupo 2
    name: str


class DevolucionIn(BaseModel):
    comment: str


# ============================================================================
# 1-3. INBOX Y DETALLE 
# ============================================================================
@app.get("/api/v1/inbox")
def listar_inbox(page: int = 1, per_page: int = 10, status: Optional[str] = None,
                  x_user: str = Header(default="docente1")):
    propias = [a for a in ASSIGNMENTS if a["assignee"] == x_user]
    if status:
        propias = [a for a in propias if a["status"] == status]
    inicio = (page - 1) * per_page
    pagina = propias[inicio: inicio + per_page]
    return {"data": pagina, "page": page, "per_page": per_page, "total": len(propias)}


@app.get("/api/v1/inbox/summary")
def resumen_inbox(x_user: str = Header(default="docente1")):
    resumen: dict = {}
    for a in ASSIGNMENTS:
        if a["assignee"] == x_user:
            resumen[a["status"]] = resumen.get(a["status"], 0) + 1
    return resumen


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
                      x_user: str = Header(default="docente1")):
    a = buscar_asignacion(assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    nuevo = {"author": x_user, "text": comentario.text}
    a["comments"].append(nuevo)
    return nuevo


# ============================================================================
# 7. VINCULAR ARCHIVO — listo, pero OJO cómo debe llegar la información
# ============================================================================
@app.post("/api/v1/assignments/{assignment_id}/files")
def vincular_archivo(assignment_id: int, archivo: ArchivoIn):
    """
    Este endpoint NO recibe el archivo en sí (no sube bytes). El archivo ya
    debió subirse ANTES a POST /api/v1/files del Grupo 2, que devuelve un
    file_id. Aquí solo guardamos ese file_id + su nombre junto a la asignación.

    Body esperado:
        { "file_id": "f-123", "name": "evidencia.pdf" }
    """
    a = buscar_asignacion(assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    a["files"].append({"file_id": archivo.file_id, "name": archivo.name})
    return {"status": "archivo vinculado", "files": a["files"]}


# ============================================================================
# 8-13. TRANSICIONES — funcionando ya, usando el stub de G3 de arriba.
# El día que G3 publique su servicio real, solo se cambia
# ejecutar_transicion_g3() — estos seis endpoints no se tocan.
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
