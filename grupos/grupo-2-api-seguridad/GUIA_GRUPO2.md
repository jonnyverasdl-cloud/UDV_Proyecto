# Guía del Grupo 2: API y Seguridad

Coordinador: Daniel (dancobs) · Versión 2 · 10-oct-2026 · Estado actualizado al 02-nov-2026

**Cómo usar esta guía:** busca tu nombre en la sección 2 y mira la semana actual. Ahí está lo que te toca y la fecha de entrega.

---

## 1. Dónde estamos (estado al 02-nov)

**Retest No. 2 de QA (23 y 24-oct):** 34 PASS, 2 FAIL (G2-21 archivos y G2-31 paginación), 1 PARCIAL (G2-33 OpenAPI) y 1 PASS histórico con retest pendiente (G2-32). Lo que falta se explica en la sección 9. `pytest` en `grupo-2` (02-nov): **98 pasan, 0 fallan, 1 xfail y 1 xpass** (el xfail esperado es el `details` del 422; la contraseña de 8 a 64 al crear usuario ya pasa).

**Avance de esta semana (hasta el 01-nov):** Daniel dejó el bloqueo por intentos, el 422 con campos vacíos y la auditoría del correo inexistente; Randy subió la paginación de `GET /users` y `tests/test_users.py`; Edgar arregló `registro.py` y las pruebas de errores; Fulvio cerró `POST /files` y `GET /files/{id}` con control de autor y registro en la tabla `archivo` (28-oct); Robert dejó probada la conexión a la base y completó OpenAPI con `tests/test_openapi.py` (ejemplos al día con las respuestas del PM, 01-nov). Edgar dejó `set_actor_id()` en NULL (30-oct) y Fulvio agregó el acceso del admin a `GET /files/{id}` (31-oct). El PM respondió las dudas del grupo (01-nov): ver secciones 7 y 9. Randy subió el 02-nov (`9205344`) `creado_en` y `actualizado_en` en `users.py`, la IP en `fijar_actor` y la contraseña de 8 a 64 al crear usuarios. Robert comprobó G2-21 el 02-nov con una prueba temporal: un docente ajeno da 403, el dueño o un admin 200, un id que no existe 404 y sin token 401. Falta el retest de QA sobre G2-21, G2-31, G2-32 y G2-33.

**Leyenda:** ✅ Hecho y verificable en el repo · 🔵 Implementado, falta validación o retest de QA · 🟡 En proceso (falta algo concreto) · ⏳ Pendiente de implementar

| Estado | Qué | Quién |
|-|-|-|
| ✅ | Migración al repo oficial, rama `grupo-2` | Todos |
| ✅ | Esqueleto: `main.py`, `config.py`, `database.py`, `models.py`, `requirements.txt` | Robert |
| ✅ | `main.py` incluye los routers `auth`, `/me`, `users`, `roles` y `files` | Robert |
| ✅ | Conexión a la base del Grupo 1 (MySQL 8 con PyMySQL y `DATABASE_URL`): `database.py` (UTC y `fijar_actor`), `models.py` y `.env.example`. Probada con su `.env` en la base compartida: `probar_conexion()` devolvió `True` (27-oct) | Robert |
| 🔵 | Login (`POST /api/v1/auth/login`): consulta la base compartida, devuelve el JWT y guarda login y login fallido en `registro.py` | Daniel |
| 🔵 | `POST /auth/logout` y `GET /me`: funcionan con la base; el token cerrado con logout ya da 401 | Daniel |
| 🔵 | `obtener_usuario_actual()` lee al usuario desde la base y fija `@actor_id` para la auditoría | Daniel |
| 🔵 | Middleware (`auth_middleware.py`): ya usa `obtener_usuario_actual()`. Sin token da 401, el encabezado `usuario-actual` ya no sirve (401) y sin rol da 403 | Randy |
| 🔵 | `users.py` y `roles.py`: leen de la base y usan el rol `admin`; `GET /users/{id}` da 404 si no existe | Randy |
| 🟡 | Formato de errores (`error_handler.py`): 401, 403 y 404 responden bien (aviso del PM, 22-oct). Falta que `details` sea un objeto con un campo por llave (hoy en 422 sale `{"campos": [...]}`) y `{}` cuando no hay detalle, como confirmó el PM (01-nov); ajustar también `tests/test_errores.py` | Edgar |
| 🔵 | Pantalla de login (`frontend-login/`) | Fulvio |
| ✅ | Login con campos vacíos: `""` ya da 422 y la contraseña va de 8 a 64 caracteres (23-oct, G2-04) | Daniel |
| ✅ | `registro.py`: el login fallido con correo inexistente o vacío se guarda con `registro_id = 0` (corregido otra vez el 02-nov por Daniel: el NULL del Grupo 1 es solo para `actor_id`; `registro_id` es NOT NULL en `01_schema.sql`). Queda quitar las funciones que ya no se usan | Edgar |
| ✅ | `registro.py`: `set_actor_id()` ya no manda `@actor_id = 0`: manda NULL cuando no hay usuario (aviso del Grupo 1, 28-oct; corregido el 30-oct) | Edgar |
| ✅ | `users.py`: al crear y al editar un usuario `fijar_actor(db, actual.id, _ip(request))` ya pasa la IP (`request.client.host`), así que los triggers llenan `ip_origen` (02-nov, `9205344`) | Randy |
| 🔵 | Archivos (28-oct): `POST /files` ya no da 500 y guarda el archivo en la tabla `archivo` con SHA-256 y `autor_id`. `GET /files/{id}` usa `{id}`, da 404 si no existe y 403 si quien pide no es el dueño ni un admin (G2-21; admin agregado el 31-oct, `7ffa69c`). El PM confirmó (01-nov) que descargan el dueño o un admin y que el límite de 5 MB aplica solo a `/files`. Falta retest de QA y `tests/test_files.py` | Fulvio |
| ✅ | Bloqueo por intentos (5 fallos = 429 por 15 minutos): PASS en el retest (G2-34) | Daniel |
| 🔵 | Paginación en `GET /users` (`page`, `per_page`, `total`, `data`): ya la usa `users.py` (24-oct) y tiene pruebas. Falta retest de QA (G2-31) | Randy |
| 🔵 | Documentación OpenAPI: `main.py` completa 401, 403, 404, 409 y 422 con el formato común y ejemplos reales (objetos, no `string`). Al día con el PM (01-nov): `creado_en` y `actualizado_en` en ISO 8601, `details` como objeto, 403 en `GET /files/{id}` y `file_id` numérico en `POST /files`. El 02-nov las fechas del ejemplo pasaron a UTC con `Z`, igual que la API (Randy ya subió las fechas); para que coincida del todo, Edgar debe subir `details`. Falta retest de QA (G2-33) | Robert |
| ✅ | `pytest` completo en `grupo-2` (02-nov): **98 pasan, 0 fallan, 1 xfail y 1 xpass** | Edgar |

**Ojo:** el PM entregó una base compartida (MySQL en Railway). Los datos de acceso se piden al PM y van **solo en tu `.env`**, nunca en el repo ni en `.env.example`. Lo que se borra ahí lo ven los demás grupos. El Grupo 1 ya subió su script SQL a la rama `grupo-1` (`grupos/grupo-1-base-de-datos/Docs/sql/`: `01_schema.sql` y `02_seed.sql`) y se puede montar la base local con `python -m g1_bd crear`. Login, sesión, middleware, `users.py` y `roles.py` ya usan la base. El JSON de prueba ya se borró (02-nov): `auth.py` ya no lo carga y la carpeta `datos_prueba/` no existe.

---

## 2. Quién hace qué, por semana

**Corte de cada semana: martes a las 23:59.** Lo que no esté subido a `grupo-2` ese día se toma como no entregado. La semana 3 (corte martes 27-oct) ya pasó; lo que sigue es la **semana 4, con corte el martes 03-nov**.

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
- `routers/auth.py` → límite de intentos: antes de revisar la contraseña llamar a `esta_bloqueado()` (5 fallos = 15 minutos). El código de error del bloqueo se confirma con el PM.
  *Usa `registro.py` de Edgar y las columnas `intentos_fallidos` y `bloqueado_hasta` de `models.py`.*
- `routers/auth.py` → `min_length=1` en los campos del login para que `""` dé 422, no 401 (G2-04).
- `routers/auth.py` → contraseña de 8 a 64 caracteres.
  *Los números salen del `.env`.*
- ✅ `routers/auth.py` → se quitó la carga del JSON de prueba y la carpeta `datos_prueba/` (02-nov).

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
- `routers/users.py` → la lista de usuarios usa la paginación (`page`, `per_page`, `total`, `data`).
  *Usa `paginacion.py` de Edgar.*
- `routers/users.py` → documentar 401, 403 y 409 en `POST /users` y el 401 y 403 en `GET /users` (`responses=`); el ejemplo del 201 debe ser un objeto, no un string.
- `GET /users/{id}` con 404 ya está hecho: quedar atento al retest de QA.
- ✅ `routers/users.py` → incluir `creado_en` y `actualizado_en` en las respuestas de usuarios, solo de lectura, en ISO 8601 con zona horaria (G2-32). Lo confirmó el PM el 01-nov. Hecho el 02-nov (`9205344`): salen en UTC con `Z` (por ejemplo `2026-10-29T21:30:00Z`), igual que la base. Si el PM prefiere otra zona, se ajusta `_fecha()` en `users.py`.
- ✅ `routers/users.py` → `fijar_actor(db, actual.id, _ip(request))` ya pasa `request.client.host` como tercer parámetro (aviso del Grupo 1). Hecho el 02-nov (`9205344`).

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
- `utils/registro.py` → que el login fallido con correo inexistente o vacío también se guarde (`registro_id` no puede ir NULL en la base). Con eso `pytest` queda en 34 de 34. *(El cambio del 30-oct volvió a dejar `registro_id` en NULL: corregir, hoy falla una prueba.)*
- `utils/registro.py` → `set_actor_id()` (línea 61) manda `@actor_id = 0` sin usuario; el Grupo 1 pide NULL o usar `fijar_actor()` (28-oct). Hecho el 30-oct: manda NULL.
- `middleware/error_handler.py` → el PM confirmó (01-nov) que `details` es un objeto con un campo por llave (por ejemplo `{"correo": "Formato de correo inválido"}`) y `{}` cuando no hay detalle, nunca null; revisar que 401, 403, 404, 409 y 422 salgan con el formato común.

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
- `routers/files.py` → corregir el 500 de `POST /files` con token válido (`usuario_actual` es un `Usuario`, no un diccionario).
- `routers/files.py` → `GET /api/v1/files/{id}`: que el parámetro de la función se llame igual que el de la ruta (hoy da 422), descarga solo con token y solo para el autor o un admin; 404 si no existe.
  *Usa el middleware de Randy.*
- `routers/files.py` → registrar el archivo en la tabla `archivo` y guardar con nombre aleatorio sin salir de la carpeta (G2-22).
  *(28-oct: subido a `grupo-2`. 31-oct: el admin también descarga, como confirmó el PM el 01-nov. Falta el retest de QA.)*

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

**Semana 3 · martes 27-oct** (adelantada: hecha el 22-oct; conexión probada con su `.env` el 27-oct)
- `.env.example` → formato de `DATABASE_URL` para las tres opciones (Docker, XAMPP y base compartida), sin claves reales.
- `requirements.txt` → sin cambios: ya trae `PyMySQL` y `cryptography`; se comprobó que instala desde cero.
- `database.py` → conexión a MySQL 8: cada conexión nueva queda en UTC y `fijar_actor(db, actor_id, ip)` llena `@actor_id` e `@ip_origen` para los triggers del Grupo 1. Las variables se limpian al devolver la conexión al pool.
- `models.py` → `auditoria.detalle` guarda JSON válido (el Grupo 1 lo exige con `JSON_VALID`).
  *Depende del script del Grupo 1 (ya subido a `grupo-1`). Daniel y Randy llaman a `fijar_actor`; Edgar usa `registrar_accion`.*
- ✅ Probar la conexión real con tu `.env`: `probar_conexion()` devolvió `True` (27-oct).
- (27 y 28-oct) `main.py` completa OpenAPI (401, 403, 404, 409, 422 y ejemplos) y `tests/test_openapi.py` lo verifica (G2-33).

**Semana 4 · martes 03-nov** (adelantada: hecha el 22-oct; ejemplos de OpenAPI al día con el PM el 01-nov)
- `README.md` → títulos y tablas corregidos, nueva sección «Auditoría: quién hizo el cambio» y la regla de descarga de archivos (01-nov).
- `main.py` y `tests/test_openapi.py` → ejemplos de OpenAPI al día con el PM (fechas, `details` como objeto, 403 en `GET /files/{id}` y `file_id` numérico).
  *Randy y Edgar deben subir su parte para que Swagger coincida con la API.*
- `tests/conftest.py` → sin cambios: `pytest` corre con SQLite temporal y nunca toca la base compartida.

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
    ├── routers/           ← auth.py (Daniel), users.py y roles.py (Randy), files.py (Fulvio)
    ├── middleware/        ← auth_middleware.py (Randy), error_handler.py (Edgar)
    └── utils/             ← paginacion.py y registro.py (Edgar)
```

Para correr la API: `http://127.0.0.1:8000/api/v1/docs`

---

## 7. Pendientes con otros grupos

- **Grupo 1:** ¿MariaDB local o servidor compartido? ¿Cuándo sube el script con datos semilla? (Ya lo respondió el Grupo 1)
- **Grupo 1 (28-oct):** el PM carga y actualiza la base de Railway (README §5), así que no hay que correr la migración. La versión se ve con `SELECT * FROM schema_migracion;`: si aparece 1.2.0 está al día; si no, se avisa al PM. También avisaron lo de `set_actor_id()` en `registro.py` (ver sección 1). Falta preguntarles el código y los permisos del rol de autoridad.
- **Grupo 5 (28-oct):** los PDF de las versiones autorizadas se guardan con nuestro módulo de archivos (hoy el límite es de 5 MB); ellos guardan `pdf_hash` en `programa_version`. Resuelto por el PM (01-nov): los PDF de G5 no pasan por `/files`; los genera y entrega G5 en `GET /program-versions/{id}/pdf` con sus propias reglas, y el límite de 5 MB aplica solo a lo que se sube por `/files`. En `/files` descarga el dueño o un admin (otro rol, 403). Preguntaron si exponemos el usuario en `request.state.user`: hoy se usa `Depends(obtener_usuario_actual)`, que devuelve el usuario con sus roles. Falta confirmar el código del rol de autoridad.
- **Grupo 3:** ¿necesita un rol "autoridad" para autorizar programas?
- **Todos:** el código de rol es `admin` (confirmado por el PM el 22-oct). Ya quedó en `users.py` y `roles.py`.

---

## 8. Pendientes del QA (Update No. 1 · 17-oct · estado al 23-oct)

Allison Espaderos (QA) entregó el primer informe y creó las tareas en el Planner (plan «2. Api y Seguridad - Allison»). El detalle por persona está en `PENDIENTES_QA.md` (misma carpeta). Las tarjetas del Planner muestran fecha **21/10**. Según Allison, el texto de cada punto se cortaba en el Planner (tiene un límite de caracteres por línea), así que lo actualiza ahí y también lo pasa por el chat. Ella revisa los puntos que se marquen como completados en el Planner, y esa lista puede cambiar entre el jueves y el viernes.

### 8.1 Tareas del Planner (texto completo)

*Los estados de esta tabla son del 23-oct. El estado vigente, con los avisos del PM, está en la sección 9.*

Las tres tareas están «No iniciado», con la prioridad en el nombre, etiqueta «Grupo 2» y **sin responsable asignado**: son de todo el grupo.

| Prioridad | Punto del Planner | Escenarios | Quién lo resuelve | Estado al 23-oct |
|-|-|-|-|-|
| 🔴 Alta | 1. Autenticación y autorización JWT: integrar la validación JWT en los endpoints protegidos, eliminar la dependencia del encabezado `usuario-actual` y verificar respuestas HTTP 401 y 403 según corresponda | G2-06, 08, 09, 10, 37 y 38 | Randy (middleware); Daniel (`verificar_token`, `obtener_usuario_actual`) | 🔵 Hecho (22-oct): el middleware usa el JWT y la base. Listo para retest |
| 🔴 Alta | 2. Cierre de sesión: implementar el endpoint de logout y asegurar que los tokens revocados no puedan seguir utilizándose | G2-05 | Daniel | 🔵 Hecho: el token revocado da 401. Listo para retest |
| 🔴 Alta | 3. Control de acceso a recursos: verificar las restricciones de acceso por usuario y rol para evitar consultas o modificaciones no autorizadas | G2-17 | Randy; Fulvio (archivos) | 🟡 Usuarios y roles listos para retest; archivos no (`POST /files` da 500 y `GET /files/{id}` da 422) |
| 🟡 Media | 1. Consulta del usuario autenticado (G2-07): implementar el endpoint `/me` para recuperar la identidad y los roles del usuario autenticado | G2-07 | Daniel | 🔵 Listo para retest (200 con JWT válido, 401 sin token) |
| 🟡 Media | 2. Consulta individual de usuarios (G2-12): revisar la disponibilidad del endpoint GET por ID y devolver HTTP 404 cuando el usuario no exista | G2-12 (y G2-11) | Randy | 🔵 Lee de la base y da 404. Listo para retest |
| 🟡 Media | 3. Manejo de recursos inexistentes (G2-26): revisar las rutas requeridas para garantizar respuestas HTTP apropiadas cuando un recurso no exista | G2-26 | Randy; Fulvio (`/files/{id}`) | 🟡 Usuarios sí; `GET /files/{id}` todavía no (da 422) |
| 🟡 Media | 4. Documentación OpenAPI/Swagger (G2-33): actualizar la documentación de los endpoints, sus esquemas y las respuestas HTTP 401, 409 y demás códigos aplicables | G2-33 | Todos; Robert revisa al final | ⏳ Pendiente: login ya documenta 401 y 422; falta `POST /users` (401, 403, 409) y `files` |
| ⚪ Baja | 1. Paginación de usuarios (G2-31): revisar la implementación de paginación en el listado de usuarios | G2-31 | Randy; Edgar (`paginacion.py`) | ⏳ Pendiente |
| ⚪ Baja | 2. Bloqueo por intentos fallidos (G2-34): integrar el bloqueo de 15 minutos después de cinco intentos fallidos de autenticación | G2-34 | Daniel; Edgar (`registro.py`) | ⏳ Pendiente: el login no llama a `esta_bloqueado()` |
| ⚪ Baja | 3. Registro de auditoría (G2-36): integrar las funciones de auditoría con las operaciones correspondientes, incluyendo intentos fallidos de autenticación y acciones sensibles | G2-36 | Daniel y Randy; Edgar (`registro.py`) | 🟡 Login, login fallido y logout ya lo llaman; falta el correo inexistente o vacío |

Notas del QA: en **Alta**, «las correcciones deben estar disponibles para retest y los escenarios afectados deben poder verificarse nuevamente por QA». En **Media**, «las funcionalidades pendientes deben quedar disponibles y documentadas para permitir la ejecución de las pruebas». **Baja** no trae notas.

**Qué marcar en el Planner:** solo lo que ya esté subido a `grupo-2` y probado. Hoy se pueden marcar, para el retest de QA, JWT en endpoints protegidos (G2-06, 08, 09, 10, 37, 38), logout (G2-05), `/me` (G2-07) y `GET /users/{id}` (G2-12). Control de acceso (G2-17) y recursos inexistentes (G2-26) quedan parciales por archivos. Paginación, bloqueo, OpenAPI y auditoría siguen pendientes.

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

### 8.5 Respuestas y avisos del PM

| Tema | Decisión del PM |
|-|-|
| Base compartida | Las pruebas automáticas siguen con SQLite o MySQL local en Docker (como está en `conftest.py`). La base compartida es para integración y pruebas manuales con QA. Se puede escribir en `sesion_token` y `auditoria` con el usuario de G2 |
| Auditoría | En `auditoria` se escriben a mano solo los eventos de acceso: login exitoso, login fallido y logout. Los cambios de datos ya los registran los triggers de G1 (por eso hace falta `@actor_id`) |
| G2-04: login con campos vacíos | **422** con detalle por campo. El 401 queda solo para credenciales incorrectas (`CONTRATO_COMUN` §1) |
| Formato de error | Se queda el formato actual de G2. El PM actualiza el `CONTRATO_COMUN` para documentarlo. Pidió que `details` sea una lista de objetos por campo (`field`, `code`, `message`). **Confirmado por el PM (01-nov):** `details` es un objeto (diccionario) con un campo por llave, como el `CONTRATO_COMUN`, y `{}` si no hay detalle; la lista queda sin efecto. Hoy `error_handler.py` devuelve `{"campos": [...]}`: Edgar lo ajusta |
| Rol administrador | Confirmado: `admin`. Los códigos oficiales son los de G1 |
| Fechas | Correcciones listas para el PR del **jueves 22** y retest de QA el **viernes 23** |
| `.env` | No se sube nunca. Cada quien lo crea en `grupos/grupo-2-api-seguridad/`, con `DATABASE_URL` real. Al repo solo va `.env.example` con el formato, sin clave. La clave se comparte solo en privado |

### 8.6 Antes del PR del jueves 22 (aviso del PM, 22-oct) y cómo quedó el 23-oct

El 22-oct el PM contó 28 pruebas que pasan y 4 que fallan (antes 15). Lo que se pidió y cómo está en `grupo-2` hoy:

1. `registro.py` (Edgar): quedó 1 falla de 4. `pytest` completo: **33 pasan y 1 falla** (`test_login_fallido_queda_en_auditoria`), porque con un correo inexistente o vacío `registro_id` queda NULL y la base lo rechaza.
2. `auth_middleware.py` (Randy): ya no lee el JSON. Usa `obtener_usuario_actual()` de `auth.py`.
3. `users.py` y `roles.py` (Randy): ya usan el rol `admin` y leen de la base.

Retest de QA: **viernes 23-oct**. Prioridad de Allison: G2-10 (suplantación por encabezado), G2-04 (422), G2-07 (`/me`) y login con las cuentas `qa.*`.

### 8.7 Semana 3 (martes 27-oct) con escenarios

Misma idea que la 8.2. Las tareas son las de la sección 2; aquí se les pone el escenario de QA que cubren.

| Persona | Tarea | Escenarios QA |
|-|-|-|
| Daniel | Límite de intentos: 5 fallos = 15 minutos bloqueado | G2-34 |
| Daniel | `min_length=1` en el login para que `""` dé 422 | G2-04 |
| Daniel | Contraseña de 8 a 64 caracteres | G2-13, 14, 28 |
| Randy | La lista de usuarios usa la paginación | G2-31 |
| Randy | Documentar 401, 403 y 409 en `POST /users` y el ejemplo del 201 | G2-33 |
| Edgar | `registro.py`: guardar también el login fallido con correo inexistente o vacío | G2-36 |
| Edgar | `error_handler.py`: `details` como objeto (confirmado por el PM, 01-nov) y repetir 401, 403, 404, 409 y 422 | G2-23, 28, 29, 30 |
| Fulvio | Corregir `POST /files` (500) y `GET /files/{id}` (422): descarga solo con token y solo el autor o un admin | G2-17, 18, 21, 22 |
| Fulvio | Registrar el archivo en la tabla `archivo`; probar tipo no permitido y tamaño con QA | G2-19, 20, 22 |
| Robert | Conexión a la base: `.env.example`, `requirements.txt`, `database.py` (hecho el 22-oct; Ya probó con el archivo `.env` (Ese archivo no se sube en el repositorio)) | G2-01, 32, 35 |
| Robert | `models.py` y `fijar_actor` para la auditoría (hecho el 22-oct) | G2-34, 36 |

### 8.8 Semana 4 (martes 03-nov) con escenarios

| Persona | Tarea | Escenarios QA |
|-|-|-|
| Daniel | `tests/test_auth.py`: login bien, login mal (401), logout y `/me` sin token (401) | G2-01, 02, 03, 05, 06, 07 |
| Randy | `tests/test_users.py`: 401 sin token, 403 sin permiso, 404 y 409 por correo repetido | G2-06, 08, 09, 12, 27 |
| Edgar | `tests/test_errores.py`: formato de error y paginación | G2-29, 30, 31 |
| Fulvio | `tests/test_files.py`: tipo no permitido, archivo muy grande y descarga sin token (401) | G2-19, 20, 21 |
| Robert | `README.md` (hecho el 22-oct) y `tests/conftest.py`; revisión de `/api/v1/docs` (al día con el PM el 01-nov) | G2-33, 35 |

### 8.9 Semana 5 (martes 10-nov) con escenarios

En la sección 2 solo Daniel tiene tarea esta semana. Para que cada quien sepa qué revisar, esta es la propuesta (los de las personas 1 a 4 los confirma Daniel):

| Persona | Qué toca | Escenarios QA |
|-|-|-|
| Daniel | Revisar los escenarios de QA (la lista de Allison tiene 38, no 36) y abrir el PR `grupo-2 → main` | G2-01 a G2-38 |
| Randy | Repetir y corregir lo que QA devuelva de usuarios, roles y middleware | G2-06, 08, 09, 10, 11, 12, 17, 26, 31, 37, 38 |
| Edgar | Repetir y corregir lo que QA devuelva de errores, paginación y registro | G2-23, 24, 28, 29, 30, 31, 36 |
| Fulvio | Repetir y corregir lo que QA devuelva de archivos | G2-18, 19, 20, 21, 22 |
| Robert | Revisión final de OpenAPI (`/api/v1/docs` contra lo que responde la API) y del README; confirmar que no hay claves en el repo | G2-33, 35 |

*Nota: las fechas de las semanas 3, 4 y 5 son martes 27-oct, 03-nov y 10-nov (las de la sección 2).*

---

## 9. Retest No. 2 de QA (23 y 24-oct) y qué falta

Fuentes: Update No. 2 e Informe de Retest No. 2 de Allison (el detalle de los 38 escenarios está en `PENDIENTES_QA.md`). Resultado: 34 PASS, 2 FAIL, 1 PARCIAL, 1 PASS histórico con retest pendiente. Los mensajes del PM (24-oct) y de Allison coinciden con esto. Cada quien toca solo sus archivos.

| Prioridad | Escenario | Qué pasa | Quién | Archivo | Estado al 02-nov |
|-|-|-|-|-|-|
| 🔴 Alta (crítica) | G2-21 | Un docente descarga el archivo de un admin (HTTP 200, posible IDOR). El PM pide 403 o 404. | Fulvio | `routers/files.py` | 🔵 Subido el 28-oct (commit `6982c15`): `GET /files/{id}` pide token, da 404 si no existe y 403 si no es el dueño ni un admin; `POST /files` guarda en la tabla `archivo`. 31-oct (`7ffa69c`): el admin también descarga, como confirmó el PM (01-nov). Falta retest, `tests/test_files.py` y el PR a `main`, donde el PM activa `/files` |
| ⚪ Baja | G2-36 | PASS del PM y del QA en el retest. El aviso anterior del PM (correo inexistente con `registro_id` en NULL) ya está corregido: se guarda `registro_id = 0` y el correo va en `detalle`; el QA lo confirmó con un LOGIN_FALLIDO en la tabla `auditoria`. Antes se avisó que el login fallido se guardaba **dos veces** (`auth.py` y `registro.py`). | Daniel y Edgar | `routers/auth.py`, `utils/registro.py` | 🟡 PASS de QA, pero hoy falla una prueba: tras el cambio del 30-oct el correo inexistente guarda `registro_id` NULL y la base lo rechaza (Edgar). Queda revisar que el login fallido quede una sola vez antes del PR a `main` |
| 🟡 Media | G2-33 | Faltaban 409, 403, ejemplos con objetos y el 422 real. | Robert | `main.py` | 🔵 Hecho (27 y 28-oct): `POST /users`, `GET /me` y `GET /users` documentan sus códigos con ejemplos reales y `tests/test_openapi.py` lo verifica. `files` ya usa `{id}`. Ejemplos al día con el PM el 01-nov (fechas, `details` como objeto, 403 en archivos). Falta retest |
| ⚪ Baja | G2-31 | `GET /users` devolvía un arreglo sin paginar. | Randy | `routers/users.py` | 🔵 Ya pagina (24-oct) con pruebas en `tests/test_users.py`. Falta retest |
| ⚪ Baja | G2-32 | Las respuestas de usuarios ya no traen `creado_en` ni `actualizado_en`. | Randy, con el PM | `routers/users.py` | 🔵 Subido el 02-nov (`9205344`): `creado_en` y `actualizado_en` salen de solo lectura, en ISO 8601 y en UTC con `Z` (por ejemplo `2026-10-29T21:30:00Z`), como pidió el PM (01-nov). Falta retest |
| ⚪ Baja | G2-34 | Bloqueo de 15 min. | Daniel | `routers/auth.py` | ✅ PASS |
| Limpieza | PM | `auth.py` cargaba `usuarios_prueba.json` y nadie lo usaba. | Daniel | `routers/auth.py` | ✅ Hecho (02-nov): se quitó la carga y la carpeta `datos_prueba/` |

### 9.1 Avisos del PM por prioridad y qué se puede probar

| Prioridad | Escenario | Aviso del PM (retest del 23-oct) | Qué probar antes de avisar | ¿Se puede comentar en el Planner? |
|-|-|-|-|-|
| 🔴 Alta | G2-21 | Un docente descargó con HTTP 200 un PDF cargado por un admin: `GET /files/{id}` pedía token pero no revisaba al dueño. Debe dar 403 o 404 sin revelar el archivo | Subir un PDF con un usuario y copiar el `file_id`; pedir `GET /files/{id}` con otro usuario (debe dar **403**), con el dueño o un admin (**200**), con un id que no existe (**404**) y sin token (**401**) | Sí, como «corregido, listo para retest» (commit `6982c15`, 28-oct). No marcarlo completado hasta que Allison repita G2-21 |
| 🟡 Media | G2-07, G2-12, G2-26 | PASS los tres (`/me`, consulta individual y recursos inexistentes) | Nada más | Ya están cerrados. Se puede comentar «PASS confirmado por el PM» |
| 🟡 Media | G2-33 | PARCIAL: Swagger no coincidía con `POST /users`, `GET /me` y `GET /users` (faltaban códigos HTTP y los ejemplos JSON eran incorrectos) | En `/api/v1/docs` revisar `POST /users` (201, 401, 403, 409, 422), `GET /me` (200 con objeto y 401), `GET /users` (200 con `page`, `per_page`, `total`, `data`, 401 y 403) y `files` con `{id}`; correr `pytest tests/test_openapi.py` | Sí, listo para retest (Robert, 27 y 28-oct) |
| 🟡 Media | G2-04, G2-18 | Observaciones del Informe No. 2: la API daba 401 con campos vacíos (el PM pidió 422) y Swagger de `files` pedía `file_id` en query en vez de `{id}` | Con campos vacíos (`""`) revisar que dé 422; en `/api/v1/docs` ver que `GET /files/{id}` use `{id}` en la ruta | Sí, como «corregido, listo para repetir» |
| ⚪ Baja | G2-34, G2-36 | PASS los dos (bloqueo temporal y registro de auditoría) | Nada más; solo confirmar antes del PR que el login fallido se guarda una vez | Ya están cerrados |
| ⚪ Baja | G2-31 | FAIL: `GET /users` no paginaba. Debe devolver `page`, `per_page`, `total` y `data` | `GET /users?page=1&per_page=5` con admin: revisar los cuatro campos y el máximo de 100 por página | Sí, listo para retest (Randy, 24-oct, con `tests/test_users.py`) |
| ⚪ Baja | G2-32 | PASS histórico, retest pendiente: las consultas de usuarios ya no traen `creado_en` ni `actualizado_en` | Revisar que `GET /users` y `GET /users/{id}` traigan `creado_en` y `actualizado_en` en ISO 8601 con zona horaria (PM, 01-nov) | Sí, listo para retest (Randy, 02-nov, `9205344`) |

**Sobre el PR a `main`:** G2 ya entró a `main` (27-oct, con 93 pruebas en verde) sin la ruta `/files`. Falta un PR nuevo, que abre solo Daniel, con la corrección de G2-21, `creado_en` y `actualizado_en`, `details` como objeto y el JSON de prueba borrado; cuando entre, el PM activa `/files`. Antes: `git fetch` y merge de `origin/main` en `grupo-2`, dejar las versiones oficiales de `requirements.txt` (ya coinciden) y correr `pytest`.

**Semana 4 de Robert:** hecha (`README.md`, `tests/conftest.py`, `tests/test_openapi.py` y los ejemplos de `main.py`, al día el 01-nov). La semana 5 (revisión final de OpenAPI y README) espera a que Edgar suba `details` y al retest de QA.
