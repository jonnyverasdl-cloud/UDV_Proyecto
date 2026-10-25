# Guía del Grupo 2: API y Seguridad

Coordinador: Daniel (dancobs) · Versión 2 · 10-oct-2026 · Estado actualizado al 23-oct-2026

**Cómo usar esta guía:** busca tu nombre en la sección 2 y mira la semana actual. Ahí está lo que te toca y la fecha de entrega.

---

## 1. Dónde estamos (estado al 23-oct)

**Hoy, viernes 23-oct, QA (Allison) repite las pruebas** sobre lo que se subió a `grupo-2` para el PR del jueves. Revisado el 23-oct contra la rama `grupo-2`: `pytest` completo pasa **33** y falla **1**.

**Leyenda:** ✅ Hecho y verificable en el repo · 🔵 Implementado, falta validación o retest de QA · 🟡 En proceso (falta algo concreto) · ⏳ Pendiente de implementar

| Estado | Qué | Quién |
|-|-|-|
| ✅ | Migración al repo oficial, rama `grupo-2` | Todos |
| ✅ | Esqueleto: `main.py`, `config.py`, `database.py`, `models.py`, `requirements.txt` | Robert |
| ✅ | `main.py` incluye los routers `auth`, `/me`, `users`, `roles` y `files` | Robert |
| 🔵 | Conexión a la base del Grupo 1 (MySQL 8 con PyMySQL y `DATABASE_URL`): `database.py` (UTC y `fijar_actor`), `models.py` y `.env.example`. Falta probar con tu `.env` en la base compartida | Robert |
| 🔵 | Login (`POST /api/v1/auth/login`): consulta la base compartida, devuelve el JWT y guarda login y login fallido en `registro.py` | Daniel |
| 🔵 | `POST /auth/logout` y `GET /me`: funcionan con la base; el token cerrado con logout ya da 401 | Daniel |
| 🔵 | `obtener_usuario_actual()` lee al usuario desde la base y fija `@actor_id` para la auditoría | Daniel |
| 🔵 | Middleware (`auth_middleware.py`): ya usa `obtener_usuario_actual()`. Sin token da 401, el encabezado `usuario-actual` ya no sirve (401) y sin rol da 403 | Randy |
| 🔵 | `users.py` y `roles.py`: leen de la base y usan el rol `admin`; `GET /users/{id}` da 404 si no existe | Randy |
| 🔵 | Formato de errores (`error_handler.py`): 401, 403 y 404 responden bien (aviso del PM, 22-oct) | Edgar |
| 🔵 | Pantalla de login (`frontend-login/`) | Fulvio |
| 🟡 | Login con campos vacíos: si el campo falta da 422, pero con `""` todavía da 401. Falta `min_length=1` en `LoginRequest` (G2-04) | Daniel |
| 🟡 | `registro.py`: de 4 pruebas fallando quedó 1 (`test_login_fallido_queda_en_auditoria`). Con un correo inexistente o vacío, `registro_id` queda NULL y la base lo rechaza | Edgar |
| 🟡 | Archivos: `POST /files` ya exige token, pero con un token válido responde **500** (`usuario_actual["correo"]`: el usuario ya no es un diccionario). `GET /files/{id}` da **422** porque la ruta dice `{id}` y la función espera `file_id`. Faltan: registrar en la tabla `archivo`, dejar descargar solo al autor o a un admin y `tests/test_files.py` | Fulvio |
| ⏳ | Bloqueo por intentos (5 fallos = 15 minutos): el login no llama a `esta_bloqueado()` y siempre da 401 | Daniel |
| ⏳ | Paginación en `GET /users` (`paginacion.py` existe, `users.py` no la usa) | Randy |
| ⏳ | Documentación OpenAPI: `POST /users` solo documenta 201 y 422 (faltan 401, 403 y 409); `GET /users` solo 200; `files` solo 200 y 422 | Randy y Fulvio |
| 🟡 | `pytest` completo: **33 pasan y 1 falla** (la de `registro.py`). El 22-oct el PM contó 28 y 4 fallas | Edgar |

**Ojo:** el PM entregó una base compartida (MySQL en Railway). Los datos de acceso se piden al PM y van **solo en tu `.env`**, nunca en el repo ni en `.env.example`. Lo que se borra ahí lo ven los demás grupos. El Grupo 1 ya subió su script SQL a la rama `grupo-1` (`grupos/grupo-1-base-de-datos/Docs/sql/`: `01_schema.sql` y `02_seed.sql`) y se puede montar la base local con `python -m g1_bd crear`. Login, sesión, middleware, `users.py` y `roles.py` ya usan la base. El JSON de prueba (`g2_api/datos_prueba/usuarios_prueba.json`) ya no autentica a nadie, pero `auth.py` todavía lo carga al arrancar sin usarlo; se quita cuando el PM confirme que se puede borrar.

---

## 2. Quién hace qué, por semana

**Corte de cada semana: martes a las 23:59.** Lo que no esté subido a `grupo-2` ese día se toma como no entregado. Hoy (viernes 23-oct) es el retest de QA; lo que sigue es la **semana 3, con corte el martes 27-oct**.

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
- `routers/auth.py` → quitar la carga del JSON de prueba cuando el PM confirme.

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
- `utils/registro.py` → que el login fallido con correo inexistente o vacío también se guarde (`registro_id` no puede ir NULL en la base). Con eso `pytest` queda en 34 de 34.
- `middleware/error_handler.py` → confirmar con el PM si `details` queda como lista de objetos (`field`, `code`, `message`) o como diccionario, y revisar que 401, 403, 404, 409 y 422 salgan con el formato común.

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

**Semana 3 · martes 27-oct** (adelantada: hecha el 22-oct, 🔵 falta probar con tu `.env`)
- `.env.example` → formato de `DATABASE_URL` para las tres opciones (Docker, XAMPP y base compartida), sin claves reales.
- `requirements.txt` → sin cambios: ya trae `PyMySQL` y `cryptography`; se comprobó que instala desde cero.
- `database.py` → conexión a MySQL 8: cada conexión nueva queda en UTC y `fijar_actor(db, actor_id, ip)` llena `@actor_id` e `@ip_origen` para los triggers del Grupo 1. Las variables se limpian al devolver la conexión al pool.
- `models.py` → `auditoria.detalle` guarda JSON válido (el Grupo 1 lo exige con `JSON_VALID`).
  *Depende del script del Grupo 1 (ya subido a `grupo-1`). Daniel y Randy llaman a `fijar_actor`; Edgar usa `registrar_accion`.*
- Probar la conexión real con tu `.env` y avisar al grupo si algo falla.

**Semana 4 · martes 03-nov** (adelantada: hecha el 22-oct)
- `README.md` → títulos y tablas corregidos y nueva sección «Auditoría: quién hizo el cambio».
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
    ├── datos_prueba/      ← JSON temporal hasta tener MariaDB
    ├── routers/           ← auth.py (Daniel), users.py y roles.py (Randy), files.py (Fulvio)
    ├── middleware/        ← auth_middleware.py (Randy), error_handler.py (Edgar)
    └── utils/             ← paginacion.py y registro.py (Edgar)
```

Para correr la API: `http://127.0.0.1:8000/api/v1/docs`

---

## 7. Pendientes con otros grupos

- **Grupo 1:** ¿MariaDB local o servidor compartido? ¿Cuándo sube el script con datos semilla? (Ya lo respondió el Grupo 1)
- **Grupos 3 y 5:** ¿necesitan un rol "autoridad" para autorizar programas?
- **Todos:** el código de rol es `admin` (confirmado por el PM el 22-oct). Ya quedó en `users.py` y `roles.py`.

---

## 8. Pendientes del QA (Update No. 1 · 17-oct · estado al 23-oct)

Allison Espaderos (QA) entregó el primer informe y creó las tareas en el Planner (plan «2. Api y Seguridad - Allison»). El detalle por persona está en `PENDIENTES_QA.md` (misma carpeta). Las tarjetas del Planner muestran fecha **21/10**. Según Allison, el texto de cada punto se cortaba en el Planner (tiene un límite de caracteres por línea), así que lo actualiza ahí y también lo pasa por el chat. Ella revisa los puntos que se marquen como completados en el Planner, y esa lista puede cambiar entre el jueves y el viernes.

### 8.1 Tareas del Planner (texto completo)

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
| Formato de error | Se queda el formato actual de G2. El PM actualiza el `CONTRATO_COMUN` para documentarlo. Pidió que `details` sea una lista de objetos por campo (`field`, `code`, `message`). **Por confirmar con el PM:** hoy `error_handler.py` devuelve `details` como diccionario (`{"campos": {...}}`) |
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
| Edgar | `error_handler.py`: confirmar `details` con el PM y repetir 401, 403, 404, 409 y 422 | G2-23, 28, 29, 30 |
| Fulvio | Corregir `POST /files` (500) y `GET /files/{id}` (422): descarga solo con token y solo el autor o un admin | G2-17, 18, 21, 22 |
| Fulvio | Registrar el archivo en la tabla `archivo`; probar tipo no permitido y tamaño con QA | G2-19, 20, 22 |
| Robert | Conexión a la base: `.env.example`, `requirements.txt`, `database.py` (hecho el 22-oct; falta probar con tu `.env`) | G2-01, 32, 35 |
| Robert | `models.py` y `fijar_actor` para la auditoría (hecho el 22-oct) | G2-34, 36 |

### 8.8 Semana 4 (martes 03-nov) con escenarios

| Persona | Tarea | Escenarios QA |
|-|-|-|
| Daniel | `tests/test_auth.py`: login bien, login mal (401), logout y `/me` sin token (401) | G2-01, 02, 03, 05, 06, 07 |
| Randy | `tests/test_users.py`: 401 sin token, 403 sin permiso, 404 y 409 por correo repetido | G2-06, 08, 09, 12, 27 |
| Edgar | `tests/test_errores.py`: formato de error y paginación | G2-29, 30, 31 |
| Fulvio | `tests/test_files.py`: tipo no permitido, archivo muy grande y descarga sin token (401) | G2-19, 20, 21 |
| Robert | `README.md` (hecho el 22-oct) y `tests/conftest.py`; revisión de `/api/v1/docs` | G2-33, 35 |

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
