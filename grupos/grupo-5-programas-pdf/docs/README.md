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
│   └── test_program_flow.py
└── docs/
    ├── README.md
    ├── instrucciones.md
    └── CONTRATO.md
```

## Requisitos e integración

- Python 3.10 o posterior.
- Las dependencias se fijan en `requirements.txt`: FastAPI 0.142.1,
  Uvicorn 0.54.0, SQLAlchemy 2.1.1, PyMySQL 1.1.1, cryptography 44.0.2,
  ReportLab 4.5.1 y pytest 9.1.1.
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

## Frontend y pruebas

El frontend está en `frontend/`. Usa la API del mismo origen, muestra el
formulario de acceso de G2 y carga el programa indicado por
`?program_id=<id>`, por ejemplo `Programa.html?program_id=1`. El token se
mantiene en `sessionStorage` durante la pestaña y se envía como Bearer en las
solicitudes protegidas. Los roles del selector se limitan a los que devuelve
G2; el backend sigue siendo quien autoriza cada operación.

Al crear una versión desde un trabajo de G3, el enlace puede incluir
`&tarea_destinatario_origen_id=<id-de-asignacion>`. Si no se proporciona en
una versión nueva, se conserva la asignación de origen de la versión clonada.

Ejecute las pruebas disponibles desde la raíz:

```bash
python -m pytest -q
```

Las pruebas unitarias cubren transiciones y permisos, el manejador de errores,
los filtros y OpenAPI, la validación del identificador de asignación, y la
selección/cierre de sesiones y auditoría con mocks. No conectan a MySQL ni
reemplazan una prueba de integración con la aplicación host.

## Documentación

- [Instrucciones para QA](instrucciones.md): contexto, cambios que revisar,
  pruebas y pendientes de integración.
