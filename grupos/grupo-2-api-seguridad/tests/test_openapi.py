# Pruebas de OpenAPI (G2-33, Persona 5): Swagger debe coincidir con lo que responde la API.
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


def test_rutas_con_id_documentan_404():
    assert "404" in _resp("/api/v1/users/{usuario_id}", "get")
    assert "404" in _resp("/api/v1/files/{id}", "get")
    
