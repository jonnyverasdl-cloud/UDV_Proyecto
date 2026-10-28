# Aplicacion principal del Grupo 2 (Persona 5).
# Cada persona agrega aqui su router cuando lo sube.
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware

from g2_api import config
from g2_api.middleware.error_handler import register_error_handlers
from g2_api.routers import auth
from g2_api.routers import files
from g2_api.routers import roles
from g2_api.routers import users

app = FastAPI(
    title="Grupo 2 - API y Seguridad",
    version="0.1.0",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json", # Misma ruta que el main.py de la raíz del PM.
    redoc_url=None,
)

# Errores: Todos salen con el formato comun (codigo, mensaje y detalles). Es el archivo de Edgar.
register_error_handlers(app)

# CORS: Solo los origenes definidos en CORS_ORIGINS del .env.
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Routers: Cada persona agrega el suyo.
app.include_router(auth.router) # Persona 1: /auth/login y /auth/logout.
# GET /api/v1/me (Daniel): Se conecta solo cuando auth.py ya trae me_router. Así main.py no se rompe antes.
if hasattr(auth, "me_router"):
    app.include_router(auth.me_router)
app.include_router(users.router) # Persona 2: /users.
app.include_router(roles.router) # Persona 2: /roles.
app.include_router(files.router) # Persona 4: /files.


# --- OpenAPI (G2-33) ---------------------------------------------------------
# Swagger debe mostrar lo mismo que responde la API. Los routers son de otras personas,
# asi que aqui se completan los codigos HTTP y los ejemplos sin tocar sus archivos.
_ERRORES = {
    400: ("BAD_REQUEST", "Solicitud inválida."),
    401: ("UNAUTHORIZED", "Falta el token de autenticación."),
    403: ("FORBIDDEN", "No tienes permisos necesarios para realizar esta acción."),
    404: ("NOT_FOUND", "Recurso no encontrado."),
    409: ("CONFLICT", "El correo ya está registrado."),
    422: ("VALIDATION_ERROR", "Datos de entrada inválidos."),
}
_USUARIO = {
    "id": 12, "correo": "docente@udv.edu.gt", "nombres": "Ana", "apellidos": "López",
    "activo": True, "roles": ["teacher"],
}


def _resp_error(codigo: int):
    code, msg = _ERRORES[codigo]
    detalles = {}
    if codigo == 422:
        detalles = {"campos": {"correo": {"message": "Input should be a valid string", "type": "string_type"}}}
    return {
        "description": msg,
        "content": {"application/json": {
            "schema": {"$ref": "#/components/schemas/ErrorResponse"},
            "example": {"error": {"code": code, "message": msg, "details": detalles}},
        }},
    }


def _resp_ok(descripcion: str, ejemplo, esquema: dict | None = None):
    cuerpo = {"example": ejemplo}
    if esquema:
        cuerpo["schema"] = esquema
    return {"description": descripcion, "content": {"application/json": cuerpo}}


def _completar_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    esquema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    esquema.setdefault("components", {}).setdefault("schemas", {})["ErrorResponse"] = {
        "type": "object",
        "required": ["error"],
        "properties": {"error": {
            "type": "object",
            "required": ["code", "message", "details"],
            "properties": {
                "code": {"type": "string", "example": "VALIDATION_ERROR"},
                "message": {"type": "string"},
                "details": {"type": "object"},
            },
        }},
    }
    pagina = {"page": 1, "per_page": 20, "total": 1, "data": [_USUARIO]}
    for ruta, metodos in esquema["paths"].items():
        for metodo, op in metodos.items():
            r = op["responses"]
            publica = ruta.endswith("/auth/login")
            admin = "/users" in ruta or "/roles" in ruta
            if not publica:
                r["401"] = _resp_error(401)
            if admin:
                r["403"] = _resp_error(403)
            if "{" in ruta:
                r["404"] = _resp_error(404)
            if ruta.endswith("/users") and metodo == "post" or (ruta.endswith("{usuario_id}") and metodo == "patch"):
                r["409"] = _resp_error(409)
            if ruta.endswith("/files") and metodo == "post":
                r["400"] = _resp_error(400)
            if "422" in r:
                r["422"] = _resp_error(422)
            # Ejemplos reales (antes Swagger mostraba un "string" generico).
            if ruta.endswith("/users") and metodo == "get":
                r["200"] = _resp_ok("Lista paginada de usuarios.", pagina)
            elif ruta.endswith("/users") and metodo == "post":
                r["201"] = _resp_ok("Usuario creado.", _USUARIO)
            elif ruta.endswith("{usuario_id}"):
                r["200"] = _resp_ok("Usuario.", _USUARIO)
            elif ruta.endswith("/me"):
                r["200"] = _resp_ok("Usuario autenticado con sus roles y permisos.",
                                    {**_USUARIO, "permisos": ["users.read"]})
            elif ruta.endswith("/files") and metodo == "post":
                r["200"] = _resp_ok("Archivo aceptado.", {"file_id": "3f2a9c1e-0000-4000-8000-000000000000"})
    app.openapi_schema = esquema
    return esquema


app.openapi = _completar_openapi
