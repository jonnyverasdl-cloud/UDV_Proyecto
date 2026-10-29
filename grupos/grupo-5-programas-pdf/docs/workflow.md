# Flujo del sistema

G5 gestiona el contenido y los estados de cada versión de un programa. La API
valida las acciones y registra los cambios en el esquema compartido de G1.
La identidad y los permisos proceden de la sesión autenticada que la
aplicación host expone en `request.state`; no se confía en el selector de rol
del frontend.

## Estados y transiciones

El recorrido normal de una versión es:

```text
draft -> submitted -> under_review -> approved -> authorized
             ^             |
             |             v
             +---------- returned
```

`returned` puede volver a `submitted` después de que se corrija. Al autorizar
una versión, G5 llama al procedimiento `sp_autorizar_version` de G1, que
gestiona la autorización en la base de datos. Para el mismo programa y período
se comprueba que no haya más de una versión con estado `authorized`.

| Acción | Estado requerido | Estado resultante | Rol de API |
|---|---|---|---|
| Enviar (`submit`) | `draft` o `returned` | `submitted` | autor |
| Tomar revisión (`review`) | `submitted` | `under_review` | revisor |
| Devolver (`return`) | `under_review` | `returned` | revisor |
| Aprobar (`approve`) | `under_review` | `approved` | revisor |
| Autorizar (`authorize`) | `approved` | `authorized` | autoridad |

Los nombres de rol normalizados que acepta el backend incluyen:

- **Autor**: `docente`, `teacher` o `elaborador`.
- **Coordinación**: `coordinator`, `coordinador-academico` o
  `coordinador_academico`.
- **Revisor**: `revisor`, `reviewer` o cualquiera de los roles de
  Coordinación anteriores.
- **Autoridad**: `autoridad`, `decanatura`, `decano` o `dean`.

Solo los estados `draft` y `returned` permiten editar. Antes de enviar, G5
requiere nombre y período, y valida que las ponderaciones de evaluación sumen
100. La acción `return` requiere un comentario u observación no vacío. Una
transición fuera de orden produce un conflicto HTTP 409.

## Rutas principales

Todas las rutas usan el prefijo `/api/v1` y requieren un usuario autenticado.
Además, crear programas requiere el rol autor; crear versiones requiere
Coordinación; y actualizar una versión o sección requiere el rol autor. Las
acciones de transición usan los roles indicados en la tabla anterior.

| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/course-programs?page=1&per_page=20` | Lista programas paginados. `per_page` admite de 1 a 100. |
| `POST` | `/course-programs` | Crea un programa y su primera versión `draft`. Requiere `curso_id`, `sede_id`, `modalidad_id` y `periodo_id`. |
| `GET` | `/course-programs/{program_id}` | Devuelve el programa y su historial de versiones. |
| `POST` | `/course-programs/{program_id}/versions` | Crea una nueva versión `draft` basada en una versión autorizada del período indicado. Requiere `periodo_id`; `clonar` es opcional y por defecto `true`. |
| `GET` | `/program-versions/{version_id}` | Devuelve la versión y sus secciones. |
| `PUT` | `/program-versions/{version_id}` | Actualiza secciones y/o `resumen_cambios` de una versión editable. |
| `PUT` | `/program-versions/{version_id}/sections/{section}` | Actualiza una sección específica con un cuerpo `{ "contenido": ... }`. |
| `POST` | `/program-versions/{version_id}/submit` | Envía una versión a revisión. |
| `POST` | `/program-versions/{version_id}/review` | Inicia la revisión. |
| `POST` | `/program-versions/{version_id}/return` | Devuelve la versión; requiere `comentario` u `observacion`. |
| `POST` | `/program-versions/{version_id}/approve` | Aprueba una versión en revisión. |
| `POST` | `/program-versions/{version_id}/authorize` | Autoriza una versión aprobada. |
| `GET` | `/program-versions/{version_id}/changes` | Compara secciones con la versión anterior del mismo programa y período. |
| `GET` | `/program-versions/{version_id}/pdf` | Genera y descarga el PDF de una versión autorizada o reemplazada. |

Las secciones reconocidas son `general`, `descripcion`, `prerrequisitos`,
`competencias`, `perfil`, `metodologia`, `contenidos`, `bibliografia`,
`evaluacion` y `responsables`. La actualización de una sección espera un
objeto o una lista en `contenido`. Los datos protegidos de identidad y estado
no se pueden cambiar mediante la ruta de actualización general.

## Creación y edición de versiones

La creación inicial requiere identificadores que pertenecen a los catálogos
de G1 y crea la versión número 1 como `draft`. Si el programa ya tiene una
versión para ese período, se debe usar la ruta de versiones.

Para abrir una versión nueva, se requiere una versión `authorized` de ese
programa y período. G5 asigna el siguiente número de versión y, por defecto,
copia las secciones de la autorizada, excepto `responsables`. Los cambios de
contenido se guardan por sección y solo mientras el estado sea `draft` o
`returned`.

## PDF institucional

El endpoint `/program-versions/{version_id}/pdf` permite generar el documento
para versiones `authorized` o `superseded`. Además, comprueba la autorización
de origen; las versiones actualmente autorizadas deben aparecer en la vista
vigente de G1. Si falta el registro de autorización, la generación falla.

El PDF se arma en memoria con ReportLab y se devuelve como descarga
`application/pdf`. G5 calcula el SHA-256 del archivo y registra su huella y
fecha de generación en la versión autorizada si todavía no tenía huella. No
guarda el archivo PDF en el repositorio ni en disco.

## Frontend de demostración

El cliente actual usa la API local `http://127.0.0.1:8000/api/v1`, selecciona
el programa con ID `1` y envía las credenciales de sesión del navegador. El
selector de roles sirve para mostrar acciones en la interfaz, no para
autenticar ni autorizar solicitudes. En un despliegue integrado, la API host
debe proporcionar la sesión real y sus roles.
