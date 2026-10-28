from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable

from fastapi import Query
from sqlalchemy.orm import Query as SAQuery


# --- Maximo de per_page -----------------------------------------------------

def _max_per_page() -> int:
    try:
        from g2_api.config import settings 

        valor = getattr(settings, "PER_PAGE_MAX", None)
        if valor is not None:
            return int(valor)
    except Exception:  
        pass
    try:
        return int(os.getenv("PER_PAGE_MAX", "100"))
    except (TypeError, ValueError):
        return 100


PER_PAGE_MAX: int = _max_per_page()
PER_PAGE_DEFECTO: int = 20


# --- Dependencia de FastAPI -------------------------------------------------

@dataclass(frozen=True)
class Paginacion:
    page: int
    per_page: int


def params_paginacion(
    page: int = Query(1, ge=1, description="Página (empieza en 1)."),
    per_page: int = Query(
        PER_PAGE_DEFECTO,
        ge=1,
        le=PER_PAGE_MAX,
        description=f"Elementos por página (máximo {PER_PAGE_MAX}).",
    ),
) -> Paginacion:
    """

    `page` y `per_page` invalidos -> 422 .
    """
    return Paginacion(page=page, per_page=per_page)


# --- Envoltura de resultado -------------------------------------------------

def paginar(
    query: SAQuery,
    page: int,
    per_page: int,
    serializador: Callable[[Any], Any] | None = None,
) -> dict[str, Any]:
    
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 1
    if per_page > PER_PAGE_MAX:
        per_page = PER_PAGE_MAX

    total = int(query.count())
    offset = (page - 1) * per_page
    filas = query.offset(offset).limit(per_page).all()

    if serializador is not None:
        data = [serializador(f) for f in filas]
    else:
        data = list(filas)

    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "data": data,
    }
