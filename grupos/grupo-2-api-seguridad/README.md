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
| `UPLOAD_DIR` | Carpeta donde se guardan los archivos subidos. |

## 5. Base de datos

| Opción | Cuándo usarla |
|-|-|
| SQLite (`sqlite:///./dev.db`) | Pruebas locales sin instalar nada. |
| MySQL o MariaDB local (XAMPP) | Con el script del Grupo 1 importado. |
| Base compartida del PM | Integración. Lo que se borra lo ven los demás grupos. |

El esquema lo crea el Grupo 1. Esta API **no crea tablas** en la base compartida.
Para comprobar la conexión:

```
python -c "from g2_api.database import probar_conexion; print(probar_conexion())"
```

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
