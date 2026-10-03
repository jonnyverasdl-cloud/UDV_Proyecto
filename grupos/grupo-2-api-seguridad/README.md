Grupo 2 - API y Seguridad (`g2_api`)

Backend en Python (FastAPI) con autenticacion, usuarios, roles y archivos.
Rutas bajo `/api/v1` segun `CONTRATO.md` y `CONTRATO_COMUN.md`.

python -m venv .venv
.venv\Scripts\activate # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env # Linux/Mac: cp .env.example .env -> y editar SECRET_KEY

Correr
python -m uvicorn g2_api.main:app --reload
Documentacion OpenAPI: http://127.0.0.1:8000/api/v1/openapi (interfaz: `/api/v1/docs`).

Probar
pytest

Variables de entorno (`.env`, nunca se sube)
| Variable | Para que sirve |
| `DATABASE_URL` | Conexion a la base (SQLite local por ahora) |
| `SECRET_KEY` | Firma de los JWT. Obligatoria; usar un valor largo y aleatorio |
| `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` | Algoritmo y vigencia del token |
| `CORS_ORIGINS` | Origenes permitidos, separados por coma |
| `LOGIN_MAX_INTENTOS`, `LOGIN_BLOQUEO_MINUTOS` | Control de intentos de login |

 Seguridad
-Contraseñas solo con hash bcrypt; ninguna respuesta las devuelve.
-Autorizacion en el servidor con token `Authorization: Bearer <token>`.
-Errores en formato comun, sin trazas ni SQL ni rutas internas.
-Sin credenciales en el codigo: todo en `.env`.

Estructura
`g2_api/` codigo (routers, middleware, utils) · `tests/` pruebas · `CONTRATO.md` del PM.
