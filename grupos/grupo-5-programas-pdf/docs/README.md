# Programas de curso UDV

Módulo FastAPI para gestionar programas de curso y sus versiones, controlar el
flujo de revisión y autorización, y generar el PDF institucional. G5 se integra
con la aplicación compartida y la base de datos de G1; este repositorio no
incluye un servidor FastAPI independiente ni un `main.py`.

## Estructura

```text
grupo-5-programas-pdf/
├── .env.example
├── requirements.txt
├── g5_programas/
│   ├── auth.py             # Identidad autenticada y permisos por rol
│   ├── database.py        # Sesiones SQLAlchemy y errores de MySQL
│   ├── domain.py          # Estados y reglas de transición
│   ├── errors.py          # Errores de API
│   ├── pdf.py             # Adaptador del generador de PDF
│   ├── pdf_service.py     # Construcción del documento con ReportLab
│   ├── repository.py      # Consultas y operaciones sobre el esquema G1
│   └── router.py          # Rutas bajo /api/v1
├── frontend/
│   ├── Programa.html
│   ├── script.js
│   ├── assets/
│   └── estilos/
├── tests/
│   └── test_program_flow.py
└── docs/
    ├── README.md
    ├── overview.md
    └── workflow.md
```

## Requisitos e integración

- Python 3.10 o posterior.
- Una base MySQL compatible con el esquema compartido de G1, incluyendo sus
  catálogos, tablas, vistas y procedimientos usados por el repositorio. La
  autorización utiliza `sp_autorizar_version`.
- Una aplicación host FastAPI que registre `g5_programas.router`, configure
  `app.state.database_session_factory` (o permita que G5 cree la sesión desde
  `DATABASE_URL`) e instale su middleware de autenticación.
- El middleware debe colocar el usuario autenticado en
  `request.state.user` o `request.state.current_user`, con ID y roles
  reconocibles por [auth.py](../g5_programas/auth.py).

Instale las dependencias del módulo:

```bash
python -m pip install -r requirements.txt
```

Configure `DATABASE_URL` en el entorno del proceso host con una URL de
SQLAlchemy para MySQL, por ejemplo:

```bash
export DATABASE_URL='mysql+pymysql://usuario:clave@localhost:3306/db_udv'
```

`.env.example` es una plantilla; el proyecto no carga archivos `.env`
automáticamente. En producción, proporcione la variable mediante el mecanismo
de configuración de la aplicación host.

Registre el router desde la aplicación compartida:

```python
from fastapi import FastAPI
from g5_programas import router

app = FastAPI()
app.include_router(router)
```

La aplicación host también debe instalar la autenticación que pueble el
usuario en `request.state`. Si no configura una fábrica de sesiones propia,
G5 usa `DATABASE_URL`.

## Frontend y pruebas

El frontend está en `frontend/`. Actualmente `script.js` apunta a
`http://127.0.0.1:8000/api/v1` y carga el programa con ID `1`; ajuste esos
valores para el entorno donde se publique. El selector de rol y los nombres
mostrados en la página son parte de la interfaz de demostración: no sustituyen
la sesión autenticada ni los permisos que valida el backend.

Ejecute las pruebas disponibles desde la raíz:

```bash
pytest -q
```

Las pruebas actuales cubren transiciones, estados editables, unicidad de la
versión autorizada y permisos; no reemplazan una prueba de integración con
MySQL y la aplicación host.

## Documentación

- [Descripción general](overview.md): arquitectura, dependencias e integración.
- [Flujo del sistema](workflow.md): estados, permisos, endpoints y PDF.
