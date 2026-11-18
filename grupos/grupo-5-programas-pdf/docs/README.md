# Programas de curso UDV

Módulo FastAPI para gestionar programas de curso y sus versiones, controlar el
flujo de revisión y autorización, y generar el PDF institucional. G5 se integra
con la aplicación compartida y la base de datos de G1; este repositorio no
incluye un servidor FastAPI independiente ni un `main.py`.

## Estructura

```text
grupo-5-programas-pdf/
├── .env.example
├── .gitignore
├── CONTRATO.md
├── requirements.txt
├── g5_programas/
│   ├── __init__.py
│   ├── auth.py             # Autenticación G2 y permisos por rol
│   ├── database.py         # Sesiones SQLAlchemy y errores de MySQL
│   ├── domain.py           # Estados y reglas de transición
│   ├── errors.py           # Errores de API
│   ├── pdf.py              # Adaptador del generador de PDF
│   ├── pdf_service.py      # Construcción del documento con ReportLab
│   ├── repository.py       # Consultas y operaciones sobre el esquema G1
│   ├── schemas.py          # Esquemas Pydantic para Swagger y validación
│   └── router.py           # Rutas bajo /api/v1
├── frontend/
│   ├── Programa.html
│   ├── script.js
│   ├── assets/
│   │   └── udv-logo.jpg
│   └── estilos/
│       ├── style.css
│       └── udv.css
├── tests/
│   ├── conftest.py
│   ├── test_api_contract.py
│   ├── test_database.py
│   ├── test_pdf.py
│   └── test_program_flow.py
└── docs/
    └── README.md  # este archivo
```

El README del proyecto está en `docs/README.md`; no hay otro README en la
raíz. El árbol omite archivos locales generados, como `.venv/`, `.pytest_cache/`
y `.DS_Store`.

## Requisitos e integración

- Python 3.10 o posterior.
- Las dependencias se fijan en `requirements.txt`: FastAPI 0.142.1,
  Pydantic 2.14.0, Uvicorn 0.54.0, SQLAlchemy 2.1.1, PyMySQL 1.1.1,
  cryptography 44.0.2, ReportLab 4.5.1 y pytest 9.1.1.
- Una base MySQL compatible con el esquema compartido de G1, incluyendo sus
  catálogos, tablas, vistas y procedimientos usados por el repositorio. La
  autorización utiliza `sp_autorizar_version`.
- Una aplicación host FastAPI que registre `g5_programas.router`, configure
  `app.state.database_session_factory` (o permita que G5 cree la sesión desde
  `DATABASE_URL`) y tenga disponible el paquete G2 con
  `g2_api.routers.auth.obtener_usuario_actual`.

Instale las dependencias del módulo desde la raíz del proyecto:

```bash
python -m pip install -r requirements.txt
```

`DATABASE_URL` debe ser una URL de SQLAlchemy para MySQL. El host y puerto
dependen de dónde se ejecute la aplicación:

```bash
# Aplicación ejecutada directamente en el equipo; Docker Compose publica MySQL
# en el puerto 3307 por defecto (MYSQL_PORT_LOCAL).
export DATABASE_URL='mysql+pymysql://<usuario>:<contraseña>@localhost:3307/db_udv'
```

Si la API y MySQL corren en Docker Compose, el host es `db` y el puerto interno
es `3306`:

```text
mysql+pymysql://<usuario>:<contraseña>@db:3306/db_udv
```

En Railway, configure `DATABASE_URL` en las variables del servicio con la URL
privada de la base MySQL. No escriba credenciales reales en el código ni en
este archivo. G5 aislado lee la variable del entorno y no carga `.env`
automáticamente; en la aplicación compartida, G2 carga `.env` y Docker
Compose también aplica su configuración de entorno.

`.env.example` es solo una plantilla y no debe contener valores reales.
Mantenga las credenciales locales en `.env` (ignorado por Git) o inyéctelas
al proceso desde el entorno de ejecución. G5 no firma ni valida JWT por su
cuenta: esa responsabilidad y `SECRET_KEY` pertenecen a G2. No incluya esa
clave en el frontend ni en archivos compartidos.

Registre el router desde la aplicación compartida:

```python
from fastapi import FastAPI
from g5_programas import router

app = FastAPI()
app.include_router(router)
```

G5 usa `obtener_usuario_actual` de G2 como dependencia de autenticación. Si
G2 no está disponible, los endpoints protegidos responden con error 503. Si no
configura una fábrica de sesiones propia, G5 usa `DATABASE_URL`.

El punto de entrada compartido debe registrar también el manejador de errores
de G5 para conservar el formato común de las excepciones `ApiError`. La
integración debe hacer ambas llamadas:

```python
app.include_router(router)

from g5_programas.errors import registrar_errores

registrar_errores(app)
```

## API principal

Todas las rutas usan el prefijo `/api/v1` y requieren la sesión Bearer que
valida G2.

| Método | Ruta | Función |
|---|---|---|
| `GET` / `POST` | `/course-programs` | Listar programas o crear un programa con su primer borrador |
| `GET` | `/course-programs/{program_id}` | Consultar un programa y sus versiones |
| `POST` | `/course-programs/{program_id}/versions` | Crear un borrador a partir de una versión autorizada |
| `GET` / `PUT` | `/program-versions/{version_id}` | Consultar una versión o actualizar sus datos |
| `PUT` | `/program-versions/{version_id}/sections/{section}` | Guardar una sección sin reemplazar las demás |
| `POST` | `/program-versions/{version_id}/submit` | Enviar una versión a revisión |
| `POST` | `/program-versions/{version_id}/review` | Iniciar la revisión |
| `POST` | `/program-versions/{version_id}/return` | Devolver una versión con observación |
| `POST` | `/program-versions/{version_id}/approve` | Aprobar una versión revisada |
| `POST` | `/program-versions/{version_id}/authorize` | Autorizarla y hacerla vigente |
| `GET` | `/program-versions/{version_id}/changes` | Comparar con la versión anterior del período |
| `GET` | `/program-versions/{version_id}/pdf` | Descargar el PDF de una versión autorizada |

Las rutas para `evaluacion` y `responsables` también tienen esquemas de entrada
específicos para documentar y validar sus datos. Los errores controlados usan
el formato común `{"error": {"code", "message", "details"}}`.

## Frontend y pruebas

El frontend está en `frontend/` y se publica en `/app/g5/Programa.html`. El
inicio de sesión pertenece a G2 y se realiza desde el portal común de `/app/`
mediante `POST /api/v1/auth/login`; G5 no implementa un login propio.
Reutiliza el token `sessionStorage["udv_token"]` y lo envía en el encabezado
`Authorization: Bearer` a la API del mismo origen. La pantalla carga el
listado de programas y permite abrir uno con el botón **Abrir**, por lo que
`program_id` en la URL es opcional.

La lista muestra todos los programas a coordinación y revisión, y solo las
versiones asignadas al docente autenticado. El docente responsable elabora,
edita y envía su propia versión; coordinación también puede elaborar y enviar.
Coordinación y revisión pueden revisar, devolver y aprobar; `authority`
autoriza. `admin`, coordinación y revisión pueden abrir versiones nuevas.
Quien creó o envió una versión no puede aprobarla. Las consultas de un docente
por ID se limitan a sus versiones. El backend valida los códigos oficiales de
G1 en cada operación y la pantalla usa los estilos comunes de
`/udv-styles/udv.css`.

Los cuerpos de escritura están descritos con modelos Pydantic para que
Swagger muestre los campos de creación, versión, encabezado y transiciones.
Al crear un programa o actualizar `responsables`, puede enviarse
`docente_responsable_id`; G5 verifica que ese usuario tenga una asignación
activa en `docente_curso` para el mismo curso, período y sede. Si no se indica
un responsable al crear, coordinación no queda asignada automáticamente como
docente. Un usuario con rol `teacher` solo se asigna a sí mismo si tiene esa
asignación activa en G1. Los nombres de docente, coordinación/revisión y
Decanatura se guardan asociados a la versión para que sobrevivan a la recarga
y estén disponibles en el PDF.
La edición se permite a gestores (`admin`, `coordinator` y `reviewer`) y al
docente responsable de su propia versión.
Las actividades de evaluación aceptan el formato del formulario o una lista
de objetos con `nombre`, `ponderacion` y `semana`; las listas incompletas
responden 422 sin borrar las filas existentes. El número de versión se asigna
por programa y respeta la unicidad de G1 aunque cambie el período.

Las secciones que la API devuelve como listas (prerrequisitos, competencias,
perfil, contenidos, bibliografía y evaluación) se conservan como listas en la
pantalla y en las solicitudes. Las listas estructuradas se editan como JSON;
un JSON inválido impide iniciar el guardado. Las secciones se guardan una por
una: al fallar una, la pantalla informa cuál fue y no envía las siguientes;
las que ya se guardaron antes del error no se revierten automáticamente.
Los ejemplos son placeholders, no valores que se envían como datos.

Al crear una versión desde un trabajo de G3, el enlace puede incluir
`&tarea_destinatario_origen_id=<id-de-asignacion>`. Si no se proporciona en
una versión nueva, se conserva la asignación de origen de la versión clonada.

Al autorizar una versión, G5 llama a `sp_autorizar_version` de G1. El trigger
de G1 registra `program.authorized` en la tabla compartida `evento`; G6
procesa ese evento para crear notificaciones. G5 no inserta una copia del
evento desde Python.

Ejecute las pruebas disponibles desde la raíz:

```bash
python -m pytest -q
```

Las pruebas cubren transiciones y permisos, y hacen solicitudes HTTP a rutas
protegidas con encabezados Bearer y roles oficiales en el formato de usuario
de G2. El proveedor de identidad se sustituye por fixtures, así que no validan
un JWT real ni conectan a MySQL. Deben complementarse con pruebas de
integración en la aplicación host y una base MySQL local de prueba.

## Documentación

- [Contrato G5](../CONTRATO.md): fuente vigente del contrato del módulo,
  ubicada en la raíz del proyecto.
