# Grupo 6: Administración, notificaciones, pruebas y despliegue

Módulo `g6_admin`. Este README explica qué existe hasta ahora y cómo probarlo
(CONTRATO.md del G6 §5).

## Qué hay por ahora

| Pieza | Ruta | Escenarios QA |
|---|---|---|
| Catálogos: listar (con sesión), agregar y modificar (solo administración) | `GET` y `POST` en `/api/v1/<catálogo>` y `PATCH` en `/api/v1/<catálogo>/{id}`; los catálogos son `academic-units`, `campuses`, `courses`, `periods`, `modalities` y `areas` | G6-01, G6-02, G6-03, G6-21 a G6-25 |
| Pantalla de catálogos | `g6_admin/pantallas/catalogos.html` | G6-01, G6-02 |
| Estado del servicio | `GET /api/v1/health` | G6-34, G6-36 (en lo que toca a esta ruta) |
| Notificaciones: las propias, paginadas y marcar como leída | `GET /api/v1/notifications` (`?unread=true`) y `PATCH /api/v1/notifications/{id}/read` | G6-04 a G6-13, G6-18 (en lo que toca a notificaciones) |
| Auditoría: consulta filtrada (solo administración) | `GET /api/v1/audit` con `user_id`, `from`, `to`, `entity` y `action` | G6-14, G6-15, G6-30 a G6-33 |

**Quién puede hacer qué**

| Rol (código del G1) | Consultar catálogos | Agregar o modificar registros |
|---|---|---|
| Administración (`admin`) | Sí | Sí |
| Docente (`teacher`) y demás roles | Sí | No: el servidor responde 403 |
| Sin sesión | No: 401 | No: 401 |

Cada persona ve y marca solo sus propias notificaciones (la de otra responde
404). La auditoría la consulta solo administración (`admin`); los demás
reciben 403.

## Qué usamos del Grupo 2

El G6 no tiene login, usuarios de prueba ni formato de error propios. Todo eso
es del G2 y se importa desde `g2_api` (CONTRATO_COMUN §1):

| Para qué | Qué se importa |
|---|---|
| Saber quién inició sesión | `g2_api.middleware.auth_middleware.obtener_usuario_actual` |
| Permitir agregar y modificar solo a administración | `requerir_rol(["admin"])` del mismo archivo |
| Formato de error (401, 403, 409, 422) | `api_error` y `register_error_handlers` de `g2_api.middleware.error_handler` |
| Paginación y máximo de `per_page` | `params_paginacion` de `g2_api.utils.paginacion` |
| Revisar la base en `/api/v1/health` | `probar_conexion` de `g2_api.database` |

La pantalla manda el token del login del G2 como
`Authorization: Bearer <token>` y pregunta los roles a `GET /api/v1/me`.

## Cómo correr las pruebas

Se necesita que la carpeta `grupos/grupo-2-api-seguridad/` tenga el código del
G2 (llega a `main` cuando se acepte su PR). Desde la raíz del repositorio:

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
source .venv/bin/activate         # Mac o Linux
pip install -r requirements.txt
cd grupos/grupo-6-administracion
python -m pytest
```

Las pruebas usan el control de roles y el formato de error reales del G2.
Solo reemplazan quién inició sesión (`dependency_overrides` de FastAPI) y usan
un SQLite temporal, así que no necesitan MySQL ni un `.env`.

## Cómo entregan sus eventos los grupos 3, 4 y 5 (G6-04 a G6-11)

Mientras el PM define el transporte de eventos (README §5), se llama a la
función del G6. Cada evento lleva un `id` único: si llega dos veces, no se
duplica.

```python
from g6_admin.api import obtener_notificaciones

obtener_notificaciones().procesar_evento({
    "id": "entrega-58-devuelta-1",
    "name": "assignment.returned",
    "recipients": [12],               # id del docente
    "data": {"task_title": "Sílabo", "comment": "Falta la bibliografía."},
})
```

| Evento | Datos obligatorios en `data` |
|---|---|
| `task.published`, `assignment.due_soon` | `task_title`, `due_date` |
| `assignment.submitted`, `assignment.approved`, `task.cancelled` | `task_title` |
| `assignment.returned` | `task_title`, `comment` |
| `program.authorized` | `program_name` |

Si falta algo responde 422 con el formato del G2 y no se guarda ninguna
notificación (G6-18).

## Cómo registran sus transiciones el G3 y el G5 (G6-15)

El contrato común pide que toda transición guarde actor, fecha, estado
anterior, estado nuevo y comentario. La fecha la pone el G6:

```python
from g6_admin.api import obtener_auditoria

obtener_auditoria().registrar_transicion(
    actor_id=12,                     # quién hizo el cambio
    entidad="assignment",            # task, assignment o program_version
    entidad_id=58,
    estado_anterior="in_progress",
    estado_nuevo="submitted",
    comentario="Entrego la planificación.",  # opcional, hasta 1000 caracteres
)
```

Solo se aceptan los estados oficiales de CONTRATO_COMUN.md §2. Las altas y los
cambios de catálogos ya se auditan solos. Los registros de auditoría solo se
agregan: no hay forma de editarlos ni borrarlos.

## Cómo se integra a la aplicación

El G6 no levanta su propia app ni servidor (CONTRATO_COMUN §1). Lo integra el
PM en el `main.py` de la raíz. **Pedidos al PM:**

1. Activar la línea `("g6_admin.api", "router")` en `ROUTERS`.
2. Servir la pantalla: la carpeta `g6_admin/pantallas/` en `/g6` y
   `grupos/udv-styles/` en `/udv-styles`. La pantalla queda en
   `/g6/catalogos.html` y usa rutas relativas (`/api/v1/...`).
3. Agregar `APP_ENV` y `APP_VERSION` al `.env.example`.

## Pendientes con el Grupo 2

| Qué | Por qué importa | Dónde se cambia si difiere |
|---|---|---|
| Middleware con `Authorization: Bearer` y `GET /api/v1/me` (su tarea de la semana del 20-oct) | Hoy su middleware lee el encabezado `usuario-actual`; la pantalla manda el token Bearer | Nada en el G6: se usa su dependencia |
| Clave donde su login guarda el token | La pantalla la lee para mandarla | `CLAVE_TOKEN` en `catalogos.html` (hoy `udv_token`) |
| Ruta de su pantalla de login | El aviso "Ir al inicio de sesión" apunta ahí | `PAGINA_INICIO_SESION` en `catalogos.html` (hoy `/g2/index.html`) |
| Código del rol de administración | La semilla del G1 usa `admin`; su JSON de prueba usa `administrador` | `ROLES_ADMINISTRACION` en `api.py` y `ROL_ADMINISTRACION` en `catalogos.html` |

## Piezas temporales

| Pieza | Por qué es temporal | Se reemplaza por |
|---|---|---|
| Repositorios de notificaciones y auditoría en memoria | Se borran al reiniciar | Tablas del G1: notificaciones con llave única (`evento_id`, `usuario_id`) y auditoría sin UPDATE ni DELETE |
| `procesar_evento` y `registrar_transicion` como llamada directa | El transporte de eventos lo decide el PM con G3 (README §5) | El mecanismo que se apruebe; la lógica no cambia |
| Repositorio en memoria | Los registros se borran al reiniciar | Un repositorio con los mismos métodos sobre las tablas del G1 (`sede`, `unidad_academica`, `curso`, `periodo`, `modalidad`, `area`) y `paginar(consulta, ...)` del G2 |
| Campos `code`, `name`, `is_active` | Las columnas reales son las del esquema del G1 | Los campos del G1 |

## Cómo está organizado

| Archivo | Qué hace |
|---|---|
| `g6_admin/api.py` | Rutas `/api/v1/...` en `router`, que monta el `main.py` de la raíz |
| `g6_admin/catalogos.py` | Reglas de catálogos: validación, búsqueda, filtro y orden |
| `g6_admin/salud.py` | Respuesta de `/api/v1/health`, sin exponer detalles internos |
| `g6_admin/pantallas/catalogos.html` | Pantalla con los estilos de `grupos/udv-styles/udv.css` |
| `tests/` | 69 pruebas automáticas |

## Variables de entorno

| Variable | Uso | Valor por defecto |
|---|---|---|
| `APP_ENV` | Nombre del ambiente que muestra `/api/v1/health` (G6-35) | `desarrollo` |
| `APP_VERSION` | Versión que muestra `/api/v1/health` | La versión de `g6_admin` |
| `DATABASE_URL` | La lee el G2; `/api/v1/health` informa si la base responde | Sin valor: `not_configured` |
