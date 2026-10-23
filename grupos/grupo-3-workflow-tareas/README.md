# Grupo 3 - Motor de workflow y tareas

Tareas, asignaciones por docente y su flujo de estados. Expone un `APIRouter` con prefijo `/api/v1`
(no crea su propia app): el `main.py` de la raíz lo monta.

## Montar en el main.py de la raíz

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent / "grupos" / "grupo-3-workflow-tareas"))
from workflow.api import router as workflow_router

app.include_router(workflow_router)
```

(Ajustar a la forma en que ya montan G2, G4 y G6.) El router da los errores en el formato del
CONTRATO_COMUN por sí solo; para 404/405 de rutas que no existen se puede usar el manejador de G2
o `workflow.http_errors.register_error_handlers(app)`.

## Configuración

- `DATABASE_URL` en el `.env` (ver `.env.example`): `mysql+pymysql://user:clave@host:3306/bd`.
- Usuario: sale del token de login de G2 (`workflow/auth.py`). Tras identificarlo se hace
  `SET @actor_id` para la auditoría de G1.

## Tests

```bash
cd grupos/grupo-3-workflow-tareas
pip install -r requirements.txt
pytest
```

Los tests usan SQLite en memoria y no necesitan MySQL. Los de `tests/test_api.py` se saltan solos si
`fastapi`/`httpx` no están instalados: instala `requirements.txt` antes para que cuenten de verdad.

## Orden de validación en las acciones

La lógica vive en `workflow/transitions.py` (`perform`). Siempre en este orden:

| Orden | Chequeo | Error |
| --- | --- | --- |
| 1 | La asignación existe | 404 |
| 2 | El usuario tiene permiso (rol y destinatario / revisor / coordinador correcto) | 403 |
| 3 | El estado actual permite la acción | 409 |
| 4 | Viene el comentario obligatorio | 422 |

La matriz completa está en `docs/matriz_estados.md` (se regenera con `python -m workflow.matrix`).
Las tablas de transiciones para el CONTRATO están en `docs/contrato_g3_transiciones.md`.
