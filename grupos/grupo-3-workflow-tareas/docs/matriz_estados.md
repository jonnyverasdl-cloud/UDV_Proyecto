# Matriz de estados, acciones y roles

Generada desde `workflow/matrix.py`. No editar a mano: ejecutar `python -m workflow.matrix`.

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

## Orden de validación y códigos de error

Las validaciones se hacen siempre en este orden y la primera que falla corta el proceso:

1. La asignación no existe: **404**.
2. El usuario no tiene permiso para la acción (rol no permitido, o no es el destinatario / revisor / coordinador que corresponde): **403**.
3. El estado actual no permite la acción (cualquier combinación estado/acción que no esté en la tabla): **409**.
4. Falta el comentario obligatorio (p. ej. `return` sin comentario): **422**.

Por eso un usuario sin permiso recibe **403 aunque además la transición sea inválida**: así no se le revela en qué estado está una asignación que no puede tocar.
Si la acción ni siquiera existe en el flujo de la tarea (p. ej. `start` en el flujo `short`), no hay permisos que evaluar y la respuesta es **409**.
Todo rechazo ocurre antes de escribir, así que nunca modifica datos.
