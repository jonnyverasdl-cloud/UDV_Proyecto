# Pendientes del QA — Grupo 2 (Update No. 1 · 17-oct-2026 · estado al 23-oct-2026)

Resumen del informe de Allison Espaderos (QA) y quién corrige cada cosa. Cada quien toca **solo sus archivos**. Los números G2-xx son los escenarios del plan de QA.

Prioridad: **Alta** → **Media** → **Baja**. El Planner de Allison tiene tres tareas (Alta, Media y Baja) con puntos por escenario; están sin responsable y con fecha 21/10. El detalle está en `GUIA_GRUPO2.md`, sección 8.

## Lo más urgente (crítico)

El middleware de usuarios y roles todavía lee el encabezado `usuario-actual` y una lista JSON temporal, en vez del JWT. Por eso cualquiera puede hacerse pasar por administrador (G2-10) y el login real no sirve para entrar a `/users` ni `/roles`. Esto bloquea G2-06, 08, 09, 17, 37 y 38.

**Cómo leer los estados:** ✅ Cumple (PASS de QA) · 🔵 Implementado, pendiente de validación o retest de QA · 🟡 En proceso · ⏳ Pendiente de implementar.

## Estado al 23-oct

- **Aviso del PM (22-oct):** G2 arregló el manejador de errores y los 401, 403 y 404 ya responden bien. Daniel agregó `obtener_usuario_actual()` desde la base, con `@actor_id` para la auditoría. El PM contó 28 pruebas que pasan y 4 que fallan (en la mañana fallaban 15).
- **Retest de QA: viernes 23-oct**, después del PR del jueves. Prioridad: G2-10 (suplantación por header), G2-04 (422), G2-07 (`/me`) y login con las cuentas `qa.*`.
- **Lo que se pidió antes del PR del jueves y cómo está en `grupo-2` (revisado el 23-oct):**
  1. `registro.py` (Edgar): de 4 pruebas fallando quedó 1. `pytest` completo: **33 pasan y 1 falla** (`test_login_fallido_queda_en_auditoria`). Falla porque, cuando el correo no existe o viene vacío, el login fallido intenta guardar `registro_id` en NULL y la base lo rechaza (NOT NULL), así que ese intento no queda registrado.
  2. `auth_middleware.py` (Randy): ya no lee el JSON. Usa `obtener_usuario_actual()` de `auth.py` (commit del 22-oct). Sin token da 401, con el header `usuario-actual` también da 401 y sin rol da 403.
  3. `users.py` y `roles.py` (Randy): ya usan el rol `admin` y leen de la base. `GET /users/{id}` da 404 si no existe.
- **Daniel** (`auth.py`): login, logout y `/me` funcionan con la base. El token cerrado con logout ya no entra (401). El login con campos ausentes da 422, pero con cadenas vacías (`""`) todavía da 401: falta `min_length=1` en los campos del login (G2-04).
- **Robert** (cuenta `Davids107`): `main.py`, `database.py` (UTC y `fijar_actor`), `models.py`, `.env.example` y `README.md` quedaron listos el 20 y 22-oct.
- **Siguen pendientes:** bloqueo de 5 intentos por 15 minutos (el login no usa `intentos_fallidos` ni `bloqueado_hasta`), paginación en `GET /users`, auditoría de login fallido con correo inexistente, documentación OpenAPI (401 y 409 en `POST /users`) y el último fallo de `pytest`.

## Por persona

### Daniel · Persona 1 · Autenticación
| Escenario | Prioridad | Qué falta | Archivo | Estado |
|-|-|-|-|-|
| G2-05 | Alta | El QA no lo encontró. Ya está subido (20-oct): `POST /auth/logout` pone `revocado_en` en `sesion_token` y el token revocado ya da 401. | `routers/auth.py` | 🔵 Listo para retest |
| G2-07 | Media | El QA recibió 404. Ya está subido (20-oct): `GET /me` con `me_router`. Responde 200 con JWT válido y 401 sin token o con token inválido. | `routers/auth.py` | 🔵 Listo para retest |
| G2-34 | Baja | El login no usa el contador ni el bloqueo (5 fallos = 15 min). `registro.py` ya trae `esta_bloqueado()`, falta llamarlo. | `routers/auth.py` | ⏳ Pendiente |
| G2-36 | Baja | Login correcto, login fallido y logout ya llaman a `registro.py`. Falta que el login fallido con correo inexistente o vacío se guarde (`registro_id` no puede ir NULL). | `routers/auth.py`, `utils/registro.py` | 🟡 En proceso |
| G2-04 | Media | Con campos vacíos devuelve 401; el QA esperaba 422. El PM confirmó (22-oct): **422** con detalle por campo; el 401 queda solo para credenciales incorrectas. Hoy da 422 si el campo falta, pero 401 si viene como `""`. | `routers/auth.py` | 🟡 Falta `min_length=1` en `LoginRequest` para que `""` dé 422 |
| G2-33 | Media | Documentar 401 en el login (`responses=`). | `routers/auth.py` | 🔵 Login documenta 401 y 422; logout y `/me` documentan 401 |

### Randy · Persona 2 · Usuarios y roles
| Escenario | Prioridad | Qué falta | Archivo | Estado |
|-|-|-|-|-|
| G2-10, 06, 08, 09, 17, 37, 38 | Alta | Leer `Authorization: Bearer` con `verificar_token()` de Daniel y dejar de usar `usuario-actual`. Sin token = 401; sin permiso = 403. | `middleware/auth_middleware.py`, `routers/users.py`, `routers/roles.py` | 🔵 Hecho (22-oct): usa `obtener_usuario_actual()` desde la base; sin token 401, `usuario-actual` ya no sirve y sin rol 403. Falta retest de QA |
| G2-11, 12, 26 | Media | `GET /users/{id}` no existía (daba 405); debe dar 404 si no existe. | `routers/users.py` | 🔵 Lee de la base y da 404; falta retest |
| G2-31 | Baja | La lista de usuarios no pagina; `GET /users` devuelve todos y no usa `paginacion.py` de Edgar. | `routers/users.py` | ⏳ Pendiente |
| G2-33 | Media | Documentar 401 y 409 en `POST /users`; el ejemplo del 201 es un string. | `routers/users.py` | ⏳ Pendiente |
| Roles | Media | El código del rol es `admin` en la lista pero `requerir_rol(["administrador"])` en el POST. El PM confirmó `admin` (22-oct): cambiarlo en `users.py` y `roles.py`. | `routers/users.py`, `routers/roles.py` | ✅ Hecho: ambos usan `admin` |

### Edgar · Persona 3 · Errores, paginación y registro
| Escenario | Prioridad | Qué falta | Archivo | Estado |
|-|-|-|-|-|
| Pruebas | Alta | `error_handler.py` ya quedó arreglado: los 401, 403 y 404 responden bien (PM, 22-oct) y pasan 28 pruebas. Con los cambios del 23-oct pasan 33 y falla 1: el login fallido con correo inexistente no se guarda porque `registro_id` queda NULL. Corre `pytest` otra vez después de corregir. | `utils/registro.py`, `tests/test_errores.py` | 🟡 Falta 1 prueba |
| G2-36 | Baja | `registro.py` ya usa `tabla`, `registro_id` e `ip_origen` (20-oct). Login, login fallido y logout ya lo llaman. En los registros de `pytest` aparece «No se pudo registrar la accion»: la causa es que `tabla` y `registro_id` no pueden ir vacíos en la base (NOT NULL) y que `detalle` debe ser JSON válido (ya lo cubre `models.py`). El PM pidió escribir a mano solo login, login fallido y logout. | `utils/registro.py` | 🟡 Conectado; falta el caso del correo inexistente |
| G2-30 | Media | Dio PASS con el formato anterior. El manejador ahora responde `{"error": {...}}` como el contrato común: repetir 401, 403, 404, 409 y 422. El PM pidió `details` como lista de objetos (`field`, `code`, `message`); hoy es un diccionario: confirmar cuál queda. | `middleware/error_handler.py` | 🔵 Pendiente de retest QA |

### Fulvio · Persona 4 · Archivos y frontend
| Escenario | Prioridad | Qué falta | Archivo | Estado |
|-|-|-|-|-|
| G2-18 a G2-22 | Alta | Ya existe `POST /files` y valida el tipo real con `puremagic` (🔵 pendiente de validación QA). Falta `GET /files/{id}` con token (G2-21), registrar el archivo en la tabla `archivo`, evitar rutas manipuladas (G2-22) y probar G2-19 y G2-20 con el QA. | `routers/files.py` | 🟡 En proceso |
| G2-18 | Media | `POST /files` ya exige token, pero con un token válido responde 500 (`usuario_actual["correo"]` y el usuario ya no es un diccionario). | `routers/files.py` | 🟡 Por corregir |
| Pruebas | Media | Falta `tests/test_files.py`. | `tests/test_files.py` | ⏳ Pendiente |

### Robert · Persona 5 · Base del proyecto e integración
| Semana | Escenario QA | Qué toca | Archivo | Estado (22-oct) |
|-|-|-|-|-|
| 1 | G2-30 | `main.py` conecta `error_handler`; `GUIA_GRUPO2.md` en la carpeta del grupo | `main.py`, `GUIA_GRUPO2.md` | ✅ Hecho |
| 2 | G2-18 a G2-22, G2-33 | `main.py` con los routers `roles` y `files` | `main.py` | ✅ Hecho. `/me` ya queda conectado: Daniel subió `me_router` el 20-oct |
| 3 | G2-01 | Conexión del login a la base compartida: `DATABASE_URL` y driver PyMySQL | `.env.example`, `requirements.txt`, `database.py` | 🔵 Hecho el 22-oct. Falta probarlo con tu `.env`: `python -c "from g2_api.database import probar_conexion; print(probar_conexion())"` |
| 3 | G2-35 | `.env.example` solo con el formato, sin claves; `.gitignore` con `.env`, `grupo-2.txt` y `semilla_local.py` | `.env.example`, `.gitignore` | 🔵 `.env.example` sin clave. Antes de cada commit: `git status` y `git diff`. `semilla_local.py` ya no aparece en el repo (copia del 22-oct) y está en el `.gitignore`: si lo tienes local, no lo agregues |
| 3 | G2-34 | Las columnas `intentos_fallidos` y `bloqueado_hasta` coinciden con el script del Grupo 1 | `models.py` | ✅ Revisado contra `01_schema.sql`. Falta que el login las use (Daniel) |
| 3 | G2-36 | `auditoria.detalle` guarda JSON válido (`JSON_VALID` de G1) y `fijar_actor(db, actor_id, ip)` llena `@actor_id` e `@ip_origen` | `models.py`, `database.py` | 🔵 Hecho el 22-oct. Daniel y Randy tienen que llamar a `fijar_actor` |
| 3 | G2-32 | Fechas en UTC: cada conexión nueva a MySQL usa `time_zone = '+00:00'` | `database.py` | 🔵 Hecho el 22-oct |
| 4 | G2-33 | `README.md` con títulos y tablas; revisar `/api/v1/docs` cuando todos terminen | `README.md`, `main.py` | 🔵 README corregido el 22-oct. Falta la revisión final de OpenAPI |
| 4 | G2-35 | El README explica `.env`, la base compartida y la auditoría, sin ningún dato real | `README.md` | 🔵 Hecho el 22-oct |
| 4 | Pruebas | `pytest` corre para todos con SQLite temporal | `tests/conftest.py` | ✅ Sin cambios. Revisado el 23-oct: pasan 33 y falla 1 (`registro.py`, Edgar) |
| QA | G2-35 | Que el repositorio no tenga contraseñas ni variables sensibles | `.gitignore` | PASS de QA. Para mantenerlo: `grupo-2.txt` y `.env` nunca se suben, y `.env.example` solo lleva el formato |

## Estado de los escenarios (resumen del informe de QA del 17-oct; el retest es el viernes 23)

- **PASS:** G2-02, 03, 04, 13, 14, 15, 16, 23, 24, 25, 27, 28, 29, 30, 32, 35.
- **Bloqueados o fallan:** G2-05, 06, 07, 08, 09, 10, 12, 37, 38.
- **Parcial:** G2-11, 17, 26, 33, 36.
- **Implementados, esperan retest de QA:** G2-05 (logout), G2-07 (`/me`) y G2-30 (formato de errores nuevo).
- **No cumple / pendiente:** G2-34 (bloqueo), G2-31 (paginación), G2-18 a G2-22 (archivos).
- **En proceso:** G2-01 (falta probar el JWT en endpoints protegidos).


**Orden recomendado** (unos dependen de otros): Edgar (`registro.py`) → Randy (`auth_middleware.py`) → Daniel (`auth.py`) → Randy (`users.py`, `roles.py`) → Fulvio (`files.py`) → Robert (`main.py`, `config.py`, `.env.example`, `.gitignore`).

| Quién | Archivo | Qué cambia |
|-|-|-|
| Edgar | `utils/registro.py` | `registrar_accion()` usaba columnas que no existen (`entidad`, `entidad_id`, `ip`). Ya quedó con `tabla`, `registro_id` e `ip_origen` (20-oct). Falta que login y logout lo llamen; sin eso el conteo de intentos sigue en 0. |
| Edgar | `middleware/error_handler.py`, `tests/test_errores.py` | Ya responde bien (PM, 22-oct). Falta corregir `registro.py` para que las 4 pruebas que fallan pasen y confirmar con el PM si `details` es lista de objetos o diccionario. |
| Randy | `middleware/auth_middleware.py` | Lee el token Bearer, valida firma, vencimiento y sesión no revocada; 401 si falla, 403 si no tiene rol. |
| Randy | `routers/users.py`, `routers/roles.py` | Pasan a la base; `GET /users/{id}` con 404; paginación; roles con los códigos del Grupo 1 (`admin`, `teacher`…); 401, 403, 404 y 409 documentados. |
| Daniel | `routers/auth.py` | `POST /auth/logout`, `GET /me`, bloqueo de 5 intentos por 15 minutos, auditoría y 422 con campos vacíos. |
| Fulvio | `routers/files.py` | Token obligatorio, archivo guardado con nombre aleatorio, `GET /files/{id}` solo para el autor o un administrador, sin salir de la carpeta. |
| Robert | `main.py`, `config.py`, `database.py`, `models.py`, `.env.example`, `.gitignore` | Hecho el 20-oct: `main.py` incluye `auth.me_router` (Daniel ya subió `auth.py`) y `config.py` trae `UPLOAD_DIR`. Hecho el 22-oct: `database.py` (UTC y `fijar_actor`), `models.py` (`auditoria.detalle` en JSON) y `.env.example`. |

**Importante:**
- El código del rol en la base es `admin` (no `administrador`). Ya está alineado en la solución.
- Al crear usuarios el cuerpo ahora lleva `correo`, `password`, `nombres`, `apellidos` y `rol` (la base exige nombres y apellidos).
- Después de subir todo, la lista JSON de prueba (`datos_prueba/usuarios_prueba.json`) ya no se usa y se puede borrar.

### Formato de errores frente al contrato común (Edgar)
Antes, `error_handler.py` respondía `{"status", "error", "meta"}` con `details` como lista, y el CONTRATO_COMUN pide `{"error": {"code", "message", "details": {}}}`. Con el cambio del 20-oct el manejador ya responde en el formato del contrato (`details` como diccionario), así que la decisión con el PM queda en cambiar el manejador, no el contrato. Como el PASS de G2-30 fue con el formato anterior, hay que repetirlo. Respuesta posterior del PM: se queda el formato actual de G2 (`error.code`, `error.message` y `error.details`, más `status` y `meta`), con `details` como lista de objetos por campo (`field`, `code`, `message`), y él actualiza el `CONTRATO_COMUN`. El código de hoy devuelve `details` como diccionario; hay que confirmar con el PM cuál queda antes del retest.

### Pruebas automáticas y auditoría
- `pytest` completo: el 22-oct (aviso del PM) pasaban 28 y fallaban 4 (antes 15). Revisado el 23-oct: pasan 33 y falla 1, la de `registro.py` con el correo inexistente.
- En la auditoría, `registro.py` ya usa las columnas reales. Login, login fallido y logout ya lo llaman; falta el caso del correo inexistente (G2-36). El PM pidió escribir a mano solo login, login fallido y logout; los cambios de datos los registran los triggers de G1 con `@actor_id` (ver `fijar_actor` en `database.py`).
- La base exige `tabla` y `registro_id` (NOT NULL) y `detalle` como JSON válido (ver `01_schema.sql`).

### Notas de integración (Robert)
- Integración con la base: el login y la sesión (`sesion_token`) ya usan la base compartida. `users.py` y `auth_middleware.py` ya leen de la base (22-oct). El JSON ya no autentica a nadie y se deja por ahora, hasta que el PM confirme que se puede quitar.
- `models.py` coincide con el diagrama del Grupo 1 (G2_Autenticacion.pdf): usuario, rol, permiso, usuario_rol, rol_permiso, sesion_token, archivo y auditoría.
- El Grupo 1 ya subió su script SQL a la rama `grupo-1` (`01_schema.sql` y `02_seed.sql`, en `grupos/grupo-1-base-de-datos/Docs/sql/`) y `models.py` se revisó contra él: coinciden las tablas y columnas de seguridad. Falta probar la conexión real con tu `.env`.
- `semilla_local.py` ya no aparece en el repo (copia del 22-oct) y está en el `.gitignore`. Si lo tienes en tu carpeta local, no lo agregues con `git add`.


## Planner: qué se puede marcar (23-oct)

Allison revisa lo que se marque como completado en el Planner. Esa lista puede cambiar entre el jueves y el viernes. Marca solo lo que ya esté subido a `grupo-2` y probado.

| Prioridad | Punto | Escenarios | ¿Se puede marcar? |
|-|-|-|-|
| 🔴 Alta | 1. Autenticación y autorización JWT: integrar la validación JWT en los endpoints protegidos, eliminar la dependencia del encabezado `usuario-actual` y verificar respuestas HTTP 401 y 403 según corresponda | G2-06, 08, 09, 10, 37, 38 | Sí, para retest: el middleware usa el JWT y la base; sin token 401 y sin rol 403 |
| 🔴 Alta | 2. Cierre de sesión: implementar el endpoint de logout y asegurar que los tokens revocados no puedan seguir utilizándose | G2-05 | Sí, para retest: el token revocado ya da 401 |
| 🔴 Alta | 3. Control de acceso a recursos: verificar las restricciones de acceso por usuario y rol para evitar consultas o modificaciones no autorizadas | G2-17 | Parcial: usuarios y roles sí; archivos no (`POST /files` responde 500) |
| 🟡 Media | 1. Consulta del usuario autenticado: implementar el endpoint `/me` para recuperar la identidad y los roles del usuario autenticado | G2-07 | Sí, para retest |
| 🟡 Media | 2. Consulta individual de usuarios: revisar la disponibilidad del endpoint GET por ID y devolver HTTP 404 cuando el usuario no exista | G2-12 (y G2-11) | Sí, para retest: lee de la base y da 404 |
| 🟡 Media | 3. Manejo de recursos inexistentes: revisar las rutas requeridas para garantizar respuestas HTTP apropiadas cuando un recurso no exista | G2-26 | Parcial: usuarios sí; `GET /files/{id}` todavía no |
| 🟡 Media | 4. Documentación OpenAPI/Swagger: actualizar la documentación de los endpoints, sus esquemas y las respuestas HTTP 401, 409 y demás códigos aplicables | G2-33 | No: pendiente |
| ⚪ Baja | 1. Paginación de usuarios: revisar la implementación de paginación en el listado de usuarios | G2-31 | No: pendiente (Randy) |
| ⚪ Baja | 2. Bloqueo por intentos fallidos: integrar el bloqueo de 15 minutos después de cinco intentos fallidos de autenticación | G2-34 | No: pendiente (Daniel) |
| ⚪ Baja | 3. Registro de auditoría: integrar las funciones de auditoría con las operaciones correspondientes, incluyendo intentos fallidos de autenticación y acciones sensibles | G2-36 | No: falta el login fallido con correo inexistente |


## Fechas

Semana 2 · martes 20-oct · Semana 3 · martes 27-oct · Semana 4 · martes 03-nov · Semana 5 · martes 10-nov (revisión de los 36 escenarios y PR `grupo-2 → main`, solo Daniel). **PR de correcciones: jueves 22-oct. Retest de QA: viernes 23-oct.**

*Nota: el resumen sale de los PDF del QA (Lista inicial, Updt_1 e Informe no. 1), del Planner de Allison y de los avisos del PM.*
