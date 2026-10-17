"""Rutas HTTP del G6. El main.py de la raíz monta `router` (README §4).

Todo lo de seguridad viene del G2 y se importa desde g2_api, no se copia:
- quién es el usuario: middleware de autenticación del G2;
- quién puede agregar: requerir_rol del G2 con el rol de administración;
- formato de error y paginación: servicios compartidos del G2.
"""

import os
import time
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, ConfigDict, Field

from g2_api.middleware.auth_middleware import obtener_usuario_actual, requerir_rol
from g2_api.utils.paginacion import Paginacion, params_paginacion

from . import __version__
from .catalogos import CATALOGOS, Catalogo, RepositorioEnMemoria, ServicioCatalogos
from .salud import estado_del_servicio

# Código del rol en la tabla `rol` del G1 (semilla: admin, teacher, ...).
ROLES_ADMINISTRACION = ["admin"]

_INICIADO_EN = time.monotonic()
_servicio = ServicioCatalogos(RepositorioEnMemoria())


def obtener_servicio() -> ServicioCatalogos:
    return _servicio


def _id_del_usuario(usuario: Any) -> int | None:
    # El G2 hoy entrega un diccionario; si pasa a un objeto, también sirve.
    if isinstance(usuario, dict):
        return usuario.get("id")
    return getattr(usuario, "id", None)


Servicio = Annotated[ServicioCatalogos, Depends(obtener_servicio)]
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


class EstadoSalud(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    time: str
    uptime_seconds: int
    checks: dict[str, str]


_ERRORES = {401: "Sin sesión", 403: "Sin permiso", 409: "El código ya existe",
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
        registros = servicio.listar(catalogo.recurso, q=q, activo=active)
        # PENDIENTE: con las tablas del G1 esto se cambia por
        # g2_api.utils.paginacion.paginar(consulta, page, per_page).
        inicio = (paginacion.page - 1) * paginacion.per_page
        return {"page": paginacion.page, "per_page": paginacion.per_page,
                "total": len(registros),
                "data": registros[inicio:inicio + paginacion.per_page]}

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


for _catalogo in CATALOGOS.values():
    _registrar_catalogo(_catalogo)
