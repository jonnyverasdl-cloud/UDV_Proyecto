# Grupo 2 · API y Seguridad (`g2_api`)

Backend en Python (FastAPI) con autenticación, usuarios, roles y archivos.
Las rutas van bajo `/api/v1`, según `CONTRATO.md` y `CONTRATO_COMUN.md`.

## 1. Instalar

Parado en `grupos/grupo-2-api-seguridad/`:

```
python -m venv .venv
.venv\Scripts\activate        # Windows (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env        # Linux/Mac: cp .env.example .env
```

Después abre `.env` y define `SECRET_KEY` (valor largo y aleatorio) y `DATABASE_URL`.

## 2. Correr

```
python -m uvicorn g2_api.main:app --reload
```

- Interfaz de la documentación: `http://127.0.0.1:8000/api/v1/docs`
- Documento OpenAPI: `http://127.0.0.1:8000/api/v1/openapi.json`

## 3. Probar

```
python -m pytest
```

Las pruebas usan una base SQLite temporal. Nunca tocan la base compartida.

## 4. Variables de entorno

El archivo `.env` **nunca se sube** al repositorio. Se copia desde `.env.example`.

| Variable | Para qué sirve |
|-|-|
| `DATABASE_URL` | Conexión a la base (`mysql+pymysql://...`). Sin ella usa SQLite local. |
| `SECRET_KEY` | Firma de los JWT. Obligatoria; valor largo y aleatorio. |
| `ALGORITHM` | Algoritmo del token (`HS256`). |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Vigencia del token (120 minutos = 7200 s). |
| `CORS_ORIGINS` | Orígenes del frontend permitidos, separados por coma. |
| `LOGIN_MAX_INTENTOS` | Intentos fallidos antes del bloqueo (5 intentos). |
| `LOGIN_BLOQUEO_MINUTOS` | Minutos de bloqueo (15 minutos). |
| `CONTRASENA_MIN` / `CONTRASENA_MAX` | Largo de la contraseña (de 8 a 64 caracteres). |
| `UPLOAD_DIR` | Carpeta donde se guardan los archivos subidos. |

## 5. Base de datos

| Opción | Cuándo usarla |
|-|-|
| SQLite (`sqlite:///./dev.db`) | Pruebas locales sin instalar nada. |
| MySQL de Docker | Desde la raíz del repo: `docker compose up -d db` (puerto local 3307). |
| MySQL o MariaDB local (XAMPP) | Con el script del Grupo 1 importado. |
| Base compartida del PM | Integración. Lo que se borra lo ven los demás grupos. |

El esquema lo crea el Grupo 1 (`01_schema.sql` y `02_seed.sql`). Esta API **no crea tablas** en la base compartida.
Las fechas se guardan en UTC y cada conexión nueva queda en UTC.

Para comprobar la conexión:

```
python -c "from g2_api.database import probar_conexion; print(probar_conexion())"
```

### Auditoría: quién hizo el cambio

Los triggers del Grupo 1 guardan el actor desde las variables `@actor_id` y `@ip_origen` de la conexión.
Antes de crear, cambiar o desactivar algo, el router llama:

```
from g2_api.database import fijar_actor
fijar_actor(db, usuario_actual_id, ip)
```

Hay que llamarla otra vez después de cada `commit`, porque la conexión vuelve al pool y las variables se limpian.
En `auditoria` solo se escriben a mano los eventos de acceso (login, login fallido y logout).

## 6. Seguridad

- Contraseñas solo con hash bcrypt; ninguna respuesta las devuelve.
- Autorización en el servidor con `Authorization: Bearer <token>`.
- Errores en el formato común, sin trazas, SQL ni rutas internas.
- Sin credenciales en el código: todo va en `.env`.

## 7. Estructura

| Carpeta o archivo | Qué contiene |
|-|-|
| `g2_api/` | Código: routers, middleware y utils. |
| `frontend-login/` | Pantalla de login. |
| `tests/` | Pruebas automáticas (pytest). |
| `CONTRATO.md` | Contrato del PM (no se toca). |
| `GUIA_GRUPO2.md` | Quién hace qué cada semana. |
| `PENDIENTES_QA.md` | Pendientes del QA y quién los corrige. |

## 8. Responsable de cada archivo

| Persona | Cuenta de GitHub | Archivos |
|-|-|-|
| Daniel - Persona 1 (coordinador) | `dancobs` | `routers/auth.py`, `seguridad.py`, `tests/test_auth.py`, `GUIA_GRUPO2.md` |
| Randy - Persona 2 | `rtorresixcoy375` | `routers/users.py`, `routers/roles.py`, `middleware/auth_middleware.py`, `tests/test_users.py` |
| Edgar - Persona 3 | `zeusgeo99-code` | `middleware/error_handler.py`, `utils/paginacion.py`, `utils/registro.py`, `tests/test_errores.py` |
| Fulvio - Persona 4 | `Ful55` | `routers/files.py`, `frontend-login/`, `tests/test_files.py` (por crear) |
| Robert - Persona 5 | `Davids107` | `main.py`, `config.py`, `database.py`, `models.py`, `requirements.txt`, `.env.example`, `.gitignore`, `README.md`, `tests/conftest.py` |
| PM | — | `CONTRATO.md`, `CONTRATO_COMUN.md`, los `.docx` de requerimientos y la raíz del repo |
