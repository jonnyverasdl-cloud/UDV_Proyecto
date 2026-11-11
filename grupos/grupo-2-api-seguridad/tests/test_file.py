
from g2_api.main import app

from tests.test_users import (
    ADMIN_CORREO,
    ADMIN_CLAVE,
    DOCENTE_CORREO,
    DOCENTE_CLAVE,
    sembrado,
)

# Helpers

def obtener_token(client, correo, password) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "correo": correo,
            "password": password
        }
    )

    assert response.status_code == 200

    return response.json()["access_token"]

# Login

def test_login_correcto(client, sembrado):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "correo": ADMIN_CORREO,
            "password": ADMIN_CLAVE
        }
    )

    assert response.status_code == 200

    body = response.json()

    assert "access_token" in body
    assert body["token_type"] == "bearer"

# Upload

def test_upload_sin_token(client):
    response = client.post(
        "/api/v1/files"
    )

    assert response.status_code == 401


def test_upload_tipo_no_permitido(client):
    response = client.post(
        "/api/v1/files",
        files={
            "file": (
                "archivo.txt",
                b"hola mundo",
                "text/plain"
            )
        }
    )

    assert response.status_code in (400, 401)


def test_upload_archivo_muy_grande(client):
    contenido = b"x" * (6 * 1024 * 1024)

    response = client.post(
        "/api/v1/files",
        files={
            "file": (
                "grande.pdf",
                contenido,
                "application/pdf"
            )
        }
    )

    assert response.status_code in (400, 401)


def test_upload_pdf_valido(client, sembrado):
    token = obtener_token(
        client,
        ADMIN_CORREO,
        ADMIN_CLAVE
    )

    contenido_pdf = b"%PDF-1.4"

    response = client.post(
        "/api/v1/files",
        headers={
            "Authorization": f"Bearer {token}"
        },
        files={
            "file": (
                "ejemplo.pdf",
                contenido_pdf,
                "application/pdf"
            )
        }
    )

    assert response.status_code == 200

    body = response.json()

    assert "file_id" in body
    assert "nombre_interno" in body

# Descarga

def test_descarga_sin_token(client):
    response = client.get(
        "/api/v1/files/1"
    )

    assert response.status_code == 401


def test_archivo_inexistente(client, sembrado):
    token = obtener_token(
        client,
        ADMIN_CORREO,
        ADMIN_CLAVE
    )

    response = client.get(
        "/api/v1/files/999999",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code in (404, 403)


def test_usuario_sin_permiso_recibe_403(client, sembrado):

    token_docente = obtener_token(
        client,
        DOCENTE_CORREO,
        DOCENTE_CLAVE
    )

    response = client.get(
        "/api/v1/files/1",
        headers={
            "Authorization": f"Bearer {token_docente}"
        }
    )

    assert response.status_code in (403, 404)
