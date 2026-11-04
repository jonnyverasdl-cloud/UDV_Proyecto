"""Auditoría transversal (escenarios G6-14, G6-15 y G6-30 a G6-33).

Cada acción importante deja un registro con quién la hizo, cuándo, sobre qué
entidad y qué cambió. Los registros solo se agregan: no hay forma de editarlos
ni de borrarlos (CONTRATO_COMUN.md §1, "Auditoría").

Los cambios de catálogos los registra el propio G6 en la tabla `auditoria` del
G1, la misma donde sus triggers registran tareas, programas y usuarios, y el G2
los inicios de sesión. Las transiciones de las asignaciones (G6-15) las guarda
el G3 en `tarea_transicion`; la consulta las une a la auditoría como acción
"transition", así muestra el historial completo sin que el G3 las escriba dos
veces. Otro módulo que no tenga historial propio, como el G5 con las versiones
de programa, usa registrar_transicion. Quién puede consultar
(administración y auditoría, los roles con el permiso audit.read del G1) lo
decide api.py con el middleware del G2.
"""

import json
from datetime import date, datetime, timedelta, timezone
from typing import Any

from g2_api.middleware.error_handler import ErrorCode, api_error
from sqlalchemy import func, insert, literal, null, select, union_all
from sqlalchemy.orm import Session

from .tablas import auditoria as tabla_auditoria
from .tablas import tarea_transicion as tabla_transicion
from .tablas import usuario as tabla_usuario

# Estados oficiales (CONTRATO_COMUN.md §2). Una transición solo se acepta con
# estados de esta lista, para que el historial no guarde nombres inventados.
ESTADOS_TAREA = frozenset({"draft", "assigned", "in_progress", "submitted",
                           "under_review", "returned", "approved", "closed",
                           "cancelled"})
ESTADOS_PROGRAMA = frozenset({"draft", "submitted", "under_review", "returned",
                              "approved", "authorized", "superseded"})
# Las entidades son los nombres de tabla del G1, igual que en sus triggers.
ESTADOS_POR_ENTIDAD: dict[str, frozenset[str]] = {
    "tarea": ESTADOS_TAREA,
    "tarea_destinatario": ESTADOS_TAREA,
    "programa_version": ESTADOS_PROGRAMA,
}

ACCION_TRANSICION = "transition"
ACCION_MAXIMA = 20   # auditoria.accion es VARCHAR(20)
ENTIDAD_MAXIMA = 64  # auditoria.tabla es VARCHAR(64)
COMENTARIO_MAXIMO = 1000
_CLAVES_TRANSICION = ("estado_anterior", "estado_nuevo", "comentario")
# De dónde sale cada registro de la consulta.
ORIGEN_AUDITORIA = "audit"
ORIGEN_HISTORIAL = "assignment_history"
ENTIDAD_HISTORIAL = "tarea_destinatario"


def _iso(valor: Any) -> str | None:
    if valor is None:
        return None
    return valor.replace(microsecond=0).isoformat() + "Z"


# Claves que nunca se muestran aunque algún módulo las guarde en el detalle (G6-20).
_CLAVES_SECRETAS = ("contrasena", "password", "hash", "token", "secret", "clave")


def _sin_secretos(valor: Any) -> Any:
    if isinstance(valor, dict):
        return {k: "***" if any(s in str(k).lower() for s in _CLAVES_SECRETAS)
                and not isinstance(v, bool) else _sin_secretos(v)
                for k, v in valor.items()}
    if isinstance(valor, list):
        return [_sin_secretos(v) for v in valor]
    return valor


def como_dict(fila: Any) -> dict[str, Any]:
    """Fila de la tabla auditoria del G1 (o de tarea_transicion) → JSON de la API.

    Sirve igual para lo que registra el G6, para lo que registran los
    triggers del G1 (tarea, programa_version, usuario) y el login del G2, y
    para el historial de asignaciones del G3, que llega con sus estados en
    columnas propias en lugar de dentro de detalle.
    """
    origen = getattr(fila, "origen", ORIGEN_AUDITORIA)
    if origen == ORIGEN_HISTORIAL:
        tabla, accion, registro_id = (ENTIDAD_HISTORIAL, ACCION_TRANSICION,
                                      fila.tarea_destinatario_id)
        detalle_historial = {"estado_anterior": fila.estado_anterior,
                             "estado_nuevo": fila.estado_nuevo,
                             "comentario": fila.comentario}
    else:
        tabla, accion, registro_id = fila.tabla, fila.accion, fila.registro_id
    try:
        detalle = json.loads(fila.detalle) if fila.detalle else {}
    except ValueError:
        detalle = {"texto": fila.detalle}
    if not isinstance(detalle, dict):
        detalle = {"valor": detalle}
    if origen == ORIGEN_HISTORIAL:
        detalle = detalle_historial
    detalle = _sin_secretos(detalle)
    # correo, nombres y apellidos solo vienen cuando la consulta une con usuario.
    nombre = " ".join(p for p in (getattr(fila, "nombres", None),
                                  getattr(fila, "apellidos", None)) if p)
    return {"id": fila.id, "source": origen, "actor_id": fila.actor_id,
            "actor_email": getattr(fila, "correo", None), "actor_name": nombre or None,
            "action": accion,
            "entity": tabla,
            "entity_id": int(registro_id) if str(registro_id).isdigit() else registro_id,
            "created_at": _iso(fila.creado_en),
            "from_state": detalle.get("estado_anterior"),
            "to_state": detalle.get("estado_nuevo"),
            "comment": detalle.get("comentario"),
            "changes": {k: v for k, v in detalle.items() if k not in _CLAVES_TRANSICION}}


class RepositorioAuditoria:
    """Agrega y consulta la tabla `auditoria` del G1.

    Solo tiene agregar y consultar a propósito: el G1 además bloquea UPDATE y
    DELETE sobre la tabla con triggers. agregar no hace commit: lo hace quien
    abrió la operación, para que el cambio y su auditoría queden juntos.
    """

    def __init__(self, sesion: Session) -> None:
        self.sesion = sesion

    def agregar(self, *, actor_id: int, accion: str, entidad: str, entidad_id: int,
                detalle: dict[str, Any]) -> dict[str, Any]:
        ahora = datetime.now(timezone.utc).replace(tzinfo=None)
        resultado = self.sesion.execute(insert(tabla_auditoria).values(
            tabla=entidad, registro_id=str(entidad_id), accion=accion,
            actor_id=actor_id, detalle=json.dumps(detalle, ensure_ascii=False),
            creado_en=ahora))
        fila = self.sesion.execute(select(tabla_auditoria).where(
            tabla_auditoria.c.id == resultado.inserted_primary_key[0])).one()
        return como_dict(fila)

    def consultar(self, *, actor_id: int | None, desde: date | None, hasta: date | None,
                  entidad: str | None, accion: str | None,
                  pagina: int, por_pagina: int) -> tuple[int, list[dict[str, Any]]]:
        consulta = self._registros(actor_id=actor_id, desde=desde, hasta=hasta,
                                   entidad=entidad, accion=accion).subquery()
        total = self.sesion.execute(
            select(func.count()).select_from(consulta)).scalar_one()
        u = tabla_usuario
        filas = self.sesion.execute(
            select(consulta, u.c.correo, u.c.nombres, u.c.apellidos)
            .outerjoin(u, u.c.id == consulta.c.actor_id)
            .order_by(consulta.c.creado_en.desc(), consulta.c.origen, consulta.c.id.desc())
            .limit(por_pagina).offset((pagina - 1) * por_pagina))
        return total, [como_dict(f) for f in filas]

    def _registros(self, *, actor_id: int | None = None, desde: date | None = None,
                   hasta: date | None = None, entidad: str | None = None,
                   accion: str | None = None):
        """La tabla auditoria y el historial del G3, con los mismos filtros.

        Cada lado trae sus propias columnas y deja en NULL las del otro: unir
        textos de las dos tablas en una misma columna falla en MySQL si sus
        collations no coinciden. La entidad y la acción del historial las pone
        como_dict.
        """
        t, h = tabla_auditoria, tabla_transicion
        de_auditoria = select(
            literal(ORIGEN_AUDITORIA).label("origen"), t.c.id, t.c.actor_id, t.c.creado_en,
            t.c.tabla, t.c.registro_id, t.c.accion, t.c.detalle,
            null().label("tarea_destinatario_id"), null().label("estado_anterior"),
            null().label("estado_nuevo"), null().label("comentario"))
        de_historial = select(
            literal(ORIGEN_HISTORIAL).label("origen"), h.c.id, h.c.actor_id, h.c.creado_en,
            null().label("tabla"), null().label("registro_id"), null().label("accion"),
            null().label("detalle"), h.c.tarea_destinatario_id, h.c.estado_anterior,
            h.c.estado_nuevo, h.c.comentario)
        if actor_id is not None:
            de_auditoria = de_auditoria.where(t.c.actor_id == actor_id)
            de_historial = de_historial.where(h.c.actor_id == actor_id)
        if desde:
            inicio = datetime.combine(desde, datetime.min.time())
            de_auditoria = de_auditoria.where(t.c.creado_en >= inicio)
            de_historial = de_historial.where(h.c.creado_en >= inicio)
        if hasta:
            fin = datetime.combine(hasta + timedelta(days=1), datetime.min.time())
            de_auditoria = de_auditoria.where(t.c.creado_en < fin)
            de_historial = de_historial.where(h.c.creado_en < fin)
        if entidad:
            de_auditoria = de_auditoria.where(t.c.tabla == entidad)
        if accion:
            de_auditoria = de_auditoria.where(t.c.accion == accion)
        partes = [de_auditoria]
        if self._incluye_historial(entidad, accion):
            partes.append(de_historial)
        return union_all(*partes)

    @staticmethod
    def _incluye_historial(entidad: str | None, accion: str | None) -> bool:
        return entidad in (None, "", ENTIDAD_HISTORIAL) and accion in (None, "", ACCION_TRANSICION)

    def opciones(self) -> dict[str, list[Any]]:
        """Valores que existen en la auditoría, para llenar los filtros."""
        t, h, u = tabla_auditoria, tabla_transicion, tabla_usuario
        entidades = set(self.sesion.execute(select(t.c.tabla).distinct()).scalars())
        acciones = set(self.sesion.execute(select(t.c.accion).distinct()).scalars())
        if self.sesion.execute(select(h.c.id).limit(1)).first() is not None:
            entidades.add(ENTIDAD_HISTORIAL)
            acciones.add(ACCION_TRANSICION)
        r = self._registros().subquery()
        actores = self.sesion.execute(
            select(r.c.actor_id, u.c.correo).distinct()
            .outerjoin(u, u.c.id == r.c.actor_id)
            .where(r.c.actor_id.is_not(None)).order_by(r.c.actor_id))
        return {"entities": sorted(entidades), "actions": sorted(acciones),
                "users": [{"id": i, "email": c} for i, c in actores]}


def _error_de_campo(campo: str, codigo: str, mensaje: str) -> dict[str, str]:
    # Misma forma que usa el G2 para el detalle de un 422.
    return {"field": campo, "code": codigo, "message": mensaje}


def _es_entero_positivo(valor: Any) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool) and valor > 0


def _texto(valor: Any, maximo: int) -> bool:
    return isinstance(valor, str) and bool(valor.strip()) and len(valor.strip()) <= maximo


def _fallar_si_hay(errores: list[dict[str, str]]) -> None:
    if errores:
        raise api_error(422, ErrorCode.VALIDATION_ERROR,
                        "Revisa los campos marcados.", errores)


class ServicioAuditoria:
    def __init__(self, repositorio: RepositorioAuditoria) -> None:
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
            entidad_id=entidad_id, detalle=dict(cambios or {}))

    def registrar_transicion(self, *, actor_id: Any, entidad: Any, entidad_id: Any,
                             estado_anterior: Any, estado_nuevo: Any,
                             comentario: Any = "") -> dict[str, Any]:
        """Registra un cambio de estado con lo que pide el contrato común (G6-15).

        El G3 y el G5 la llaman con la misma sesión que cambia el estado y
        hacen un solo commit, para que no quede una transición sin su registro.
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
            entidad_id=entidad_id, detalle={"estado_anterior": estado_anterior,
                                            "estado_nuevo": estado_nuevo,
                                            "comentario": comentario.strip()})

    @staticmethod
    def _validar_basico(actor_id: Any, accion: Any, entidad: Any,
                        entidad_id: Any) -> list[dict[str, str]]:
        errores: list[dict[str, str]] = []
        if not _es_entero_positivo(actor_id):
            errores.append(_error_de_campo("actor_id", "INVALID",
                                           "Debe ser el id del usuario que hizo la acción."))
        if not _texto(accion, ACCION_MAXIMA):
            errores.append(_error_de_campo("action", "REQUIRED", "Campo obligatorio."))
        if not _texto(entidad, ENTIDAD_MAXIMA):
            errores.append(_error_de_campo("entity", "REQUIRED", "Campo obligatorio."))
        if not _es_entero_positivo(entidad_id):
            errores.append(_error_de_campo("entity_id", "INVALID",
                                           "Debe ser un número entero positivo."))
        return errores

    def consultar(self, *, actor_id: int | None = None, desde: date | None = None,
                  hasta: date | None = None, entidad: str | None = None,
                  accion: str | None = None, pagina: int = 1,
                  por_pagina: int = 20) -> tuple[int, list[dict[str, Any]]]:
        """Consulta filtrada, de lo más reciente a lo más antiguo (G6-30 a G6-33).

        Las fechas incluyen el día completo, en UTC. Devuelve (total, página).
        """
        if desde and hasta and desde > hasta:
            _fallar_si_hay([_error_de_campo(
                "to", "DATE_RANGE", "Debe ser igual o posterior a la fecha inicial.")])
        return self.repositorio.consultar(
            actor_id=actor_id, desde=desde, hasta=hasta,
            entidad=entidad.strip() if entidad else None,
            accion=accion.strip() if accion else None,
            pagina=pagina, por_pagina=por_pagina)

    def opciones(self) -> dict[str, list[Any]]:
        return self.repositorio.opciones()
