"""Flujo de punta a punta con la app completa (G6-04 a G6-16 y G6-18).

Usa el main.py de la raíz, con el login del G2, el workflow del G3 y las rutas
del G6, contra un MySQL con db_udv recién creada por el G1. Recorre una tarea
como lo haría el equipo (crear, publicar, empezar, entregar, revisar,
devolver, reenviar y aprobar) y revisa en cada paso que la notificación le
llegue a quien corresponde y que la auditoría muestre la transición.

    set G6_MYSQL_URL=mysql+pymysql://root:<clave>@127.0.0.1:3306/db_udv
    python -m pytest tests/integracion

Sin G6_MYSQL_URL, o si la rama no tiene el main.py de la raíz con el G3, se
omite. Deja tareas nuevas en la base: úsala solo con una base de pruebas,
nunca la compartida.
"""

import importlib
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

URL = os.getenv("G6_MYSQL_URL")
RAIZ = Path(__file__).resolve().parents[4]
pytestmark = [
    pytest.mark.skipif(not URL, reason="Define G6_MYSQL_URL para probar con MySQL"),
    pytest.mark.skipif(not (RAIZ / "main.py").exists()
                       or not (RAIZ / "grupos" / "grupo-3-workflow-tareas").exists(),
                       reason="Hace falta el main.py de la raíz y el G3"),
]

CONTRASENA_DEMO = "Demo2026!"  # Pública en el README del G1; solo datos de prueba.
COORDINACION, DOCENTE, REVISION, DIRECCION, ADMIN = 2, 3, 5, 6, 1


@pytest.fixture(scope="module")
def cliente():
    from fastapi.testclient import TestClient
    from g2_api.database import get_db
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # El G3 abre su conexión con DATABASE_URL en cada petición; el G2 y el G6
    # usan get_db, que aquí se apunta a la misma base.
    anterior = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = URL
    if str(RAIZ) not in sys.path:
        sys.path.insert(0, str(RAIZ))
    app = importlib.import_module("main").app
    motor = create_engine(URL, pool_pre_ping=True)
    fabrica = sessionmaker(bind=motor)

    def sesion():
        with fabrica() as s:
            yield s

    app.dependency_overrides[get_db] = sesion
    montados = app.openapi()["paths"]
    if "/api/v1/tasks" not in montados or "/api/v1/notifications" not in montados:
        pytest.skip("main.py no monta todavía el G3 y el G6")
    yield TestClient(app)
    app.dependency_overrides.clear()
    motor.dispose()
    if anterior is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = anterior


def entrar(cliente, correo):
    respuesta = cliente.post("/api/v1/auth/login",
                             json={"correo": correo, "password": CONTRASENA_DEMO})
    assert respuesta.status_code == 200, respuesta.text
    return {"Authorization": f"Bearer {respuesta.json()['access_token']}"}


@pytest.fixture(scope="module")
def sesiones(cliente):
    return {quien: entrar(cliente, f"{quien}@demo.udv.edu.gt")
            for quien in ("coordinacion", "docente1", "revisor", "admin", "auditoria", "docente2")}


def avisos(cliente, encabezados, titulo):
    """Notificaciones del usuario que hablan de esta tarea, por evento."""
    respuesta = cliente.get("/api/v1/notifications?per_page=100", headers=encabezados)
    assert respuesta.status_code == 200, respuesta.text
    salida = {}
    for n in respuesta.json()["data"]:
        if titulo in n["message"]:
            salida.setdefault(n["event"], []).append(n)
    return salida


def accion(cliente, encabezados, asignacion, nombre, comentario=None):
    return cliente.post(f"/api/v1/assignments/{asignacion}/actions/{nombre}",
                        json={"comment": comentario}, headers=encabezados)


def publicar(cliente, s, titulo, dias=2):
    # Vence en pocos días para que también salga el aviso de vencimiento (G6-05).
    vence = (datetime.now(timezone.utc) + timedelta(days=dias)).date().isoformat()
    tarea = cliente.post("/api/v1/tasks", headers=s["coordinacion"], json={
        "type_id": 1, "title": titulo, "due_date": vence, "reviewer_id": REVISION})
    assert tarea.status_code == 201, tarea.text
    tarea_id = tarea.json()["id"]
    assert cliente.post(f"/api/v1/tasks/{tarea_id}/recipients", headers=s["coordinacion"],
                        json={"mode": "users", "user_ids": [DOCENTE]}).status_code == 200
    assert cliente.post(f"/api/v1/tasks/{tarea_id}/publish",
                        headers=s["coordinacion"]).status_code == 200
    asignaciones = cliente.get(f"/api/v1/tasks/{tarea_id}/assignments",
                               headers=s["coordinacion"]).json()
    return tarea_id, (asignaciones.get("items") or asignaciones.get("data") or asignaciones)[0]["id"]


def test_flujo_completo_notifica_y_audita_cada_paso(cliente, sesiones):
    s = sesiones
    titulo = f"G6E2E-{uuid.uuid4().hex[:6].upper()}"
    _, asignacion = publicar(cliente, s, titulo)

    # G6-04 y G6-05: al publicar, el docente recibe la tarea y el aviso de vencimiento.
    del_docente = avisos(cliente, s["docente1"], titulo)
    assert len(del_docente["task.published"]) == 1
    assert len(del_docente["assignment.due_soon"]) == 1

    # G6-06: al entregar, le llega al revisor.
    assert accion(cliente, s["docente1"], asignacion, "start").status_code == 200
    assert accion(cliente, s["docente1"], asignacion, "submit").status_code == 200
    assert len(avisos(cliente, s["revisor"], titulo)["assignment.submitted"]) == 1

    # G6-07: al devolver, le llega al docente con la observación.
    assert accion(cliente, s["revisor"], asignacion, "review").status_code == 200
    assert accion(cliente, s["revisor"], asignacion, "return",
                  "Falta la bibliografía.").status_code == 200
    devuelta = avisos(cliente, s["docente1"], titulo)["assignment.returned"]
    assert len(devuelta) == 1 and "Falta la bibliografía." in devuelta[0]["message"]

    # G6-16: el docente reenvía la entrega devuelta y el revisor la vuelve a recibir.
    assert accion(cliente, s["docente1"], asignacion, "resubmit").status_code == 200
    assert len(avisos(cliente, s["revisor"], titulo)["assignment.submitted"]) == 2

    # G6-08: al aprobar, le llega al docente y a coordinación.
    assert accion(cliente, s["revisor"], asignacion, "review").status_code == 200
    assert accion(cliente, s["revisor"], asignacion, "approve").status_code == 200
    assert len(avisos(cliente, s["docente1"], titulo)["assignment.approved"]) == 1
    assert len(avisos(cliente, s["coordinacion"], titulo)["assignment.approved"]) == 1

    # G6-11: consultar otra vez y procesar a mano no duplica nada.
    antes = avisos(cliente, s["docente1"], titulo)
    assert cliente.post("/api/v1/notifications/process", headers=s["admin"]).status_code == 200
    assert avisos(cliente, s["docente1"], titulo) == antes
    # Nadie más recibe avisos de esta tarea.
    assert avisos(cliente, s["docente2"], titulo) == {}

    # G6-15: la auditoría muestra las 8 transiciones de la asignación, con quién las hizo.
    auditoria = cliente.get("/api/v1/audit?action=transition&entity=tarea_destinatario"
                            "&per_page=100", headers=s["auditoria"])
    assert auditoria.status_code == 200, auditoria.text
    pasos = [(r["from_state"], r["to_state"], r["actor_id"]) for r in auditoria.json()["data"]
             if r["entity_id"] == asignacion]
    assert list(reversed(pasos)) == [
        (None, "assigned", COORDINACION), ("assigned", "in_progress", DOCENTE),
        ("in_progress", "submitted", DOCENTE), ("submitted", "under_review", REVISION),
        ("under_review", "returned", REVISION), ("returned", "submitted", DOCENTE),
        ("submitted", "under_review", REVISION), ("under_review", "approved", REVISION)]


def test_marcar_como_leida_solo_afecta_al_dueno(cliente, sesiones):
    s = sesiones
    titulo = f"G6E2E-{uuid.uuid4().hex[:6].upper()}"
    publicar(cliente, s, titulo, dias=20)
    aviso = avisos(cliente, s["docente1"], titulo)["task.published"][0]

    # G6-13: otra persona no puede marcarla (404, como si no existiera).
    ajena = cliente.patch(f"/api/v1/notifications/{aviso['id']}/read", headers=s["docente2"])
    assert ajena.status_code == 404
    assert avisos(cliente, s["docente1"], titulo)["task.published"][0]["is_read"] is False

    # G6-12: el dueño sí, y la marca no se pierde al volver a consultar.
    propia = cliente.patch(f"/api/v1/notifications/{aviso['id']}/read", headers=s["docente1"])
    assert propia.status_code == 200 and propia.json()["is_read"] is True
    assert avisos(cliente, s["docente1"], titulo)["task.published"][0]["is_read"] is True


def test_cancelar_avisa_a_los_destinatarios(cliente, sesiones):
    s = sesiones
    titulo = f"G6E2E-{uuid.uuid4().hex[:6].upper()}"
    tarea_id, _ = publicar(cliente, s, titulo, dias=20)

    # G6-10
    assert cliente.post(f"/api/v1/tasks/{tarea_id}/cancel", headers=s["coordinacion"],
                        json={"reason": "Prueba del G6"}).status_code == 200
    assert len(avisos(cliente, s["docente1"], titulo)["task.cancelled"]) == 1


def test_programa_autorizado_avisa_al_docente_y_a_coordinacion(cliente, sesiones):
    # G6-09: la semilla del G1 autoriza el programa 1, y su trigger deja el evento.
    # Las rutas de programas son del G5; aquí se revisa lo que le toca al G6.
    nombre = "Programación Web - 2026-1"
    for quien in ("docente1", "coordinacion"):
        respuesta = cliente.get("/api/v1/notifications?per_page=100", headers=sesiones[quien])
        eventos = [n["event"] for n in respuesta.json()["data"] if nombre in n["message"]]
        assert eventos.count("program.authorized") == 1, quien


def test_una_accion_rechazada_no_deja_nada_a_medias(cliente, sesiones):
    s = sesiones
    titulo = f"G6E2E-{uuid.uuid4().hex[:6].upper()}"
    _, asignacion = publicar(cliente, s, titulo, dias=20)
    antes = cliente.get(f"/api/v1/assignments/{asignacion}/history",
                        headers=s["coordinacion"]).json()

    # G6-18: aprobar sin revisar es una transición inválida (409) y no toca nada.
    assert accion(cliente, s["revisor"], asignacion, "approve").status_code == 409
    # Un docente no puede devolver (403) y tampoco toca nada.
    assert accion(cliente, s["docente1"], asignacion, "return", "x").status_code == 403

    despues = cliente.get(f"/api/v1/assignments/{asignacion}/history",
                          headers=s["coordinacion"]).json()
    assert despues == antes
    assert set(avisos(cliente, s["revisor"], titulo)) == set()
