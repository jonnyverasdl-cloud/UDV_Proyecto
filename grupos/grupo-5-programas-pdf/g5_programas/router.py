"""Rutas de la API para trabajar con programas de curso y sus versiones.

Cada ruta comprueba quién está haciendo la solicitud y deja el trabajo de la
base de datos al repositorio. Todas empiezan con ``/api/v1``.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from .auth import Actor, authenticated_actor, require_role
from .database import get_session
from .domain import ACTOR_ROLES
from .errors import ApiError
from . import repository

router = APIRouter(prefix="/api/v1", tags=["Programas de curso"])
DbSession = Annotated[Session, Depends(get_session)]
CurrentActor = Annotated[Actor, Depends(authenticated_actor)]


# Revisión del formato de los datos que llegan a la API.
def _body_object(body):
    """Confirma que el cuerpo de la solicitud sea un objeto JSON."""
    if not isinstance(body, dict):
        raise ApiError(422, "VALIDATION_ERROR", "El cuerpo debe ser un objeto JSON.", {"body": "Se requiere un objeto."})
    return body


# Rutas para consultar y crear programas y versiones.
@router.get("/course-programs")
def list_course_programs(
    session: DbSession,
    actor: CurrentActor,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """Muestra los programas por páginas."""
    return repository.list_programs(session, page, per_page)


@router.post("/course-programs", status_code=201)
def post_course_program(body: dict, session: DbSession, actor: CurrentActor):
    """Crea un programa con su primer borrador; lo puede hacer un autor."""
    require_role(actor, "author")
    return repository.create_program(session, actor, _body_object(body))


@router.get("/course-programs/{program_id}")
def course_program(program_id: int, session: DbSession, actor: CurrentActor):
    """Muestra los datos del programa y sus versiones anteriores."""
    return repository.get_program(session, program_id)


@router.post("/course-programs/{program_id}/versions", status_code=201)
def post_version(program_id: int, body: dict, session: DbSession, actor: CurrentActor):
    """Abre otra versión copiando una autorizada; lo puede hacer coordinación."""
    require_role(actor, "coordinator")
    return repository.create_version(session, actor, program_id, _body_object(body))


@router.get("/program-versions/{version_id}")
def read_version(version_id: int, session: DbSession, actor: CurrentActor):
    """Muestra los datos de una versión y todo su contenido."""
    return repository.get_version(session, version_id)


@router.put("/program-versions/{version_id}")
def put_version(version_id: int, body: dict, session: DbSession, actor: CurrentActor):
    """Guarda cambios en una versión que todavía se puede editar."""
    require_role(actor, "author")
    return {"ok": True, "version": repository.update_version(
        session, actor, version_id, _body_object(body)
    )}


@router.put("/program-versions/{version_id}/sections/{section}")
def put_section(version_id: int, section: str, body: dict, session: DbSession, actor: CurrentActor):
    """Guarda una sección sin tocar las demás."""
    require_role(actor, "author")
    return {"ok": True, "version": repository.update_version(
        session, actor, version_id, _body_object(body), section
    )}


# Acciones para enviar, revisar, devolver, aprobar y autorizar una versión.
def _transition(action: str):
    """Prepara una ruta para la acción indicada y su rol correspondiente."""
    def endpoint(version_id: int, session: DbSession, actor: CurrentActor, body: dict | None = None):
        """Realiza la acción y devuelve la versión con su estado actualizado."""
        require_role(actor, ACTOR_ROLES[action])
        payload = _body_object(body or {})
        comment = payload.get("comentario", payload.get("observacion"))
        version = repository.transition(session, actor, version_id, action, comment)
        return {"ok": True, "version": version}

    endpoint.__name__ = f"post_{action}"
    return endpoint


router.add_api_route("/program-versions/{version_id}/submit", _transition("submit"), methods=["POST"])
router.add_api_route("/program-versions/{version_id}/review", _transition("review"), methods=["POST"])
router.add_api_route("/program-versions/{version_id}/return", _transition("return"), methods=["POST"])
router.add_api_route("/program-versions/{version_id}/approve", _transition("approve"), methods=["POST"])
router.add_api_route("/program-versions/{version_id}/authorize", _transition("authorize"), methods=["POST"])


# Rutas para consultar diferencias y bajar el PDF.
@router.get("/program-versions/{version_id}/changes")
def version_changes(version_id: int, session: DbSession, actor: CurrentActor):
    """Muestra las diferencias con la versión anterior del mismo período."""
    return repository.get_changes(session, version_id)


@router.get("/program-versions/{version_id}/pdf")
def version_pdf(version_id: int, session: DbSession, actor: CurrentActor):
    """Genera y descarga el PDF de una versión autorizada."""
    content, digest, program, version = repository.generate_pdf_data(session, version_id, actor)
    repository.record_pdf(session, actor, version_id, content, digest)
    filename = f"programa-{program['id']}-version-{version['numero_version']}.pdf"
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
