"""Rutas HTTP del G6. El main.py de la raíz monta `router` (README §4).

Todo lo de seguridad viene del G2 y se importa desde g2_api, no se copia:
- quién es el usuario: middleware de autenticación del G2;
- quién puede agregar o modificar: requerir_rol del G2 con el rol de administración;
- formato de error y paginación: servicios compartidos del G2.
"""

import os
import time
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, Query, Response
from pydantic import BaseModel, ConfigDict, Field

from g2_api.middleware.auth_middleware import obtener_usuario_actual, requerir_rol
from g2_api.utils.paginacion import Paginacion, params_paginacion

from . import __version__
from .auditoria import RepositorioAuditoriaEnMemoria, ServicioAuditoria
from .catalogos import CATALOGOS, Catalogo, RepositorioEnMemoria, ServicioCatalogos
from .notificaciones import RepositorioNotificacionesEnMemoria, ServicioNotificaciones
from .salud import estado_del_servicio

# Código del rol en la tabla `rol` del G1 (semilla: admin, teacher, ...).
ROLES_ADMINISTRACION = ["admin"]

_INICIADO_EN = time.monotonic()
_auditoria = ServicioAuditoria(RepositorioAuditoriaEnMemoria())
_servicio = ServicioCatalogos(RepositorioEnMemoria(), _auditoria)
_notificaciones = ServicioNotificaciones(RepositorioNotificacionesEnMemoria())


def obtener_servicio() -> ServicioCatalogos:
    return _servicio


def obtener_auditoria() -> ServicioAuditoria:
    """El G3 y el G5 registran sus transiciones con obtener_auditoria().registrar_transicion(...)."""
    return _auditoria


def obtener_notificaciones() -> ServicioNotificaciones:
    """Los grupos 3, 4 y 5 entregan sus eventos con obtener_notificaciones().procesar_evento(...)."""
    return _notificaciones


def _id_del_usuario(usuario: Any) -> int | None:
    # El G2 hoy entrega un diccionario; si pasa a un objeto, también sirve.
    if isinstance(usuario, dict):
        return usuario.get("id")
    return getattr(usuario, "id", None)


Servicio = Annotated[ServicioCatalogos, Depends(obtener_servicio)]
Auditoria = Annotated[ServicioAuditoria, Depends(obtener_auditoria)]
Notificaciones = Annotated[ServicioNotificaciones, Depends(obtener_notificaciones)]
UsuarioConSesion = Annotated[Any, Depends(obtener_usuario_actual)]
Administracion = Annotated[Any, Depends(requerir_rol(ROLES_ADMINISTRACION))]

# ── Esquemas para el OpenAPI ────────────────────────────────────────────────


class RegistroNuevo(BaseModel):
    """Las reglas completas se validan en catalogos.validar_registro."""

    model_config = ConfigDict(extra="forbid")

    code: str | None = Field(
        None, examples=["CENTRAL"],
        description="Obligatorio. De 2 a 20 caracteres: letras, números, guion "
                    "o guion bajo. Se guarda en mayúsculas.")
    name: str | None = Field(
        None, examples=["Campus Central"],
        description="Obligatorio. De 2 a 120 caracteres.")
    is_active: bool | None = Field(
        None, description="Opcional. Si se omite, el registro queda activo.")


class CambioRegistro(BaseModel):
    """Solo los campos que se envían cambian. Las reglas son las de RegistroNuevo."""
    model_config = ConfigDict(extra="forbid")

    code: str | None = Field(None, examples=["CENTRAL"])
    name: str | None = Field(None, examples=["Campus Central"])
    is_active: bool | None = Field(None, examples=[False])


class RegistroSalida(BaseModel):
    id: int
    code: str
    name: str
    is_active: bool
    created_at: str


class PaginaRegistros(BaseModel):
    page: int
    per_page: int
    total: int
    data: list[RegistroSalida]


class NotificacionSalida(BaseModel):
    id: int
    event: str
    message: str
    is_read: bool
    created_at: str
    read_at: str | None


class PaginaNotificaciones(BaseModel):
    page: int
    per_page: int
    total: int
    data: list[NotificacionSalida]


class RegistroAuditoriaSalida(BaseModel):
    id: int
    actor_id: int
    action: str
    entity: str
    entity_id: int
    created_at: str
    from_state: str | None
    to_state: str | None
    comment: str | None
    changes: dict[str, Any]


class PaginaAuditoria(BaseModel):
    page: int
    per_page: int
    total: int
    data: list[RegistroAuditoriaSalida]


class EstadoSalud(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    time: str
    uptime_seconds: int
    checks: dict[str, str]


_ERRORES = {401: "Sin sesión", 403: "Sin permiso", 404: "No existe",
            409: "El código ya existe",
            422: "Error de validación con detalle por campo"}


def _errores(*codigos: int) -> dict[int | str, dict[str, Any]]:
    return {c: {"description": _ERRORES[c]} for c in codigos}


# ── Rutas ───────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/api/v1")


@router.get("/health", tags=["Salud"], summary="Estado técnico del servicio",
            response_model=EstadoSalud,
            responses={503: {"model": EstadoSalud,
                             "description": "Alguna verificación falló"}})
def health(response: Response) -> dict[str, Any]:
    estado = estado_del_servicio(
        iniciado_en=_INICIADO_EN,
        entorno=os.getenv("APP_ENV", "desarrollo"),
        version=os.getenv("APP_VERSION", __version__),
    )
    response.headers["Cache-Control"] = "no-store"
    if estado["status"] != "ok":
        response.status_code = 503
    return estado


def _pagina(elementos: list[dict[str, Any]], paginacion: Paginacion) -> dict[str, Any]:
    # PENDIENTE: con las tablas del G1 esto se cambia por
    # g2_api.utils.paginacion.paginar(consulta, page, per_page).
    inicio = (paginacion.page - 1) * paginacion.per_page
    return {"page": paginacion.page, "per_page": paginacion.per_page,
            "total": len(elementos),
            "data": elementos[inicio:inicio + paginacion.per_page]}


def _registrar_catalogo(catalogo: Catalogo) -> None:
    ruta = f"/{catalogo.recurso}"
    sufijo = catalogo.recurso.replace("-", "_")

    @router.get(ruta, tags=["Catálogos"], response_model=PaginaRegistros,
                summary=f"Listar {catalogo.nombre}",
                operation_id=f"listar_{sufijo}", responses=_errores(401, 422))
    def listar(
        servicio: Servicio,
        _usuario: UsuarioConSesion,
        paginacion: Annotated[Paginacion, Depends(params_paginacion)],
        q: Annotated[str | None, Query(
            max_length=120, description="Busca en código y nombre")] = None,
        active: Annotated[bool | None, Query(
            description="Filtra por activos (true) o inactivos (false)")] = None,
    ) -> dict[str, Any]:
        return _pagina(servicio.listar(catalogo.recurso, q=q, activo=active), paginacion)

    @router.post(ruta, tags=["Catálogos"], response_model=RegistroSalida,
                 status_code=201,
                 summary=f"Agregar a {catalogo.nombre} (solo administración)",
                 operation_id=f"crear_{sufijo}",
                 responses=_errores(401, 403, 409, 422))
    def crear(datos: RegistroNuevo, servicio: Servicio,
              usuario: Administracion) -> dict[str, Any]:
        return servicio.crear(catalogo.recurso,
                              datos.model_dump(exclude_unset=True),
                              _id_del_usuario(usuario))

    @router.patch(f"{ruta}/{{registro_id}}", tags=["Catálogos"],
                  response_model=RegistroSalida,
                  summary=f"Modificar en {catalogo.nombre} (solo administración)",
                  operation_id=f"modificar_{sufijo}",
                  responses=_errores(401, 403, 404, 409, 422))
    def modificar(registro_id: Annotated[int, Path(ge=1)], datos: CambioRegistro,
                  servicio: Servicio, usuario: Administracion) -> dict[str, Any]:
        return servicio.modificar(catalogo.recurso, registro_id,
                                  datos.model_dump(exclude_unset=True),
                                  _id_del_usuario(usuario))


for _catalogo in CATALOGOS.values():
    _registrar_catalogo(_catalogo)


# ── Notificaciones (G6-04 a G6-13) ──────────────────────────────────────────


@router.get("/notifications", tags=["Notificaciones"],
            response_model=PaginaNotificaciones,
            summary="Listar mis notificaciones (las más recientes primero)",
            responses=_errores(401, 422))
def listar_notificaciones(
    servicio: Notificaciones,
    usuario: UsuarioConSesion,
    paginacion: Annotated[Paginacion, Depends(params_paginacion)],
    unread: Annotated[bool, Query(
        description="true muestra solo las que no se han leído")] = False,
) -> dict[str, Any]:
    return _pagina(servicio.listar(_id_del_usuario(usuario), no_leidas=unread), paginacion)


@router.patch("/notifications/{notificacion_id}/read", tags=["Notificaciones"],
              response_model=NotificacionSalida,
              summary="Marcar como leída una notificación propia",
              responses=_errores(401, 404, 422))
def marcar_notificacion_leida(
    notificacion_id: Annotated[int, Path(ge=1)],
    servicio: Notificaciones,
    usuario: UsuarioConSesion,
) -> dict[str, Any]:
    return servicio.marcar_leida(_id_del_usuario(usuario), notificacion_id)


# ── Auditoría (G6-14, G6-15 y G6-30 a G6-33) ────────────────────────────────


@router.get("/audit", tags=["Auditoría"], response_model=PaginaAuditoria,
            summary="Consultar la auditoría (solo administración)",
            responses=_errores(401, 403, 422))
def consultar_auditoria(
    servicio: Auditoria,
    _usuario: Administracion,
    paginacion: Annotated[Paginacion, Depends(params_paginacion)],
    user_id: Annotated[int | None, Query(ge=1, description="Quién hizo la acción")] = None,
    from_: Annotated[date | None, Query(alias="from",
                                        description="Desde este día (AAAA-MM-DD, UTC)")] = None,
    to: Annotated[date | None, Query(description="Hasta este día, incluido")] = None,
    entity: Annotated[str | None, Query(
        max_length=120, description="Por ejemplo campuses, assignment o program_version")] = None,
    action: Annotated[str | None, Query(
        max_length=120, description="Por ejemplo create, update o transition")] = None,
) -> dict[str, Any]:
    registros = servicio.consultar(actor_id=user_id, desde=from_, hasta=to,
                                   entidad=entity, accion=action)
    return _pagina(registros, paginacion)
