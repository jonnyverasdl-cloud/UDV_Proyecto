# Guía del Grupo 2: API y Seguridad

Coordinador: Daniel (dancobs) · Versión 2 · 10-oct-2026

**Cómo usar esta guía:** busca tu nombre en la sección 2 y mira la semana actual. Ahí está lo que te toca y la fecha de entrega.

---

## 1. Dónde estamos

| Ya está hecho | Quién |
|-|-|
| Migración al repo oficial, rama `grupo-2` | Todos |
| Login (`POST /api/v1/auth/login`) | Daniel |
| Listar, crear y actualizar usuarios (`/api/v1/users`) | Randy |
| Formato de errores (`error_handler.py`) | Edgar |
| Pantalla de login (`frontend-login/`) | Fulvio |
| Esqueleto: `main.py`, `config.py`, `database.py`, `models.py`, `requirements.txt` | Robert |

**Ojo:** todavía no hay base de datos. Mientras el Grupo 1 no entregue MariaDB, trabajamos con el JSON de prueba (`g2_api/datos_prueba/usuarios_prueba.json`).

---

## 2. Quién hace qué, por semana

**Corte de cada semana: martes a las 23:59.** Lo que no esté subido a `grupo-2` ese día se toma como no entregado.

Cada tarea dice: **archivo → qué haces** y, en *cursiva*, con quién se conecta.

---

### Daniel · Persona 1 · Autenticación

**Semana 1 · martes 13-oct**
- `g2_api/seguridad.py` (nuevo) → dos funciones: `crear_token()` arma el token JWT y `verificar_token()` lo valida.
  *Randy lo usa en su middleware.*
- `routers/auth.py` → el login devuelve el token, no solo "Login exitoso".
  *Fulvio lo guarda en el frontend.*

**Semana 2 · martes 20-oct**
- `routers/auth.py` → `POST /auth/logout` invalida el token.
- `routers/auth.py` → `GET /me` devuelve quién soy y mis roles, sin la contraseña.

**Semana 3 · martes 27-oct**
- `routers/auth.py` → límite de intentos: 5 fallos = 15 minutos bloqueado.
- `routers/auth.py` → contraseña de 8 a 64 caracteres.
  *Los números salen del `.env`.*

**Semana 4 · martes 03-nov**
- `tests/test_auth.py` → pruebas: login bien, login mal (401), logout y `/me` sin token (401).

**Semana 5 · martes 10-nov**
- Revisar los 36 escenarios de QA y abrir el PR `grupo-2 → main`.

---

### Randy · Persona 2 · Usuarios y roles

**Semana 1 · martes 13-oct**
- `routers/users.py` → quitar `id` del body; el sistema pone el siguiente número.
- `routers/roles.py` (nuevo) → `GET /api/v1/roles` lista los roles; `POST` crea uno (solo administrador).
  *Robert lo agrega en `main.py`.*

**Semana 2 · martes 20-oct**
- `middleware/auth_middleware.py` → leer el usuario del header `Authorization: Bearer <token>`, ya no del correo.
  *Usa `verificar_token()` de Daniel.*

**Semana 3 · martes 27-oct**
- `routers/users.py` → `GET /users/{id}` muestra un usuario; 404 si no existe.
- `routers/users.py` → la lista de usuarios usa la paginación.
  *Usa `paginacion.py` de Edgar.*

**Semana 4 · martes 03-nov**
- `tests/test_users.py` → pruebas: 401 sin token, 403 sin permiso, 404 y 409 por correo repetido.

---

### Edgar · Persona 3 · Errores, paginación y registro

**Semana 1 · martes 13-oct**
- `utils/paginacion.py` (nuevo) → función que recibe una lista y devuelve `page`, `per_page`, `total` y `data`. Máximo 100 por página.
  *Randy la usa en `GET /users`.*

**Semana 2 · martes 20-oct**
- `utils/registro.py` (nuevo) → función `registrar(accion, usuario, ip)` que guarda login, logout y usuario creado o desactivado.
  *Daniel y Randy la llaman.*

**Semana 3 · martes 27-oct**
- `middleware/error_handler.py` → revisar que 401, 403, 404, 409 y 422 salgan con el formato común.

**Semana 4 · martes 03-nov**
- `tests/test_errores.py` → pruebas del formato de error y de la paginación.

---

### Fulvio · Persona 4 · Archivos y frontend

**Semana 1 · martes 13-oct**
- `frontend-login/script.js` → input con `id="correo"`, fetch a `/api/v1/auth/login`, usar `respuesta.ok` y mostrar el error si falla.
  *Se conecta al login de Daniel.*

**Semana 2 · martes 20-oct**
- `frontend-login/script.js` → guardar el token del login y mandarlo en las siguientes peticiones.
- `routers/files.py` (nuevo) → `POST /api/v1/files`: solo PDF, JPG o PNG, máximo 5 MB, nombre interno aleatorio. Devuelve `file_id`.
  *Robert lo agrega en `main.py`.*

**Semana 3 · martes 27-oct**
- `routers/files.py` → `GET /api/v1/files/{id}`: descarga solo si tiene token.
  *Usa el middleware de Randy.*

**Semana 4 · martes 03-nov**
- `tests/test_files.py` → pruebas: tipo no permitido, archivo muy grande y descarga sin token (401).

---

### Robert · Persona 5 · Base del proyecto e integración

**Semana 1 · martes 13-oct**
- `main.py` → conectar el `error_handler`: importar `register_error_handlers` y llamarlo con `app`.
  *Es el archivo de Edgar.*
- `GUIA_GRUPO2.md` → moverla de `g2_api/` a la carpeta del grupo, junto a `README.md`.

**Semana 2 · martes 20-oct**
- `main.py` → agregar los routers nuevos: `roles` y `files`.
  *Son de Randy y Fulvio.*

**Semana 3 · martes 27-oct**
- `.env.example`, `requirements.txt`, `database.py` → conexión a MariaDB: agregar `PyMySQL` y la `DATABASE_URL`.
  *Depende de que el Grupo 1 entregue la base.*

**Semana 4 · martes 03-nov**
- `README.md` → títulos y tablas bien hechas.
- `tests/conftest.py` → revisar que `pytest` corra para todos.

---

## 3. Cómo entregar cada semana

1. **Al empezar:** en VS Code, `...` → **Pull**.
2. Trabaja **solo en tus archivos**.
3. Prueba que levante: `.venv\Scripts\python.exe -m uvicorn g2_api.main:app --reload --reload-dir g2_api`
4. **+** a tus archivos → mensaje claro (por ejemplo `roles: GET y POST /roles`) → **Commit** → **Push**.
5. Avisa en el grupo qué subiste.

**Si no arranca, no lo subas.** Si te trabas, avisa antes del martes, no el martes.

---

## 4. Reglas (no cambian)

- Rutas en inglés con `/api/v1`. Datos y variables en español.
- Imports siempre con `g2_api.` al inicio (`from g2_api.routers import auth`).
- Errores: `{"error": {"code": "...", "message": "...", "details": {}}}`
- Listas: `page`, `per_page`, `total`, `data`.
- Nunca devolver la contraseña ni el hash.
- Nada de claves en el código: van en `.env`, y el `.env` no se sube.
- Nunca push a `main`. Solo Daniel abre el PR `grupo-2 → main`.
- Cada quien sube con **su propia cuenta** (el PM cuenta los commits).

---

## 5. Checklist del PR (del CONTRATO.md)

- [ ] Se instala desde cero con `pip install -r requirements.txt`.
- [ ] Rutas `/api/v1`, formato de error, paginación y fechas ISO 8601.
- [ ] Pruebas de 401, 403, 404, 409 y 422, y pasan.
- [ ] Sin credenciales ni datos reales en el código.
- [ ] La documentación (`/api/v1/docs`) coincide con lo que responde la API.
- [ ] No se tocó nada fuera de `grupos/grupo-2-api-seguridad/`.

---

## 6. Referencia: estructura del proyecto (ya armada)

```
grupos/grupo-2-api-seguridad/
├── CONTRATO.md, 02_Requerimientos...docx   ← del PM, no tocar
├── README.md, requirements.txt, .env.example, .gitignore   ← Robert
├── frontend-login/        ← Fulvio
├── tests/                 ← todos (cada uno su test_*.py)
└── g2_api/
    ├── main.py, config.py, database.py, models.py   ← Robert
    ├── seguridad.py       ← Daniel (token JWT)
    ├── datos_prueba/      ← JSON temporal hasta tener MariaDB
    ├── routers/           ← auth.py (Daniel), users.py y roles.py (Randy), files.py (Fulvio)
    ├── middleware/        ← auth_middleware.py (Randy), error_handler.py (Edgar)
    └── utils/             ← paginacion.py y registro.py (Edgar)
```

Para correr la API: `http://127.0.0.1:8000/api/v1/docs`

---

## 7. Pendientes con otros grupos

- **Grupo 1:** ¿MariaDB local o servidor compartido? ¿Cuándo sube el script con datos semilla?
- **Grupos 3 y 5:** ¿necesitan un rol "autoridad" para autorizar programas?
- **Todos:** el código de rol es `administrador` o `admin`. Hay que alinearlo.
