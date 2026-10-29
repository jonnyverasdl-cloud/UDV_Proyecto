# Descripción general

G5 es un módulo de integración para gestionar programas de curso y su ciclo de
revisión en la Universidad Da Vinci de Guatemala. Expone un router FastAPI con
prefijo `/api/v1`; la aplicación compartida lo registra y aporta la sesión de
usuario autenticada. El repositorio no incluye una aplicación host ni un
servidor independiente.

## Componentes

- **`g5_programas/router.py`**: rutas para consultar y crear programas,
  actualizar secciones, ejecutar transiciones, revisar diferencias y descargar
  el PDF.
- **`g5_programas/domain.py`**: estados permitidos, transiciones y reglas
  asociadas al ciclo de vida.
- **`g5_programas/auth.py`**: transforma el usuario de `request.state.user` o
  `request.state.current_user` en un actor y verifica roles. La identidad no se
  toma de los datos enviados por el navegador.
- **`g5_programas/database.py`**: crea una sesión SQLAlchemy por solicitud a
  partir de `DATABASE_URL` (o utiliza la fábrica configurada por la aplicación
  host) y traduce errores de MySQL a errores de API.
- **`g5_programas/repository.py`**: lee y modifica el esquema compartido de G1.
  La autorización delega la operación a `sp_autorizar_version`.
- **`g5_programas/pdf_service.py`** y **`g5_programas/pdf.py`**: construyen el
  documento A4 en memoria con ReportLab.
- **`frontend/`**: formulario web para editar las secciones del programa y
  mostrar acciones del flujo.

## Integración con la aplicación host

La aplicación compartida debe:

1. Registrar `g5_programas.router`.
2. Instalar el middleware de autenticación y colocar el usuario en
   `request.state.user` o `request.state.current_user`.
3. Proporcionar una sesión compatible con el esquema G1, bien configurando
   `app.state.database_session_factory` o bien estableciendo `DATABASE_URL`.
4. Contar con las tablas, vistas, catálogos y procedimientos de G1 que consulta
   el repositorio.

Para instrucciones de instalación y ejecución, consulte [README](README.md).

## API

Las rutas están bajo `/api/v1`. Incluyen operaciones para listar y consultar
programas y versiones, crear programas y versiones, actualizar versiones o
secciones, enviar/revisar/devolver/aprobar/autorizar, obtener cambios entre
versiones y descargar el PDF. La lista detallada está en [Flujo del
sistema](workflow.md#rutas-principales).

Los errores controlados se representan con estado HTTP, código y mensaje; los
errores de validación pueden incluir detalles de los campos.

## Frontend

La interfaz de `frontend/Programa.html` y `frontend/script.js` es una capa de
presentación que consume la API con credenciales de sesión. En su estado
actual, el cliente apunta a `http://127.0.0.1:8000/api/v1` y a un ID de
programa fijo. El selector de rol actualiza la interfaz, pero no concede
permisos: el backend toma la identidad y los roles de la sesión autenticada que
aporta la aplicación host.
