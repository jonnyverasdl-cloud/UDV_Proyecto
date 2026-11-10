# Plan de Pruebas QA - Grupo 3 (Workflow)

**Estado Actual:** En Ejecución / Pruebas E2E Completadas

## Hallazgos en la Infraestructura Inicial (Superados)
Se logró establecer conexión con la API y ejecutar el flujo completo, superando los bloqueos iniciales. Se recomienda al equipo de desarrollo limpiar el repositorio oficial (remover `workflow.db` expuesto y mover el código a `grupos/grupo-3-workflow-tareas/g3_workflow/`).

## Flujo de Pruebas Ejecutadas (End-to-End)
Se validó la máquina de estados y las rutas reales implementadas por el equipo de desarrollo. El flujo End-to-End (E2E) se ejecutó con éxito desde la creación hasta la aprobación final.

| Prueba | Acción | Rol | Método | Endpoint Objetivo | Estado QA |
|---|---|---|---|---|---|
| QA-WF-01 | Crear Tarea | Coordinador | POST | `/api/v1/tasks` |  Completado (Bug de duplicidad) |
| QA-WF-02 | Asignar Destinatarios | Coordinador | POST | `/api/v1/tasks/{task_id}/recipients` |  Completado |
| QA-WF-03 | Publicar Tarea | Coordinador | POST | `/api/v1/tasks/{task_id}/publish` |  Completado |
| QA-WF-04 | Iniciar Tarea | Docente | POST | `/api/v1/assignments/{assignment_id}/start` |  Completado |
| QA-WF-05 | Entregar Tarea | Docente | POST | `/api/v1/assignments/{assignment_id}/submit` |  Completado |
| QA-WF-06 | Iniciar Revisión | Revisor | POST | `/api/v1/assignments/{assignment_id}/review` |  Completado |
| QA-WF-07 | Devolver Tarea | Revisor | POST | `/api/v1/assignments/{assignment_id}/return` |  Completado (Exige comentario) |
| QA-WF-08 | Re-entregar Tarea | Docente | POST | `/api/v1/assignments/{assignment_id}/resubmit` |  Completado |
| QA-WF-09 | Aprobar Tarea | Revisor | POST | `/api/v1/assignments/{assignment_id}/approve` |  Completado |

## Hallazgos y Validaciones de Seguridad y Lógica

1. **Máquina de Estados (Validación Exitosa):** 
   El sistema protege correctamente el ciclo de vida de la tarea. Se validó que devuelve error `409 Conflict` (invalid_transition) si se intenta saltar pasos obligatorios, como intentar hacer un `submit` sin antes dar `start`, o intentar hacer un `return/approve` sin que el revisor haya marcado la entrega en `review`.

2. **Seguridad y Control de Acceso (Validación Exitosa):**
   Se comprobó que los endpoints están correctamente protegidos por roles. Se obtuvo un error `403 Forbidden` al intentar acceder a tareas de otros usuarios o ejecutar acciones sin los permisos correspondientes.

3. **Validación de Reglas de Negocio (Validación Exitosa):**
   El sistema exige correctamente justificaciones en acciones críticas. Por ejemplo, se bloquea con error `422` si el Revisor intenta devolver (`return`) una tarea sin adjuntar un comentario o motivo.

4. ** BUG CRÍTICO DETECTADO: Duplicidad de Tareas**
   El backend no realiza validaciones de unicidad al momento de crear tareas. El coordinador puede enviar el mismo payload varias veces creando múltiples tareas idénticas que, al aplicar la regla `"mode": "all"`, inundan la bandeja de los docentes con copias exactas del mismo trabajo. (Ver reporte de Bug en el ticket correspondiente).
