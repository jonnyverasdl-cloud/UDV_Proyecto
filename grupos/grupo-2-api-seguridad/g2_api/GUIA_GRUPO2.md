# Guía oficial de trabajo — Grupo 2: API y Seguridad

Coordinador: Daniel (dancobs) · Versión 1 · 29-sep-2026

Esta guía reemplaza al documento de organización anterior. A partir de ahora trabajamos **solo** en el repositorio oficial del Project Manager.

---

## 1. ¿Por qué cambiamos?

El PM publicó el repositorio oficial: https://github.com/jonnyverasdl-cloud/UDV_Proyecto

Ahí hay 3 documentos que **mandan sobre todo lo demás**, en este orden:

1. `README.md` (raíz) → reglas, proceso y **estructura de carpetas**.
2. `CONTRATO_COMUN.md` → reglas que cumplen los 6 grupos (rutas `/api/v1`, formato de error, paginación, fechas).
3. `grupos/grupo-2-api-seguridad/CONTRATO.md` → **nuestros endpoints** y lo que se revisa en cada Pull Request.

Lo que cambia para nosotros:

| Antes | Ahora (según el PM) |
|-|-|
| Repo de David (`Davids107/grupo2-api-seguridad`) | Repo oficial, rama `grupo-2` |
| Carpeta `backend/` | Paquete `g2_api/` dentro de `grupos/grupo-2-api-seguridad/` |
| Sin pruebas | Carpeta `tests/` obligatoria (ningún PR entra sin pruebas) |
| Rutas `/login`, `/usuarios` | Rutas del contrato: `/api/v1/auth/login`, `/api/v1/users`… |
| Catálogos y notificaciones | **No son nuestros.** Nuestro contrato no los incluye |
| Sin roles ni archivos | `/roles` y `/files` **sí son nuestros** |

**Nuestro código no se pierde.** Lo que ya funciona se mueve a su nuevo lugar y se ajusta.

---

## 2. Qué nos toca según el CONTRATO.md (todo bajo `/api/v1`)

| Método | Ruta | Qué hace |
|-|-|-|
| POST | `/auth/login` | Autentica y entrega token |
| POST | `/auth/logout` | Invalida el token |
| GET | `/me` | Usuario, roles y permisos del que inició sesión |
| GET / POST | `/users` | Lista o crea usuarios |
| GET / PATCH | `/users/{id}` | Consulta o actualiza un usuario |
| GET / POST | `/roles` | Consulta o administra roles |
| POST | `/files` | Sube un archivo validado y devuelve `file_id` |
| GET | `/files/{id}` | Descarga autorizada |
| GET | `/openapi` | Documentación de la API |

Además somos dueños de piezas que **los otros 4 grupos van a usar**: formato de error común, paginación, middleware de autenticación y permisos, límite de intentos de login y registro de acciones sensibles.

---

## 3. Reglas de idioma

| Qué | Idioma | Fuente |
|-|-|-|
| Carpeta y paquete (`grupo-2-api-seguridad`, `g2_api`) | Fijo, no se cambia | README del PM |
| Rutas (`/auth/login`, `/users`, `/roles`, `/files`) | Inglés | CONTRATO.md |
| Campos de error y paginación (`error`, `code`, `message`, `details`, `page`, `per_page`, `total`, `data`) | Inglés | CONTRATO_COMUN |
| Estados (`draft`, `approved`…) | Inglés, minúsculas | CONTRATO_COMUN |
| Variables y campos de la base de datos (`correo`, `id_usuario`, `nombre_completo`) | Español | PM + diagrama del Grupo 1 |
| Nombres de archivo `.py` | Igual que la ruta que manejan (`auth.py`, `users.py`) | Acuerdo del grupo |

Regla fácil: **lo que ven otros grupos, en inglés; lo interno y los datos, en español.**

---

## 4. Estructura oficial del Grupo 2

```
UDV_Proyecto/                              ← repo del PM (la raíz NO se toca)
└── grupos/
    └── grupo-2-api-seguridad/             ← SOLO trabajamos aquí
        ├── CONTRATO.md                    ← del PM, no tocar
        ├── 02_Requerimientos_API_y_Seguridad.docx  ← del PM, no tocar
        ├── README.md                      ← P5: cómo instalar, correr y probar
        ├── requirements.txt               ← P5: UNA sola lista de librerías
        ├── .env.example                   ← P5: variables de ejemplo (sin secretos reales)
        ├── .gitignore                     ← P5: ignora .env, __pycache__, *.db
        ├── g2_api/                        ← TODO el código Python
        │   ├── __init__.py                ← P5 (vacío, convierte la carpeta en paquete)
        │   ├── main.py                    ← P5: crea la app, CORS, junta los routers
        │   ├── config.py                  ← P5: lee el .env
        │   ├── database.py                ← P5: conexión a la base de datos
        │   ├── models.py                  ← P5: tablas iguales al diagrama del Grupo 1
        │   ├── seguridad.py               ← P1: hash bcrypt + crear/verificar JWT
        │   ├── routers/
        │   │   ├── __init__.py
        │   │   ├── auth.py                ← P1: /auth/login, /auth/logout, /me
        │   │   ├── users.py               ← P2: /users, /users/{id}
        │   │   ├── roles.py               ← P2: /roles
        │   │   └── files.py               ← P4: /files, /files/{id}
        │   ├── middleware/
        │   │   ├── __init__.py
        │   │   ├── auth_middleware.py     ← P2: lee el token y revisa el rol
        │   │   └── error_handler.py       ← P3: formato de error común
        │   └── utils/
        │       ├── __init__.py
        │       ├── paginacion.py          ← P3: page, per_page, total, data
        │       └── registro.py            ← P3: registro de accesos y acciones sensibles
        ├── frontend-login/                ← P4 (ubicación por confirmar con el PM)
        │   ├── index.html
        │   ├── style.css
        │   └── mi_fondo.jpg
        └── tests/                         ← pruebas automáticas (pytest)
            ├── conftest.py                ← P5: configuración común de pruebas
            ├── test_auth.py               ← P1
            ├── test_users.py              ← P2
            ├── test_errores.py            ← P3
            └── test_files.py              ← P4
```

### ¿Qué es cada cosa, en simple?

- **`g2_api/`**: es un "paquete". Así los otros grupos pueden usar nuestro código con `from g2_api...` (lo pide el README del PM).
- **`__init__.py`**: archivo vacío. Le dice a Python "esta carpeta es un paquete". Sin él, los imports fallan.
- **`models.py`**: las tablas de la base de datos escritas en Python (SQLAlchemy) con los **mismos nombres del diagrama del Grupo 1**. Cuando el Grupo 1 entregue su base real, solo cambiamos la conexión en el `.env`.
- **`seguridad.py`**: las funciones de seguridad que usan varias personas (hash y token). Así no se repite código.
- **`tests/`**: código que prueba nuestro código. El PM no acepta un PR si las pruebas fallan.

---

## 5. Cambios en los archivos (qué se agrega y qué se quita)

| Archivo | Estado | Motivo |
|-|-|-|
| `routers/catalogos.py` | **Se elimina** | No está en nuestro contrato |
| `routers/notificaciones.py` | **Se elimina** | No está en nuestro contrato |
| `openapi.yaml` | **Se elimina** | Estaba vacío. FastAPI genera la documentación solo |
| `routers/usuarios.py` | **Se renombra** a `users.py` | La ruta es `/users` |
| `routers/roles.py` | **Nuevo** (P2) | `/roles` está en el contrato |
| `routers/files.py` | **Nuevo** (P4) | `/files` está en el contrato |
| `seguridad.py` | **Nuevo** (P1) | Hash + JWT en un solo lugar |
| `models.py`, `config.py` | **Nuevos** (P5) | Tablas del Grupo 1 y lectura del `.env` |
| `utils/paginacion.py`, `utils/registro.py` | **Nuevos** (P3) | Paginación y registro, obligatorios |
| `tests/*` | **Nuevos** (todos) | Obligatorio para cada PR |

Siguen siendo **5 personas**. Cambian algunas tareas:

- **P3** ya no hace catálogos: hace errores, paginación y registro.
- **P4** ya no hace notificaciones: hace archivos y el frontend.

---

## 6. Quién hace qué

### Persona 1 — Autenticación (Daniel)
Archivos: `g2_api/routers/auth.py`, `g2_api/seguridad.py`, `tests/test_auth.py`
- `POST /api/v1/auth/login`: responde **401 real** si falla (con `HTTPException`, no con 200) y entrega un JWT si es correcto.
- JWT con **PyJWT**: guardar el token en la tabla `TOKENS` (activo = true).
- `POST /api/v1/auth/logout`: marca el token como `activo = false`.
- `GET /api/v1/me`: devuelve usuario, rol y permisos (nunca la contraseña).
- Límite de intentos fallidos de login.
- Validar campos vacíos (contraseña de 8 a 64 caracteres).

### Persona 2 — Usuarios, roles y permisos
Archivos: `routers/users.py`, `routers/roles.py`, `middleware/auth_middleware.py`, `tests/test_users.py`
- Mover su `usuarios.py` actual a `users.py`, con la ruta `/users`.
- Middleware: sacar al usuario del header `Authorization: Bearer <token>`, **ya no del correo** (hoy cualquiera puede hacerse pasar por admin).
- `GET/POST /roles`.
- Correo duplicado → **409**. El `id` lo genera la base de datos, no el cliente.
- 401 sin token, 403 sin permiso, 404 si no existe.

### Persona 3 — Errores, paginación y registro
Archivos: `middleware/error_handler.py`, `utils/paginacion.py`, `utils/registro.py`, `tests/test_errores.py`
- Que **todos** los errores salgan así:
  `{"error": {"code": "VALIDATION_ERROR", "message": "...", "details": {}}}`
- Un 422 debe traer el detalle de cada campo inválido.
- Nunca mostrar trazas, SQL, rutas internas ni secretos.
- Paginación reutilizable: `page`, `per_page`, `total`, `data` (con un máximo de `per_page`).
- Registro de accesos y acciones sensibles.

### Persona 4 — Archivos y frontend
Archivos: `routers/files.py`, `frontend-login/`, `tests/test_files.py`
- `POST /files`: lista de tipos permitidos, límite de tamaño, nombre interno aleatorio y devolver `file_id`.
- `GET /files/{id}`: descargar solo si tiene permiso.
- Frontend: cambiar el `fetch` a `/api/v1/auth/login`, guardar el token y mostrar los errores del formato nuevo.

### Persona 5 — Base del proyecto e integración
Archivos: `main.py`, `config.py`, `database.py`, `models.py`, `requirements.txt`, `.env.example`, `.gitignore`, `README.md`, `tests/conftest.py`
- **Primero:** crear el esqueleto de carpetas (sección 4) en la rama `grupo-2`.
- `models.py` con las tablas del diagrama del Grupo 1 (SEGURIDAD, ROLES, TOKENS) en SQLite local.
- Un solo `requirements.txt` limpio.
- `main.py`: incluir todos los routers con el prefijo `/api/v1`, CORS leyendo `CORS_ORIGINS` del `.env` y la documentación en `/api/v1/openapi`.
- README con los pasos para instalar, correr y probar.

---

## 7. ¿Dónde va el código que ya hicimos? (migración)

| Código actual (repo de David) | Dueño | Nuevo lugar | Qué ajustar |
|-|-|-|-|
| `backend/routers/auth.py` | P1 | `g2_api/routers/auth.py` | Rutas del contrato, 401 real, JWT |
| `backend/usuarios_prueba.json` | P1 | Temporal en `g2_api/` | Se borra cuando `models.py` tenga datos semilla |
| `backend/routers/usuarios.py` | P2 | `g2_api/routers/users.py` | Ruta `/users`, 409, id automático |
| `backend/middleware/auth_middleware.py` | P2 | `g2_api/middleware/auth_middleware.py` | Leer el token, no el correo |
| `backend/middleware/error_handler.py` (vacío) | P3 | `g2_api/middleware/error_handler.py` | Escribirlo desde cero |
| `backend/database.py` | P5 | `g2_api/database.py` + `models.py` | Nombres del Grupo 1, sin contraseñas en el código |
| `backend/.env.example` | P5 | `.env.example` | Cambiar python-jose por PyJWT |
| `backend/requirements.txt` + `requirements.txt` (raíz) | P5 | `requirements.txt` | Unir en uno solo, sin duplicados |
| `backend/main.py` | P5 | `g2_api/main.py` | Incluir todos los routers, prefijo `/api/v1` |
| `frontend-login/*` | P4 | `frontend-login/` | Nueva ruta del login + token |
| `catalogos.py`, `notificaciones.py`, `openapi.yaml`, `__pycache__/` | — | No se migran | — |

**Importante para el crédito de cada uno:** cada persona sube **su propio archivo** al repo oficial con **su propia cuenta**. El PM dijo que los commits se registran con el nombre de cada contribuyente.

### Cambio en los imports (todos)

```python
# Antes
from routers import auth
from middleware.auth_middleware import requerir_rol

# Ahora
from g2_api.routers import auth
from g2_api.middleware.auth_middleware import requerir_rol
```

### Cómo se corre ahora (parados en `grupos/grupo-2-api-seguridad/`)

```
pip install -r requirements.txt
python -m uvicorn g2_api.main:app --reload
```

Documentación: http://127.0.0.1:8000/api/v1/openapi · Pruebas: `pytest`

---

## 8. Cómo trabajamos con Git (paso a paso)

**Una sola vez:**
```
git clone https://github.com/jonnyverasdl-cloud/UDV_Proyecto.git
cd UDV_Proyecto
git checkout grupo-2
```

**Cada vez que trabajas:**
```
git pull origin grupo-2          ← 1. traer lo último de todos
(trabajas SOLO en tus archivos)
git add .
git commit -m "auth: logout con token"   ← 2. mensaje: módulo + qué hiciste
git pull origin grupo-2          ← 3. traer cambios otra vez antes de subir
git push origin grupo-2          ← 4. subir
```

**Reglas:**
1. **Nunca** push a `main`. Solo a `grupo-2`.
2. Solo tocamos `grupos/grupo-2-api-seguridad/`. Nada de la raíz.
3. Cada quien toca **solo sus archivos**. Si necesitas cambiar el de otro, primero avisas.
4. Nada de contraseñas ni claves reales en el código: todo va en `.env`, y el `.env` no se sube.
5. Antes de subir, corre `pytest` y el servidor en tu compu.
6. Avisa en el chat cuando subas algo.

**El Pull Request:**
1. Todos suben a `grupo-2`.
2. Daniel revisa: estructura, pruebas y checklist del CONTRATO.md.
3. Si falta algo, Daniel le avisa a esa persona para que corrija.
4. Cuando todo está bien, **solo Daniel** abre el Pull Request `grupo-2 → main`.

---

## 9. Plan por semanas

| Semana | Meta | Responsables |
|-|-|-|
| 1 | Migración a la estructura oficial + login, logout y `/me` con JWT + formato de error + primeras pruebas → **primer PR** | Todos (P5 empieza con el esqueleto) |
| 2 | `/users` y `/roles` protegidos con token (401 y 403) + paginación | P2, P3 |
| 3 | Servicio de archivos + conectar la base real del Grupo 1 (si ya la entregó) | P4, P5 |
| 4 | Límite de intentos, registro de acciones, CORS restringido, OpenAPI revisado | P1, P3, P5 |
| 5 | Pasar los 36 escenarios de QA + integración con los grupos 3 a 6 | Todos |
| 6 | Colchón, correcciones y demo | Todos |

---

## 10. Checklist de cada Pull Request (del CONTRATO.md)

- [ ] Se instala desde cero con `pip install -r requirements.txt`.
- [ ] Cumple el CONTRATO_COMUN (rutas `/api/v1`, formato de error, paginación, fechas ISO 8601).
- [ ] Tiene pruebas de 401, 403, 404, 409 y 422, y pasan.
- [ ] No hay credenciales en el código.
- [ ] La documentación OpenAPI coincide con lo que responde la API.
- [ ] No se modificó nada fuera de nuestra carpeta.
- [ ] No hay datos reales escritos en el código.
- [ ] El README explica cómo instalar, las variables de entorno y la seguridad.

---

## 11. Pendientes de confirmar con el PM y el Grupo 1

**PM:**
- ¿Ya están los 5 integrantes como colaboradores?
- ¿Dónde va el frontend del login?
- Propuesta del stack: FastAPI + SQLAlchemy + PyJWT + bcrypt + IDs enteros.

**Grupo 1:**
- Tablas que faltan en el diagrama: permisos, archivos, registro/auditoría.
- Campo `activo` en SEGURIDAD para poder desactivar usuarios.
- Motor de base de datos que van a usar.
