"""Notificaciones internas (escenarios G6-04 a G6-13).

Los grupos 3, 4 y 5 emiten los eventos oficiales (CONTRATO_COMUN.md §3) y el
G6 los convierte en una notificación por destinatario. Aquí vive la lógica:
qué eventos existen, qué datos trae cada uno, cómo se evita duplicar y quién
puede marcar una notificación como leída.

Quién inició sesión lo decide api.py con el middleware del G2. Los errores
salen con el formato común del G2 (g2_api.middleware.error_handler).
"""

import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from g2_api.middleware.error_handler import ErrorCode, api_error


@dataclass(frozen=True)
class TipoEvento:
    nombre: str
    campos: tuple[str, ...]  # Datos que el emisor debe enviar en "data"
    plantilla: str           # Mensaje que ve el destinatario


# Los destinatarios los elige quien emite el evento (el G3, G4 o G5 conoce al
# docente, al revisor y al coordinador); la tabla del CONTRATO.md §3 dice a
# quién va cada uno.
EVENTOS: dict[str, TipoEvento] = {e.nombre: e for e in (
    TipoEvento("task.published", ("task_title", "due_date"),
               "Nueva tarea asignada: «{task_title}». Fecha límite: {due_date}."),
    TipoEvento("assignment.due_soon", ("task_title", "due_date"),
               "La tarea «{task_title}» vence el {due_date}."),
    TipoEvento("assignment.submitted", ("task_title",),
               "Hay una entrega de «{task_title}» lista para revisión."),
    TipoEvento("assignment.returned", ("task_title", "comment"),
               "Tu entrega de «{task_title}» fue devuelta. Observación: {comment}"),
    TipoEvento("assignment.approved", ("task_title",),
               "La entrega de «{task_title}» fue aprobada."),
    TipoEvento("program.authorized", ("program_name",),
               "Se autorizó una nueva versión del programa «{program_name}»."),
    TipoEvento("task.cancelled", ("task_title",),
               "La tarea «{task_title}» fue cancelada."),
)}

TEXTO_MAXIMO = 500


@dataclass
class Notificacion:
    id: int
    usuario_id: int
    evento: str
    evento_id: str
    mensaje: str
    created_at: str
    read_at: str | None = None

    def como_dict(self) -> dict[str, Any]:
        return {"id": self.id, "event": self.evento, "message": self.mensaje,
                "is_read": self.read_at is not None,
                "created_at": self.created_at, "read_at": self.read_at}


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class RepositorioNotificacionesEnMemoria:
    """Guarda las notificaciones en memoria mientras el G1 entrega la tabla.

    Para pasar a MySQL se crea un repositorio con los mismos métodos. Ahí
    agregar_de_evento debe correr en UNA transacción, y la tabla necesita una
    llave única (evento_id, usuario_id) para que la base también impida
    duplicados.
    """

    def __init__(self) -> None:
        self._notificaciones: list[Notificacion] = []
        self._siguiente_id = 1
        self._candado = threading.Lock()

    def agregar_de_evento(self, evento: str, evento_id: str,
                          mensajes: dict[int, str]) -> list[Notificacion]:
        """Guarda una notificación por destinatario: todas o ninguna.

        Si el evento ya se procesó para un destinatario, ese no se repite.
        """
        with self._candado:
            ya_avisados = {n.usuario_id for n in self._notificaciones
                           if n.evento_id == evento_id}
            pendientes = [(u, m) for u, m in mensajes.items() if u not in ya_avisados]
            nuevas = [
                Notificacion(id=self._siguiente_id + i, usuario_id=usuario_id,
                             evento=evento, evento_id=evento_id,
                             mensaje=mensaje, created_at=_ahora())
                for i, (usuario_id, mensaje) in enumerate(pendientes)
            ]
            # Se arma toda la lista antes de tocar los datos guardados: si algo
            # falla arriba, no queda ninguna notificación a medias (G6-18).
            self._notificaciones.extend(nuevas)
            self._siguiente_id += len(nuevas)
            return nuevas

    def listar_de(self, usuario_id: int) -> list[Notificacion]:
        with self._candado:
            return [n for n in self._notificaciones if n.usuario_id == usuario_id]

    def marcar_leida(self, notificacion_id: int, usuario_id: int) -> Notificacion | None:
        """Marca solo si la notificación es de ese usuario; si no, devuelve None."""
        with self._candado:
            for n in self._notificaciones:
                if n.id == notificacion_id and n.usuario_id == usuario_id:
                    if n.read_at is None:
                        n.read_at = _ahora()
                    return n
            return None


def _error_de_campo(campo: str, codigo: str, mensaje: str) -> dict[str, str]:
    # Misma forma que usa el G2 para el detalle de un 422.
    return {"field": campo, "code": codigo, "message": mensaje}


def _es_entero(valor: Any) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool)


def validar_evento(evento: Any) -> tuple[TipoEvento, str, list[int], dict[str, str]]:
    """Revisa un evento {"id", "name", "recipients", "data"} antes de guardar nada."""
    if not isinstance(evento, dict):
        raise api_error(422, ErrorCode.VALIDATION_ERROR, "El evento debe ser un objeto.",
                        [_error_de_campo("_body", "OBJECT_TYPE", "Envía un objeto.")])

    errores: list[dict[str, str]] = []
    tipo = EVENTOS.get(evento.get("name")) if isinstance(evento.get("name"), str) else None
    if tipo is None:
        errores.append(_error_de_campo("name", "UNKNOWN_EVENT", "Evento desconocido."))

    evento_id = evento.get("id")
    if not isinstance(evento_id, str) or not evento_id.strip():
        errores.append(_error_de_campo(
            "id", "REQUIRED", "Cada evento necesita un identificador único (texto)."))

    destinatarios = evento.get("recipients")
    if (not isinstance(destinatarios, list) or not destinatarios
            or not all(_es_entero(u) and u > 0 for u in destinatarios)):
        errores.append(_error_de_campo(
            "recipients", "INVALID", "Envía una lista con los id de los destinatarios."))

    datos = evento.get("data")
    if not isinstance(datos, dict):
        errores.append(_error_de_campo("data", "OBJECT_TYPE",
                                       "Envía los datos del evento como objeto."))
        datos = {}
    if tipo is not None:
        for campo in tipo.campos:
            valor = datos.get(campo)
            if not isinstance(valor, str) or not valor.strip():
                errores.append(_error_de_campo(f"data.{campo}", "REQUIRED",
                                               "Campo obligatorio."))
            elif len(valor) > TEXTO_MAXIMO:
                errores.append(_error_de_campo(
                    f"data.{campo}", "TOO_LONG",
                    f"Usa como máximo {TEXTO_MAXIMO} caracteres."))

    if errores:
        raise api_error(422, ErrorCode.VALIDATION_ERROR,
                        "El evento no es válido.", errores)
    limpios = {c: " ".join(datos[c].split()) for c in tipo.campos}
    # dict.fromkeys quita destinatarios repetidos conservando el orden.
    return tipo, evento_id.strip(), list(dict.fromkeys(destinatarios)), limpios


class ServicioNotificaciones:
    def __init__(self, repositorio: RepositorioNotificacionesEnMemoria) -> None:
        self.repositorio = repositorio

    def procesar_evento(self, evento: Any) -> list[dict[str, Any]]:
        """Crea las notificaciones de un evento emitido por el G3, G4 o G5.

        Procesar dos veces el mismo evento (mismo "id") no duplica nada
        (G6-11). Devuelve solo las notificaciones nuevas.
        """
        tipo, evento_id, destinatarios, datos = validar_evento(evento)
        mensaje = tipo.plantilla.format(**datos)
        nuevas = self.repositorio.agregar_de_evento(
            tipo.nombre, evento_id, {u: mensaje for u in destinatarios})
        return [n.como_dict() for n in nuevas]

    def listar(self, usuario_id: int, *, no_leidas: bool = False) -> list[dict[str, Any]]:
        """Solo las del usuario, de la más reciente a la más antigua. La página la arma api.py."""
        notificaciones = self.repositorio.listar_de(usuario_id)
        if no_leidas:
            notificaciones = [n for n in notificaciones if n.read_at is None]
        notificaciones.sort(key=lambda n: n.id, reverse=True)
        return [n.como_dict() for n in notificaciones]

    def marcar_leida(self, usuario_id: int, notificacion_id: int) -> dict[str, Any]:
        """Marca como leída una notificación propia (G6-12 y G6-13).

        La de otra persona responde 404, igual que una inexistente, para no
        revelar qué notificaciones existen.
        """
        notificacion = self.repositorio.marcar_leida(notificacion_id, usuario_id)
        if notificacion is None:
            raise api_error(404, ErrorCode.NOT_FOUND, "No existe esa notificación.")
        return notificacion.como_dict()
