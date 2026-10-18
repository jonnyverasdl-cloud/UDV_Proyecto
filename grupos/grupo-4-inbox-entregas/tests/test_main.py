"""
Pruebas automáticas de main.py — los 11 endpoints que no son del inbox
(detalle, borrador, comentarios, archivos, y las 6 transiciones).


"""
import pytest
from fastapi.testclient import TestClient

import g4_inbox.routes as modulo_routes
from g4_inbox.main import app

cliente = TestClient(app)


@pytest.fixture(autouse=True)
def reiniciar_base_de_datos():
    """Cada prueba empieza con los datos originales, sin lo que dejaron las anteriores."""
    modulo_routes.DB[:] = modulo_routes._construir_db()
    yield


# ============================================================================
# DETALLE
# ============================================================================
def test_detalle_de_tarea_existente_devuelve_200():
    respuesta = cliente.get("/api/v1/assignments/1")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["id"] == 1
    assert "allowed_actions" in cuerpo


def test_detalle_de_tarea_inexistente_devuelve_404():
    respuesta = cliente.get("/api/v1/assignments/9999")
    assert respuesta.status_code == 404


# ============================================================================
# BORRADOR
# ============================================================================
def test_guardar_borrador_no_cambia_el_estado():
    antes = cliente.get("/api/v1/assignments/2").json()["status"]
    respuesta = cliente.put(
        "/api/v1/assignments/2/submission-draft",
        json={"comment": "borrador de prueba"},
    )
    despues = cliente.get("/api/v1/assignments/2").json()["status"]
    assert respuesta.status_code == 200
    assert respuesta.json()["draft_comment"] == "borrador de prueba"
    assert antes == despues  # guardar borrador NUNCA cambia el estado


def test_guardar_borrador_en_tarea_inexistente_devuelve_404():
    respuesta = cliente.put("/api/v1/assignments/9999/submission-draft", json={})
    assert respuesta.status_code == 404


# ============================================================================
# COMENTARIOS
# ============================================================================
def test_crear_y_listar_comentario():
    respuesta = cliente.post(
        "/api/v1/assignments/1/comments", json={"text": "comentario de prueba"}
    )
    assert respuesta.status_code == 200
    listado = cliente.get("/api/v1/assignments/1/comments").json()
    assert any(c["text"] == "comentario de prueba" for c in listado)


def test_comentario_sin_texto_es_rechazado():
    respuesta = cliente.post("/api/v1/assignments/1/comments", json={})
    assert respuesta.status_code == 422  # "text" es obligatorio


# ============================================================================
# ARCHIVOS
# ============================================================================
def test_vincular_archivo():
    respuesta = cliente.post(
        "/api/v1/assignments/1/files",
        json={"file_id": "f-test-1", "name": "evidencia.pdf"},
    )
    assert respuesta.status_code == 200
    assert {"file_id": "f-test-1", "name": "evidencia.pdf"} in respuesta.json()["files"]


# ============================================================================
# TRANSICIONES — probamos el ciclo completo, en orden, con una tarea fija
# ============================================================================
@pytest.fixture
def tarea_assigned():
    """Busca una tarea que esté en 'assigned' para empezar el ciclo limpio."""
    inbox = cliente.get("/api/v1/inbox", headers={"X-User": "1"}).json()["data"]
    for t in inbox:
        if t["status"] == "assigned":
            return t["id"]
    pytest.skip("No hay ninguna tarea en 'assigned' para probar el ciclo")


def test_iniciar_tarea_assigned_pasa_a_in_progress(tarea_assigned):
    respuesta = cliente.post(
        f"/api/v1/assignments/{tarea_assigned}/start", headers={"X-Role": "docente"}
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["status"] == "in_progress"


def test_transicion_invalida_devuelve_409(tarea_assigned):
    # "approve" nunca es válido desde "assigned"
    respuesta = cliente.post(
        f"/api/v1/assignments/{tarea_assigned}/approve", headers={"X-Role": "revisor"}
    )
    assert respuesta.status_code == 409


def test_transicion_con_rol_incorrecto_devuelve_403(tarea_assigned):
    # "start" es del docente, no del revisor
    respuesta = cliente.post(
        f"/api/v1/assignments/{tarea_assigned}/start", headers={"X-Role": "revisor"}
    )
    assert respuesta.status_code == 403


def test_entregar_sin_archivo_devuelve_422(tarea_assigned):
    cliente.post(f"/api/v1/assignments/{tarea_assigned}/start", headers={"X-Role": "docente"})
    respuesta = cliente.post(
        f"/api/v1/assignments/{tarea_assigned}/submit", headers={"X-Role": "docente"}
    )
    assert respuesta.status_code == 422


def test_devolver_sin_observacion_devuelve_422(tarea_assigned):
    cliente.post(f"/api/v1/assignments/{tarea_assigned}/start", headers={"X-Role": "docente"})
    cliente.post(
        f"/api/v1/assignments/{tarea_assigned}/files",
        json={"file_id": "f-test-2", "name": "ev.pdf"},
    )
    cliente.post(f"/api/v1/assignments/{tarea_assigned}/submit", headers={"X-Role": "docente"})
    cliente.post(f"/api/v1/assignments/{tarea_assigned}/review", headers={"X-Role": "revisor"})
    respuesta = cliente.post(
        f"/api/v1/assignments/{tarea_assigned}/return",
        headers={"X-Role": "revisor"},
        json={"comment": ""},
    )
    assert respuesta.status_code == 422


def test_ciclo_completo_hasta_aprobada(tarea_assigned):
    t = tarea_assigned
    assert cliente.post(f"/api/v1/assignments/{t}/start", headers={"X-Role": "docente"}).status_code == 200
    cliente.post(f"/api/v1/assignments/{t}/files", json={"file_id": "f-test-3", "name": "ev.pdf"})
    assert cliente.post(f"/api/v1/assignments/{t}/submit", headers={"X-Role": "docente"}).status_code == 200
    assert cliente.post(f"/api/v1/assignments/{t}/review", headers={"X-Role": "revisor"}).status_code == 200
    respuesta = cliente.post(f"/api/v1/assignments/{t}/approve", headers={"X-Role": "revisor"})
    assert respuesta.status_code == 200
    assert respuesta.json()["status"] == "approved"
