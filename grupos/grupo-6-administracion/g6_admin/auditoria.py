"""Auditoría transversal (escenarios G6-14, G6-15 y G6-30 a G6-33).

Cada acción importante deja un registro con quién la hizo, cuándo, sobre qué
entidad y qué cambió. Los registros solo se agregan: no hay forma de editarlos
ni de borrarlos (CONTRATO_COMUN.md §1, "Auditoría").

Las transiciones de estado (G6-15) las reportan el G3 (tareas y asignaciones)
y el G5 (versiones de programa); los cambios de catálogos los registra el
propio G6. Quién puede consultar (solo administración) lo decide api.py con el
middleware del G2.
"""

import threading
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any

from g2_api.middleware.error_handler import ErrorCode, api_error

# Estados oficiales (CONTRATO_COMUN.md §2). Una transición solo se acepta con
# estados de esta lista, para que el historial no guarde nombres inventados.
ESTADOS_TAREA = frozenset({"draft", "assigned", "in_progress", "submitted",
                           "under_review", "returned", "approved", "closed",
                           "cancelled"})
ESTADOS_PROGRAMA = frozenset({"draft", "submitted", "under_review", "returned",
                              "approved", "authorized", "superseded"})
ESTADOS_POR_ENTIDAD: dict[str, frozenset[str]] = {
    "task": ESTADOS_TAREA,
    "assignment": ESTADOS_TAREA,
    "program_version": ESTADOS_PROGRAMA,
}

ACCION_TRANSICION = "transition"
TEXTO_MAXIMO = 120
COMENTARIO_MAXIMO = 1000


@dataclass(frozen=True)
class RegistroAuditoria:
    id: int
    actor_id: int
    accion: str
    entidad: str
    entidad_id: int
    fecha: str
    estado_anterior: str | None = None
    estado_nuevo: str | None = None
    comentario: str | None = None
    cambios: dict[str, Any] = field(default_factory=dict)

    def como_dict(self) -> dict[str, Any]:
        return {"id": self.id, "actor_id": self.actor_id, "action": self.accion,
                "entity": self.entidad, "entity_id": self.entidad_id,
                "created_at": self.fecha, "from_state": self.estado_anterior,
                "to_state": self.estado_nuevo, "comment": self.comentario,
                "changes": dict(self.cambios)}


class RepositorioAuditoriaEnMemoria:
    """Guarda la auditoría en memoria mientras el G1 entrega la tabla.

    Solo tiene agregar y listar a propósito: el repositorio con MySQL debe
    tener los mismos dos métodos y ningún UPDATE ni DELETE sobre la tabla.
    """

    def __init__(self) -> None:
        self._registros: list[RegistroAuditoria] = []
        self._siguiente_id = 1
        self._candado = threading.Lock()

    def agregar(self, **datos: Any) -> RegistroAuditoria:
        with self._candado:
            registro = RegistroAuditoria(
                id=self._siguiente_id,
                fecha=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                **datos)
            self._siguiente_id += 1
            self._registros.append(registro)
            return registro

    def listar(self) -> list[RegistroAuditoria]:
        with self._candado:
            return list(self._registros)


def _error_de_campo(campo: str, codigo: str, mensaje: str) -> dict[str, str]:
    # Misma forma que usa el G2 para el detalle de un 422.
    return {"field": campo, "code": codigo, "message": mensaje}


def _es_entero_positivo(valor: Any) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool) and valor > 0


def _texto(valor: Any) -> bool:
    return isinstance(valor, str) and bool(valor.strip()) and len(valor) <= TEXTO_MAXIMO


def _fallar_si_hay(errores: list[dict[str, str]]) -> None:
    if errores:
        raise api_error(422, ErrorCode.VALIDATION_ERROR,
                        "Revisa los campos marcados.", errores)


class ServicioAuditoria:
    def __init__(self, repositorio: RepositorioAuditoriaEnMemoria) -> None:
        self.repositorio = repositorio

    def registrar(self, *, actor_id: Any, accion: Any, entidad: Any,
                  entidad_id: Any, cambios: dict[str, Any] | None = None) -> dict[str, Any]:
        """Registra una acción que no es transición (G6-14), como crear un registro."""
        errores = self._validar_basico(actor_id, accion, entidad, entidad_id)
        if accion == ACCION_TRANSICION:
            errores.append(_error_de_campo("action", "USE_TRANSITION",
                                           "Para una transición usa registrar_transicion."))
        if cambios is not None and not isinstance(cambios, dict):
            errores.append(_error_de_campo("changes", "OBJECT_TYPE",
                                           "Envía los cambios como objeto."))
        _fallar_si_hay(errores)
        return self.repositorio.agregar(
            actor_id=actor_id, accion=accion.strip(), entidad=entidad.strip(),
            entidad_id=entidad_id, cambios=dict(cambios or {})).como_dict()

    def registrar_transicion(self, *, actor_id: Any, entidad: Any, entidad_id: Any,
                             estado_anterior: Any, estado_nuevo: Any,
                             comentario: Any = "") -> dict[str, Any]:
        """Registra un cambio de estado con lo que pide el contrato común (G6-15).

        El G3 y el G5 la llaman dentro de la misma operación que cambia el
        estado, para que no quede una transición sin su registro.
        """
        errores = self._validar_basico(actor_id, ACCION_TRANSICION, entidad, entidad_id)
        estados = ESTADOS_POR_ENTIDAD.get(entidad) if isinstance(entidad, str) else None
        if estados is None and not any(e["field"] == "entity" for e in errores):
            errores.append(_error_de_campo(
                "entity", "NO_STATES",
                "Entidad sin estados oficiales. Usa: "
                + ", ".join(sorted(ESTADOS_POR_ENTIDAD)) + "."))
        if estados is not None:
            if estado_anterior not in estados:
                errores.append(_error_de_campo("from_state", "UNKNOWN_STATE",
                                               "Estado no reconocido para esta entidad."))
            if estado_nuevo not in estados:
                errores.append(_error_de_campo("to_state", "UNKNOWN_STATE",
                                               "Estado no reconocido para esta entidad."))
            elif estado_nuevo == estado_anterior:
                errores.append(_error_de_campo("to_state", "SAME_STATE",
                                               "El estado nuevo debe ser distinto del anterior."))
        if not isinstance(comentario, str) or len(comentario) > COMENTARIO_MAXIMO:
            errores.append(_error_de_campo(
                "comment", "INVALID",
                f"Debe ser texto de hasta {COMENTARIO_MAXIMO} caracteres."))
        _fallar_si_hay(errores)
        return self.repositorio.agregar(
            actor_id=actor_id, accion=ACCION_TRANSICION, entidad=entidad,
            entidad_id=entidad_id, estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo, comentario=comentario.strip()).como_dict()

    @staticmethod
    def _validar_basico(actor_id: Any, accion: Any, entidad: Any,
                        entidad_id: Any) -> list[dict[str, str]]:
        errores: list[dict[str, str]] = []
        if not _es_entero_positivo(actor_id):
            errores.append(_error_de_campo("actor_id", "INVALID",
                                           "Debe ser el id del usuario que hizo la acción."))
        if not _texto(accion):
            errores.append(_error_de_campo("action", "REQUIRED", "Campo obligatorio."))
        if not _texto(entidad):
            errores.append(_error_de_campo("entity", "REQUIRED", "Campo obligatorio."))
        if not _es_entero_positivo(entidad_id):
            errores.append(_error_de_campo("entity_id", "INVALID",
                                           "Debe ser un número entero positivo."))
        return errores

    def consultar(self, *, actor_id: int | None = None, desde: date | None = None,
                  hasta: date | None = None, entidad: str | None = None,
                  accion: str | None = None) -> list[dict[str, Any]]:
        """Consulta filtrada, de lo más reciente a lo más antiguo (G6-30 a G6-33).

        Las fechas incluyen el día completo, en UTC. La página la arma api.py.
        """
        if desde and hasta and desde > hasta:
            _fallar_si_hay([_error_de_campo(
                "to", "DATE_RANGE", "Debe ser igual o posterior a la fecha inicial.")])

        registros = self.repositorio.listar()
        if actor_id is not None:
            registros = [r for r in registros if r.actor_id == actor_id]
        if entidad:
            registros = [r for r in registros if r.entidad == entidad.strip()]
        if accion:
            registros = [r for r in registros if r.accion == accion.strip()]
        if desde:
            registros = [r for r in registros if r.fecha[:10] >= desde.isoformat()]
        if hasta:
            registros = [r for r in registros if r.fecha[:10] <= hasta.isoformat()]

        registros.sort(key=lambda r: r.id, reverse=True)
        return [r.como_dict() for r in registros]
