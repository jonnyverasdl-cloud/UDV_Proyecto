# Transiciones de asignación (para pegar en el CONTRATO.md de G3)

Las 6 acciones de asignación ahora son del **Grupo 3** (antes figuraban como de G4).
Todas son `POST /api/v1/assignments/{id}/<accion>`, con cuerpo opcional `{"comment": "..."}`.
El usuario sale del token de G2; la respuesta es la asignación actualizada.

| Endpoint | Estado actual | Estado nuevo | Quién puede | Notas |
| --- | --- | --- | --- | --- |
| `POST /assignments/{id}/start` | assigned | in_progress | Docente destinatario | |
| `POST /assignments/{id}/submit` | in_progress | submitted | Docente destinatario | Flujo `short`: desde assigned |
| `POST /assignments/{id}/resubmit` | returned | submitted | Docente destinatario | |
| `POST /assignments/{id}/review` | submitted | under_review | Revisor designado | |
| `POST /assignments/{id}/return` | under_review | returned | Revisor designado | `comment` obligatorio (422 si falta) |
| `POST /assignments/{id}/approve` | under_review | approved | Revisor designado o Autoridad | Flujo `short`: desde submitted |

Errores (formato `{"error": {"code", "message", "details"}}`), en este orden:
404 la asignación no existe · 403 sin permiso · 409 el estado actual no permite la acción · 422 falta el comentario obligatorio.

`close` y `cancel` siguen disponibles por la ruta genérica `POST /assignments/{id}/actions/{accion}` (marcada como deprecated).
La matriz completa está en `docs/matriz_estados.md`.
