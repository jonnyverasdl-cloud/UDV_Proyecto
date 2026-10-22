# Pendientes del QA — Grupo 2 (Update No. 1 · 17-oct-2026)

Resumen del informe de Allison Espaderos (QA) y quién corrige cada cosa. Cada quien toca **solo sus archivos**. Los números G2-xx son los escenarios del plan de QA.

Prioridad: **Alta** → **Media** → **Baja**. El Planner de Allison tiene tres tareas (Alta, Media y Baja) con puntos por escenario; están sin responsable y con fecha 21/10. El detalle está en `GUIA_GRUPO2.md`, sección 8.

## Lo más urgente (crítico)

El middleware de usuarios y roles todavía lee el encabezado `usuario-actual` y una lista JSON temporal, en vez del JWT. Por eso cualquiera puede hacerse pasar por administrador (G2-10) y el login real no sirve para entrar a `/users` ni `/roles`. Esto bloquea G2-06, 08, 09, 17, 37 y 38.

**Cómo leer los estados:** ✅ Cumple (PASS de QA) · 🔵 Implementado, pendiente de validación o retest de QA · 🟡 En proceso · ⏳ Pendiente de implementar.

## Estado al 20-oct

- **Randy** ya lee el token Bearer y agregó `GET /users/{id}` con 404, pero sigue buscando al usuario en la lista JSON y no en la base. Con eso, un token del login real todavía no entra a `/users`. Falta: leer desde la base, revisar que la sesión no esté revocada y usar el rol `admin`.
- **David** subió el import de `files` en `main.py` y las dependencias `puremagic` y `email-validator`.
- **Daniel** subió `POST /auth/logout` y `GET /me` en `auth.py` (20-oct). Quedan 🔵 implementados, pendientes de validación de QA; todavía dependen del middleware de Randy.
- **Edgar** actualizó `error_handler.py` y `registro.py` (20-oct). El formato de error ya sigue el contrato común y `registro.py` ya usa las columnas reales de `auditoria`, pero `error_handler.py` quedó con un fallo (ver «Pruebas automáticas y auditoría» más abajo).
- **Siguen pendientes:** bloqueo, auditoría (que login y logout llamen a `registro.py`), paginación y que `pytest` completo pase.

## Por persona

### Daniel · Persona 1 · Autenticación
| Escenario | Prioridad | Qué falta | Archivo | Estado |
|-|-|-|-|-|
| G2-05 | Alta | El QA no lo encontró. Ya está subido (20-oct): `POST /auth/logout` pone `revocado_en` en `sesion_token`. Falta que el middleware de Randy rechace el token revocado. | `routers/auth.py` | 🔵 Implementado, pendiente de validación QA |
| G2-07 | Media | El QA recibió 404. Ya está subido (20-oct): `GET /me` con `me_router`. Falta retest con JWT válido, sin token y con token inválido. | `routers/auth.py` | 🔵 Implementado, pendiente de validación QA |
| G2-34 | Baja | El login no usa el contador ni el bloqueo (5 fallos = 15 min). | `routers/auth.py` | ⏳ Pendiente |
| G2-36 | Baja | El login no llama a `registrar_accion()` ni `registrar_login_fallido()`. | `routers/auth.py` | ⏳ Pendiente |
| G2-04 | Media | Con campos vacíos devuelve 401; el QA esperaba 422 (revisar con el PM). | `routers/auth.py` | 🔎 Por confirmar con el PM |
| G2-33 | Media | Documentar 401 en el login (`responses=`). | `routers/auth.py` | ⏳ Pendiente |

### Randy · Persona 2 · Usuarios y roles
| Escenario | Prioridad | Qué falta | Archivo | Estado |
|-|-|-|-|-|
| G2-10, 06, 08, 09, 17, 37, 38 | Alta | Leer `Authorization: Bearer` con `verificar_token()` de Daniel y dejar de usar `usuario-actual`. Sin token = 401; sin permiso = 403. | `middleware/auth_middleware.py`, `routers/users.py`, `routers/roles.py` | 🟡 En proceso |
| G2-11, 12, 26 | Media | `GET /users/{id}` no existe (da 405); debe dar 404 si no existe. | `routers/users.py` | 🟡 Parcial |
| G2-31 | Baja | La lista de usuarios no pagina; usar `paginacion.py` de Edgar. | `routers/users.py` | ⏳ Pendiente |
| G2-33 | Media | Documentar 401 y 409 en `POST /users`; el ejemplo del 201 es un string. | `routers/users.py` | ⏳ Pendiente |
| Roles | Media | El código del rol es `admin` en la lista pero `requerir_rol(["administrador"])` en el POST; alinear con el PM. Además `"coordinador "` tiene un espacio al final. | `routers/roles.py` | ⏳ Pendiente |

### Edgar · Persona 3 · Errores, paginación y registro
| Escenario | Prioridad | Qué falta | Archivo | Estado |
|-|-|-|-|-|
| Pruebas | Alta | El alias `registrar_manejadores` ya existe en `error_handler.py`, pero en `DEFAULT_MESSAGES` (línea 45) hay unas comillas `''''...'''` de más y la constante no se crea. Resultado al correr `pytest`: 15 fallan y 14 pasan (`NameError`). Quitar esas comillas y volver a correr `pytest`. | `middleware/error_handler.py`, `tests/test_errores.py` | ⏳ Pendiente |
| G2-36 | Baja | `registro.py` ya usa `tabla`, `registro_id` e `ip_origen` (20-oct). Falta que login y logout lo llamen; coordinar con Daniel y Randy. En los registros de `pytest` aparece «No se pudo registrar la accion»: revisar la causa. | `utils/registro.py` | 🔵 Implementado, falta conectarlo |
| G2-30 | Media | Dio PASS con el formato anterior. El manejador ahora responde `{"error": {...}}` como el contrato común: repetir 401, 403, 404, 409 y 422. | `middleware/error_handler.py` | 🔵 Pendiente de retest QA |

### Fulvio · Persona 4 · Archivos y frontend
| Escenario | Prioridad | Qué falta | Archivo | Estado |
|-|-|-|-|-|
| G2-18 a G2-22 | Alta | Ya existe `POST /files` y valida el tipo real con `puremagic` (🔵 pendiente de validación QA). Falta `GET /files/{id}` con token (G2-21), registrar el archivo en la tabla `archivo`, evitar rutas manipuladas (G2-22) y probar G2-19 y G2-20 con el QA. | `routers/files.py` | 🟡 En proceso |
| G2-18 | Media | `POST /files` aún no exige token (se activa cuando Randy termine el middleware). | `routers/files.py` | ⏳ Pendiente |
| Pruebas | Media | Falta `tests/test_files.py`. | `tests/test_files.py` | ⏳ Pendiente |

### Robert · Persona 5 · Base del proyecto e integración
| Semana | Qué toca | Archivo | Estado |
|-|-|-|-|
| 1 | `main.py` conecta `error_handler`; `GUIA_GRUPO2.md` en la carpeta del grupo | `main.py`, `GUIA_GRUPO2.md` | ✅ Hecho |
| 2 | `main.py` con los routers `roles` y `files` (G2-18 a G2-22) | `main.py` | ✅ Hecho. `/me` ya queda conectado: Daniel subió `me_router` el 20-oct. |
| 3 | `.env.example`, `requirements.txt`, `database.py` con `PyMySQL` y `DATABASE_URL` | `.env.example`, `requirements.txt`, `database.py` | ✅ Ya estaba; se agregó la opción de la base compartida. Falta probar la conexión real con tu `.env`. |
| 4 | `README.md` con títulos y tablas; `conftest.py` | `README.md`, `tests/conftest.py` | ✅ README rehecho; `conftest.py` con guarda para no tocar la base compartida. ⚠️ `pytest` completo aún se interrumpe por `test_errores.py` (Edgar). |
| QA | G2-35 sin credenciales | `.gitignore` | PASS. Para mantenerlo: `grupo-2.txt` y `.env` nunca se suben; `semilla_local.py` se saca del repo. |
| QA | G2-33 documentación | `main.py` (`/api/v1/docs`) | ⏳ Pendiente: revisar `/api/v1/docs` cuando todos terminen. |

## Estado de los escenarios (resumen)

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
| Edgar | `middleware/error_handler.py`, `tests/test_errores.py` | El alias `registrar_manejadores` ya existe. Falta quitar las comillas de más en `DEFAULT_MESSAGES` (línea 45) y confirmar que `pytest` completo pasa, con la tabla falsa de auditoría con las columnas reales. |
| Randy | `middleware/auth_middleware.py` | Lee el token Bearer, valida firma, vencimiento y sesión no revocada; 401 si falla, 403 si no tiene rol. |
| Randy | `routers/users.py`, `routers/roles.py` | Pasan a la base; `GET /users/{id}` con 404; paginación; roles con los códigos del Grupo 1 (`admin`, `teacher`…); 401, 403, 404 y 409 documentados. |
| Daniel | `routers/auth.py` | `POST /auth/logout`, `GET /me`, bloqueo de 5 intentos por 15 minutos, auditoría y 422 con campos vacíos. |
| Fulvio | `routers/files.py` | Token obligatorio, archivo guardado con nombre aleatorio, `GET /files/{id}` solo para el autor o un administrador, sin salir de la carpeta. |
| Robert | `main.py`, `config.py`, `.env.example`, `.gitignore` | Hecho el 20-oct: `main.py` incluye `auth.me_router` (Daniel ya subió `auth.py`) y `config.py` trae `UPLOAD_DIR`. |

**Importante:**
- El código del rol en la base es `admin` (no `administrador`). Ya está alineado en la solución.
- Al crear usuarios el cuerpo ahora lleva `correo`, `password`, `nombres`, `apellidos` y `rol` (la base exige nombres y apellidos).
- Después de subir todo, la lista JSON de prueba (`datos_prueba/usuarios_prueba.json`) ya no se usa y se puede borrar.

### Formato de errores frente al contrato común (Edgar)
Antes, `error_handler.py` respondía `{"status", "error", "meta"}` con `details` como lista, y el CONTRATO_COMUN pide `{"error": {"code", "message", "details": {}}}`. Con el cambio del 20-oct el manejador ya responde en el formato del contrato (`details` como diccionario), así que la decisión con el PM queda en cambiar el manejador, no el contrato. Como el PASS de G2-30 fue con el formato anterior, hay que repetirlo. Antes, hay que arreglar `DEFAULT_MESSAGES` (ver «Pruebas» en la tabla de Edgar).

### Pruebas automáticas y auditoría
- `pytest` completo (rama `grupo-2`, 20-oct): 15 fallan y 14 pasan. La causa es `DEFAULT_MESSAGES` sin definir en `error_handler.py`.
- En la auditoría, `registro.py` ya usa las columnas reales. Falta conectarlo con login y logout (G2-36) y revisar por qué aparece «No se pudo registrar la accion» al correr las pruebas.

### Notas de integración (Robert)
- Integración con la base: el login y la sesión (`sesion_token`) ya usan la base compartida. `users.py` y `auth_middleware.py` todavía leen la lista JSON; pasan a la base cuando Randy suba su parte.
- `models.py` coincide con el diagrama del Grupo 1 (G2_Autenticacion.pdf): usuario, rol, permiso, usuario_rol, rol_permiso, sesion_token, archivo y auditoría.
- El Grupo 1 todavía no subió su script SQL (solo diagramas). Falta probar contra MariaDB real.
- `semilla_local.py` está en el repo aunque dice "NO SE SUBE" y trae una clave de demostración. Para G2-35 conviene sacarlo del repo y agregarlo al `.gitignore`.

## Fechas

Semana 2 · martes 20-oct · Semana 3 · martes 27-oct · Semana 4 · martes 03-nov · Semana 5 · martes 10-nov (revisión de los 36 escenarios y PR `grupo-2 → main`, solo Daniel).

*Nota: el resumen sale de los PDF del QA (Lista inicial, Updt_1 e Informe no. 1) y del Planner de Allison.*
