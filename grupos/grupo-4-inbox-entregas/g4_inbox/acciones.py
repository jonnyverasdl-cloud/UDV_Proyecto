"""
g4_inbox.acciones — Las 6 transiciones de estado (start, submit, resubmit,
review, return, approve), AISLADAS en su propio router.

Decisión del 21/10: estas acciones pasan a ser de G3, no de G4. Este
archivo queda aquí por dos razones:
1. Para que el equipo de G4 pueda seguir probando el flujo completo en
   local (inbox -> detalle -> entregar -> revisar) mientras G3 no
   publique su propio motor.
2. Se comparte con G3 como referencia de cómo se ve la tabla de
   transiciones y las reglas duras del contrato — no para que lo copien
   tal cual, sino para que no tengan que adivinar el comportamiento
   esperado.

IMPORTANTE: acciones_router NUNCA se monta en el main.py de la raíz del
proyecto. Solo main.py de ESTA carpeta (el de pruebas locales de G4) lo
incluye. En la integración real, estas rutas las sirve G3.
"""

from typing import List, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

acciones_router = APIRouter(prefix="/api/v1", tags=["G4 - Acciones (temporal, pasa a G3)"])


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


class DevolucionIn(BaseModel):
    comment: str


def _transicionar(buscar_asignacion, assignment_id: int, accion: str,
                   rol_usuario: str, comentario: Optional[str] = None) -> dict:
    a = buscar_asignacion(assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    return ejecutar_transicion_g3(a, accion, rol_usuario, comentario)


def construir_acciones_router(buscar_asignacion):
    """Las rutas necesitan buscar_asignacion de routes.py — se las pasamos
    así en vez de importar routes.py desde aquí, para que acciones.py no
    dependa de routes.py (solo al revés, routes.py sí puede importar
    acciones_permitidas desde aquí sin crear un import circular).
    Lo llama SOLO el main.py de pruebas locales de G4 — nunca la raíz."""

    @acciones_router.post("/assignments/{assignment_id}/start")
    def iniciar(assignment_id: int, x_role: str = Header(default="docente")):
        return _transicionar(buscar_asignacion, assignment_id, "start", x_role)

    @acciones_router.post("/assignments/{assignment_id}/submit")
    def entregar(assignment_id: int, x_role: str = Header(default="docente")):
        a = buscar_asignacion(assignment_id)
        if a and a.get("requiere_archivo", True) and not a.get("files"):
            raise HTTPException(status_code=422, detail="Falta adjuntar evidencia antes de entregar")
        return _transicionar(buscar_asignacion, assignment_id, "submit", x_role)

    @acciones_router.post("/assignments/{assignment_id}/resubmit")
    def reenviar(assignment_id: int, x_role: str = Header(default="docente")):
        return _transicionar(buscar_asignacion, assignment_id, "resubmit", x_role)

    @acciones_router.post("/assignments/{assignment_id}/review")
    def tomar_revision(assignment_id: int, x_role: str = Header(default="revisor")):
        return _transicionar(buscar_asignacion, assignment_id, "review", x_role)

    @acciones_router.post("/assignments/{assignment_id}/return")
    def devolver(assignment_id: int, cuerpo: DevolucionIn, x_role: str = Header(default="revisor")):
        return _transicionar(buscar_asignacion, assignment_id, "return", x_role, cuerpo.comment)

    @acciones_router.post("/assignments/{assignment_id}/approve")
    def aprobar(assignment_id: int, x_role: str = Header(default="revisor")):
        return _transicionar(buscar_asignacion, assignment_id, "approve", x_role)

    return acciones_router
