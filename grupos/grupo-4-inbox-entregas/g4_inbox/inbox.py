"""Lógica del inbox del docente (GET /inbox y GET /inbox/summary).


"""
import unicodedata
from dataclasses import asdict, dataclass
from datetime import date

ESTADOS = (
    "draft", "assigned", "in_progress", "submitted", "under_review",
    "returned", "approved", "closed", "cancelled",
)
# `draft` existe solo a nivel de tarea y NUNCA aparece en el inbox (G3, regla dura).
ESTADOS_INBOX = tuple(e for e in ESTADOS if e != "draft")
# Estados en los que el docente todavía tiene que hacer algo: solo en estos
# importa el vencimiento.
ESTADOS_PENDIENTES = ("assigned", "in_progress", "returned")
ORDEN_PRIORIDAD = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
DIAS_POR_VENCER = 3

PER_PAGE_POR_DEFECTO = 20
# Provisional: el máximo oficial lo documenta el G2 en el OpenAPI.
PER_PAGE_MAXIMO = 100


class ErrorValidacion(ValueError):
    """Parámetros inválidos. El endpoint lo traduce a 422 con `details` por campo."""

    def __init__(self, details):
        super().__init__("Parámetros inválidos")
        self.details = details


@dataclass(frozen=True)
class Asignacion:
    id: int
    assignee_id: int
    title: str
    task_type: str
    status: str
    priority: str
    due_at: date | None = None

    def to_dict(self):
        datos = asdict(self)
        datos["due_at"] = self.due_at.isoformat() if self.due_at else None
        return datos


def normalizar(texto):
    """Minúsculas y sin acentos, para que "programacion" encuentre "Programación"."""
    sin_acentos = unicodedata.normalize("NFD", str(texto or ""))
    return "".join(c for c in sin_acentos if not unicodedata.combining(c)).lower().strip()


def dias_restantes(asignacion, hoy):
    """Días hasta el vencimiento (negativo = ya pasó); None si no hay fecha."""
    if asignacion.due_at is None:
        return None
    return (asignacion.due_at - hoy).days


def situacion_vencimiento(asignacion, hoy):
    """"vencida", "por-vencer" o "" (también "" si ya no está pendiente)."""
    if asignacion.status not in ESTADOS_PENDIENTES:
        return ""
    dias = dias_restantes(asignacion, hoy)
    if dias is None:
        return ""
    if dias < 0:
        return "vencida"
    if dias <= DIAS_POR_VENCER:
        return "por-vencer"
    return ""


def visibles_para(asignaciones, usuario_id):
    """Reglas duras: solo lo del usuario autenticado y nunca borradores."""
    return [a for a in asignaciones
            if a.assignee_id == usuario_id and a.status in ESTADOS_INBOX]


def _clave_orden(asignacion, hoy):
    # Fecha más cercana primero, sin fecha al final; empate: más urgente primero.
    dias = dias_restantes(asignacion, hoy)
    return (
        dias is None,
        dias if dias is not None else 0,
        ORDEN_PRIORIDAD.get(asignacion.priority, 99),
        asignacion.id,
    )


def _validar(status, page, per_page):
    errores = {}
    if status is not None and status not in ESTADOS_INBOX:
        errores["status"] = f"Estado desconocido: {status!r}"
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        errores["page"] = "Debe ser un entero mayor o igual a 1"
    if (not isinstance(per_page, int) or isinstance(per_page, bool)
            or not 1 <= per_page <= PER_PAGE_MAXIMO):
        errores["per_page"] = f"Debe ser un entero entre 1 y {PER_PAGE_MAXIMO}"
    if errores:
        raise ErrorValidacion(errores)


def listar_inbox(asignaciones, usuario_id, *, q="", status=None,
                 page=1, per_page=PER_PAGE_POR_DEFECTO, hoy=None):
    """GET /inbox: respuesta paginada {page, per_page, total, data}."""
    _validar(status, page, per_page)
    hoy = hoy or date.today()

    texto = normalizar(q)
    filtradas = [
        a for a in visibles_para(asignaciones, usuario_id)
        if texto in normalizar(a.title) and (status is None or a.status == status)
    ]
    filtradas.sort(key=lambda a: _clave_orden(a, hoy))

    inicio = (page - 1) * per_page
    pagina = filtradas[inicio:inicio + per_page]
    data = []
    for a in pagina:
        item = a.to_dict()
        item["due_state"] = situacion_vencimiento(a, hoy)
        data.append(item)
    return {"page": page, "per_page": per_page, "total": len(filtradas), "data": data}


def resumen_inbox(asignaciones, usuario_id, *, hoy=None):
    """GET /inbox/summary: contadores por estado y por vencimiento."""
    hoy = hoy or date.today()
    propias = visibles_para(asignaciones, usuario_id)
    por_estado = {estado: 0 for estado in ESTADOS_INBOX}
    vencidas = por_vencer = 0
    for a in propias:
        por_estado[a.status] += 1
        situacion = situacion_vencimiento(a, hoy)
        vencidas += situacion == "vencida"
        por_vencer += situacion == "por-vencer"
    return {
        "total": len(propias),
        "pending": sum(por_estado[e] for e in ESTADOS_PENDIENTES),
        "overdue": vencidas,
        "due_soon": por_vencer,
        "by_status": por_estado,
    }
