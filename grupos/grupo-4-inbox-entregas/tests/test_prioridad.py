"""Orden del inbox por prioridad, con la columna "orden" del catálogo
prioridad_tarea de G1 (low=1, medium=2, high=3, urgent=4; mayor = más urgente).

La prioridad solo desempata: primero va la fecha límite más cercana."""
from datetime import date

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from g4_inbox import database
from g4_inbox.inbox import Asignacion, ORDEN_PRIORIDAD_POR_DEFECTO, listar_inbox

HOY = date(2026, 11, 2)
MISMO_DIA = date(2026, 11, 10)


def tarea(id, prioridad, vence=MISMO_DIA):
    return Asignacion(id, 1, f"Tarea {id}", "X", "assigned", prioridad, vence)


def ids(resultado):
    return [item["id"] for item in resultado["data"]]


def test_a_igual_fecha_va_primero_la_mas_urgente():
    tareas = [tarea(1, "low"), tarea(2, "urgent"), tarea(3, "medium"), tarea(4, "high")]
    assert ids(listar_inbox(tareas, 1, hoy=HOY)) == [2, 4, 3, 1]


def test_la_fecha_pesa_mas_que_la_prioridad():
    tareas = [tarea(1, "urgent", date(2026, 12, 1)), tarea(2, "low", date(2026, 11, 5))]
    assert ids(listar_inbox(tareas, 1, hoy=HOY)) == [2, 1]


def test_usa_el_orden_del_catalogo_que_le_pasan():
    # Si G1 cambiara los números del catálogo, el inbox los sigue.
    invertido = {"urgent": 1, "high": 2, "medium": 3, "low": 4}
    tareas = [tarea(1, "low"), tarea(2, "urgent")]
    assert ids(listar_inbox(tareas, 1, hoy=HOY, orden_prioridad=invertido)) == [1, 2]


def test_prioridad_que_el_catalogo_no_conoce_queda_al_final():
    tareas = [tarea(1, "inventada"), tarea(2, "low")]
    assert ids(listar_inbox(tareas, 1, hoy=HOY)) == [2, 1]


def test_la_copia_por_defecto_es_la_del_catalogo_de_g1():
    assert ORDEN_PRIORIDAD_POR_DEFECTO == {"low": 1, "medium": 2, "high": 3, "urgent": 4}


# ---------- lectura del catálogo (con una base SQLite en memoria) ----------

@pytest.fixture
def base_en_memoria(monkeypatch):
    motor = create_engine("sqlite://", poolclass=StaticPool)
    monkeypatch.setattr(database, "SessionLocal", sessionmaker(bind=motor))
    return motor


def test_fetch_orden_prioridades_lee_solo_las_activas(base_en_memoria):
    with base_en_memoria.begin() as con:
        con.execute(text("CREATE TABLE prioridad_tarea (codigo TEXT, nombre TEXT, orden INTEGER, activo INTEGER)"))
        con.execute(text(
            "INSERT INTO prioridad_tarea VALUES "
            "('low','Baja',1,1), ('medium','Media',2,1), ('high','Alta',3,1), "
            "('urgent','Urgente',4,1), ('vieja','Vieja',9,0)"))
    assert database.fetch_orden_prioridades() == {"low": 1, "medium": 2, "high": 3, "urgent": 4}


def test_si_el_catalogo_no_existe_devuelve_vacio_y_el_inbox_sigue(base_en_memoria):
    # Una base de la versión anterior no tiene la tabla: no debe tumbar el inbox.
    assert database.fetch_orden_prioridades() == {}
    tareas = [tarea(1, "low"), tarea(2, "urgent")]
    assert ids(listar_inbox(tareas, 1, hoy=HOY, orden_prioridad={})) == [2, 1]
