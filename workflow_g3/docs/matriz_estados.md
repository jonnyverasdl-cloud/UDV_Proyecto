# Matriz de estados, acciones y roles

Ejecutar `python -m workflow.matrix`.

## Flujo `standard`

| Estado actual | Acción | Estado nuevo | Roles | Alcance | Comentario |
| --- | --- | --- | --- | --- | --- |
| draft | publish | assigned | Coordinador | quien creó la tarea o su responsable | - |
| assigned | start | in_progress | Docente | solo el docente destinatario | - |
| in_progress | submit | submitted | Docente | solo el docente destinatario | - |
| submitted | review | under_review | Revisor | el revisor designado en la tarea | - |
| under_review | return | returned | Revisor | el revisor designado en la tarea | obligatorio |
| returned | resubmit | submitted | Docente | solo el docente destinatario | - |
| under_review | approve | approved | Revisor, Autoridad | el revisor designado en la tarea | - |
| approved | close | closed | Coordinador, Sistema | quien creó la tarea o su responsable | - |
| draft | cancel | cancelled | Coordinador | quien creó la tarea o su responsable | - |
| assigned | cancel | cancelled | Coordinador | quien creó la tarea o su responsable | - |

## Flujo `short`

| Estado actual | Acción | Estado nuevo | Roles | Alcance | Comentario |
| --- | --- | --- | --- | --- | --- |
| draft | publish | assigned | Coordinador | quien creó la tarea o su responsable | - |
| approved | close | closed | Coordinador, Sistema | quien creó la tarea o su responsable | - |
| draft | cancel | cancelled | Coordinador | quien creó la tarea o su responsable | - |
| assigned | cancel | cancelled | Coordinador | quien creó la tarea o su responsable | - |
| assigned | submit | submitted | Docente | solo el docente destinatario | - |
| submitted | approve | approved | Revisor, Autoridad | el revisor designado en la tarea | - |

Cualquier otra combinación estado/acción responde **409** sin modificar datos.
Rol no permitido o usuario que no es el destinatario: **403**.
Devolver (`return`) sin comentario: **422**.
