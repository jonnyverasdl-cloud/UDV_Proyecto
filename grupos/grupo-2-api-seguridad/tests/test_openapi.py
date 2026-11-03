# Pruebas de OpenAPI (G2-33, Persona 5): Swagger debe coincidir con lo que responde la API.
from datetime import datetime

from g2_api.main import app

def _resp(ruta, metodo):
    return app.openapi()["paths"][ruta][metodo]["responses"]

def test_post_users_documenta_401_403_409_y_422():
    r = _resp("/api/v1/users", "post")
    for codigo in ("201", "401", "403", "409", "422"):
        assert codigo in r

def test_get_users_documenta_403_y_ejemplo_paginado():
    r = _resp("/api/v1/users", "get")
    assert "403" in r
    ejemplo = r["200"]["content"]["application/json"]["example"]
    assert set(ejemplo) == {"page", "per_page", "total", "data"}

def test_me_documenta_401_y_ejemplo_objeto():
    r = _resp("/api/v1/me", "get")
    assert "401" in r
    assert isinstance(r["200"]["content"]["application/json"]["example"], dict)

def test_422_usa_el_formato_comun_de_errores():
    ejemplo = _resp("/api/v1/users", "post")["422"]["content"]["application/json"]["example"]
    assert set(ejemplo["error"]) == {"code", "message", "details"}

def test_422_documenta_details_como_objeto_con_un_campo_por_llave():
    ejemplo = _resp("/api/v1/users", "post")["422"]["content"]["application/json"]["example"]
    detalles = ejemplo["error"]["details"]
    assert isinstance(detalles, dict) and detalles
    assert all(isinstance(mensaje, str) for mensaje in detalles.values())

def test_ejemplo_de_usuario_trae_fechas_iso_con_zona_horaria():
    ejemplo = _resp("/api/v1/users/{usuario_id}", "get")["200"]["content"]["application/json"]["example"]
    for campo in ("creado_en", "actualizado_en"):
        assert datetime.fromisoformat(ejemplo[campo].replace("Z", "+00:00")).tzinfo is not None

def test_rutas_con_id_documentan_404():
    assert "404" in _resp("/api/v1/users/{usuario_id}", "get")
    assert "404" in _resp("/api/v1/files/{id}", "get")

def test_descarga_de_archivos_documenta_403_y_subida_devuelve_file_id_numerico():
    assert "403" in _resp("/api/v1/files/{id}", "get")
    ejemplo = _resp("/api/v1/files", "post")["200"]["content"]["application/json"]["example"]
    assert isinstance(ejemplo["file_id"], int)

def test_422_real_devuelve_details_como_objeto_con_un_campo_por_llave(client):
    r = client.post("/api/v1/auth/login", json={"correo": "", "password": ""})
    assert r.status_code == 422
    detalles = r.json()["error"]["details"]
    assert "correo" in detalles and isinstance(detalles["correo"], str)
