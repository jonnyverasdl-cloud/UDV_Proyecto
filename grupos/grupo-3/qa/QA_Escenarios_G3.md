#  Plan de Pruebas QA - Grupo 3 (Workflow)

**Estado Actual:**  BLOQUEADO (En espera de Desarrollo)

##  Hallazgos en el Repositorio Oficial (Rama `grupo-3`)
Al auditar la rama oficial de desarrollo, se detecta que aún no se aplican los requerimientos del PM, lo que bloquea la ejecución de pruebas:
1. **Estructura incorrecta:** El código sigue en la raíz (`workflow_g3/`) y no en `grupos/grupo-3-workflow-tareas/g3_workflow/`.
2. **Archivos prohibidos:** El archivo de base de datos SQLite (`workflow.db`) sigue expuesto en el repositorio.
3. **Falta de actualización:** El último commit fue la semana pasada. No hay evidencia de la migración a MySQL ni del prefijo `/api/v1`.

##  Preparación de QA (Completada)
Se ha diseñado y configurado la colección de Postman localmente. Se ejecutará en cuanto el servidor esté levantado.

| Prueba | Acción | Método | Endpoint Objetivo | Estado QA |
|---|---|---|---|---|
| QA-WF-01 | Crear Tarea | POST | `/api/v1/tasks` |  Pendiente servidor |
| QA-WF-02 | Asignar Destinatarios | POST | `/api/v1/tasks/{tid}/recipients` | Pendiente servidor |
| QA-WF-03 | Publicar Tarea | POST | `/api/v1/tasks/{tid}/publish` |  Pendiente servidor |
| QA-WF-04 | Iniciar Tarea | POST | `/api/v1/assignments/{aid}/actions/start` |  Pendiente servidor |
| QA-WF-05 | Devolver Tarea | POST | `/api/v1/assignments/{aid}/actions/return` |  Pendiente servidor |
| QA-WF-06 | Cancelar Tarea | POST | `/api/v1/tasks/{tid}/cancel` |  Pendiente servidor |

##  Vulnerabilidades a Validar (Pruebas de Seguridad)
Una vez el sistema esté funcional, QA forzará los siguientes fallos críticos detectados en la revisión de código:
* **Suplantación de Identidad (IDOR):** Se manipulará el header `X-User-Id` usando el valor `1` (Coordinador) y `7` (Docente) para intentar inyectar tareas sin validación real de sesión.
* **Invasión de Endpoints:** Se forzará la ruta `/inbox` para verificar si el Grupo 3 sigue invadiendo el territorio del Grupo 4.
* **Crash por Prioridad:** Se enviará el valor no soportado `"priority": "urgent"` para documentar la caída del servicio.
