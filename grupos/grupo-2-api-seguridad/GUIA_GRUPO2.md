# Guía del Grupo 2: API y Seguridad

Coordinador: Daniel (dancobs) · Versión 2 · 10-oct-2026

**Cómo usar esta guía:** busca tu nombre en la sección 2 y mira la semana actual. Ahí está lo que te toca y la fecha de entrega.

---

## 1. Dónde estamos

**Leyenda:** ✅ Hecho y verificable en el repo · 🔵 Implementado, falta validación o retest de QA · ⏳ Pendiente de implementar

| Estado | Qué | Quién |
|-|-|-|
| ✅ | Migración al repo oficial, rama `grupo-2` | Todos |
| ✅ | Esqueleto: `main.py`, `config.py`, `database.py`, `models.py`, `requirements.txt` | Robert |
| ✅ | `main.py` incluye los routers `auth`, `/me`, `users`, `roles` y `files` | Robert |
| 🔵 | Login (`POST /api/v1/auth/login`): consulta la base compartida y devuelve el JWT | Daniel |
| 🔵 | `POST /auth/logout` y `GET /me` (subidos el 20-oct; falta retest de G2-05 y G2-07) | Daniel |
| 🔵 | Listar, crear y actualizar usuarios (`/api/v1/users`) y `GET /users/{id}` con 404 | Randy |
| 🔵 | Formato de errores (`error_handler.py`): ya responde como el contrato común (ver 8.4) | Edgar |
| 🔵 | Pantalla de login (`frontend-login/`) | Fulvio |
| 🔵 | `POST /api/v1/files`: valida el tipo real con `puremagic` | Fulvio |
| ⏳ | Middleware: leer al usuario desde la base, revisar sesión no revocada y rol `admin` (hoy usa la lista JSON) | Randy |
| ⏳ | `users.py` y `roles.py` pasados a la base | Randy |
| ⏳ | Archivos: token obligatorio en `POST /files`, `GET /files/{id}` y registro en la tabla `archivo` | Fulvio |
| ⏳ | Bloqueo por intentos y auditoría: `registro.py` ya existe, pero login y logout todavía no lo llaman | Daniel y Edgar |
| ⏳ | Paginación en `GET /users` (`paginacion.py` existe, `users.py` no la usa) | Randy |
| ⏳ | `pytest` completo: hoy 15 pruebas fallan por `error_handler.py` (ver 8.4) | Edgar |

**Ojo:** el PM entregó una base compartida (MySQL en Railway). Los datos de acceso se piden al PM y van **solo en tu `.env`**, nunca en el repo. Lo que se borra ahí lo ven los demás grupos. El script SQL del Grupo 1 todavía no está en el repo. El login y la sesión ya usan la base; `users.py` y el middleware todavía leen el JSON de prueba (`g2_api/datos_prueba/usuarios_prueba.json`), que ya no debe usarse para autenticar.

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
- **Grupos 3 y 5:** ¿necesitan un rol "autoridad" para - **Todos:** el código de rol es `admin` (el del Grupo 1; los demás: `coordinator`, `teacher`, `reviewer`, `authority`, `auditor`). Hay que alinear el código que dice `administrador`.

---

## 8. Pendientes del QA (Update No. 1 · 17-oct)

Allison Espaderos (QA) entregó el primer informe y creó las tareas en el Planner (plan «2. Api y Seguridad - Allison»). El detalle por persona está en `PENDIENTES_QA.md` (misma carpeta). Las tarjetas del Planner muestran fecha **21/10** y dicen que las correcciones deben quedar disponibles para un nuevo retest.

### 8.1 Tareas del Planner

Las tres tareas están «No iniciado», prioridad en el nombre, etiqueta «Grupo 2» y **sin responsable asignado**: son de todo el grupo. El texto de cada punto aparece cortado en las capturas; abajo va lo visible.

| Prioridad | Punto | Escenarios | Quién lo resuelve |
|-|-|-|-|
| 🔴 Alta | 1. Autenticación y autorización JWT | G2-06, 08, 09, 10, 37, 38 (la lista se corta en «G2-3…») | Randy (middleware); Daniel (`verificar_token`) |
| 🔴 Alta | 2. Cierre de sesión: implementar `logout` | G2-05 | Daniel |
| 🔴 Alta | 3. Control de acceso a recursos | G2-17 | Randy; Fulvio (archivos) |
| 🟡 Media | 1. Consulta del usuario autenticado: implementar `/me` | G2-07 | Daniel |
| 🟡 Media | 2. Consulta individual de usuarios | G2-12 (y G2-11) | Randy |
| 🟡 Media | 3. Manejo de recursos inexistentes | G2-26 | Randy; Fulvio (`/files/{id}`) |
| 🟡 Media | 4. Documentación OpenAPI/Swagger | G2-33 | Todos; Robert revisa al final |
| ⚪ Baja | 1. Paginación de usuarios | G2-31 | Randy; Edgar (`paginacion.py`) |
| ⚪ Baja | 2. Bloqueo por intentos fallidos | G2-34 | Daniel; Edgar (`registro.py`) |
| ⚪ Baja | 3. Registro de auditoría | G2-36 | Daniel y Randy; Edgar (`registro.py`) |

Notas del QA: en **Alta**, «las correcciones deben estar disponibles para retest y los escenarios afectados deben poder verificarse nuevamente por QA». En **Media**, «las funcionalidades pendientes deben quedar disponibles y documentadas para permitir la ejecución de las pruebas». **Baja** no trae notas. Falta copiar el texto del tablero «Update No. 1 17/10».

### 8.2 Semana 2 (martes 20-oct) con escenarios

| Persona | Tarea | Escenarios QA |
|-|-|-|
| Daniel | `POST /auth/logout` revoca el token | G2-05 |
| Daniel | `GET /me` sin contraseña | G2-07 |
| Randy | Middleware lee `Authorization: Bearer` desde la **base** (no del JSON) | G2-06, 08, 09, 10, 17, 37, 38 |
| Edgar | `registro.py` guarda en la tabla `auditoria` (columnas `tabla`, `registro_id`, `ip_origen`) | G2-36 |
| Fulvio | `POST /files` con token, tipo real y 5 MB | G2-18, 19, 20 |
| Robert | `main.py` con los routers `roles` y `files` | G2-18 a G2-22 y G2-33 |

### 8.3 Cuando alguien corrija

1. Sube a `grupo-2` con su propia cuenta. 2. Avisa en el grupo. 3. Se le avisa a Allison **en el grupo** (no por privado), para que el PM vea el avance de todos, y ella repite el escenario (retest).

### 8.4 Observaciones de Allison sobre esta guía (21-oct)

Allison revisó `GUIA_GRUPO2.md` y `PENDIENTES_QA.md`. Ella indica que la prioridad principal sigue siendo corregir la autenticación y autorización JWT. Lo que se ajustó:

| Observación de Allison | Qué quedó en la guía |
|-|-|
| Diferenciar lo implementado de lo pendiente de validación por QA | La sección 1 ahora marca cada punto como ✅, 🔵 o ⏳. `logout` y `/me` están subidos (Daniel, 20-oct) y quedan en 🔵 hasta el retest. |
| Actualizar el estado de archivos y de la integración con la base | `POST /files` existe, pero no exige token, no hay `GET /files/{id}` y no registra en la tabla `archivo`. Login y sesión usan la base; `users.py` y el middleware siguen con el JSON. |
| Inconsistencia entre el formato de errores actual y el contrato común | `error_handler.py` (20-oct) ya responde `{"error": {"code", "message", "details": {}}}`, igual que `CONTRATO_COMUN.md`. G2-30 dio PASS con el formato anterior, así que se repite. |
| Problema en las pruebas automáticas y en las funciones de auditoría | `pytest` completo: 15 fallan y 14 pasan. En `error_handler.py` (línea 45) `DEFAULT_MESSAGES` quedó dentro de unas comillas `''''...'''` y no existe; Edgar lo corrige. `registro.py` ya usa `tabla`, `registro_id` e `ip_origen`, pero login y logout no lo llaman (G2-36). |

## 7. Pendientes con otros grupos

- **Grupo 1:** ¿MariaDB local o servidor compartido? ¿Cuándo sube el script con datos semilla?
- **Grupos 3 y 5:** ¿necesitan un rol "autoridad" para autorizar programas?
- **Todos:** el código de rol es `administrador` o `admin`. Hay que alinearlo.
