# Grupo 4 - Inbox y entregas

Este es el módulo del inbox, el detalle de las asignaciones, la entrega
y la revisión. Lo armamos entre Isai (inbox), Elmer (detalle/entrega/
revisión) y yo (backend e integración).

## Cómo correrlo

```
cd grupo-4-inbox-entregas
pip install -r requirements.txt
set PYTHONPATH=<ruta a tu copia de grupo-2-api-seguridad>;.
set SECRET_KEY=lo-que-sea-para-pruebas
uvicorn g4_inbox.main:app --reload --app-dir .
```

Abre `http://127.0.0.1:8000/api/v1/docs`. Para probar cualquier cosa
primero hay que hacer login (`POST /api/v1/auth/login`) 


Y para ver las pantallas: `http://127.0.0.1:8000/static/inbox.html`.
Si se ve sin estilos, agrega `G4_STANDALONE_DEV=1` al correr el
servidor (eso trae el CSS institucional solo para pruebas locales, en
producción lo sirve la app principal).

## Cómo está armado

- `g4_inbox/inbox.py` y `datos_ejemplo.py` .
- `g4_inbox/routes.py` - el router que de verdad se monta en el
  proyecto completo: inbox, detalle, borrador, comentarios, archivos.
  Nada más.
- `g4_inbox/acciones.py` - las seis transiciones (iniciar, entregar,
  revisar, aprobar, devolver, reenviar). Desde el 21 de octubre esto ya
  no es nuestro, es de G3, así que este router no se monta en
  producción. Lo dejamos aparte para poder seguir probando el flujo
  completo en nuestras pruebas, y es el archivo que le pasamos a G3
  como referencia.
- `g4_inbox/database.py` - conexión real a MySQL (las vistas de G1:
  `v_inbox`, `v_historial_tarea`, etc). Se activa con
  `G4_USAR_MYSQL=1` y una `DATABASE_URL` en el `.env`. Si no está
  prendido, usa los datos de prueba en memoria.
- `g4_inbox/main.py` - solo sirve para correr G4 por su cuenta en
  local. La raíz del proyecto usa `routes.py` directo, no este archivo.
- `static/` - las dos pantallas, con sus propios css y js.

## Cosas que hay que tener en cuenta

El inbox ahora exige un token real de G2 (`obtener_usuario_actual`) y
ya no un header inventado. Esto significa que G4 no arranca si no
tiene el código de G2 al lado, en el `PYTHONPATH` - es a propósito, fue
un hueco de seguridad que nos encontraron en la prueba de integración
del PM (cualquiera podía ver las tareas de otro cambiando un header).

La validación de "requiere evidencia" sale de la tabla `tipo_tarea` de
G1, no está puesta a mano - solo algunas tareas piden archivo
obligatorio.

La tabla de transiciones que usamos en `acciones.py` es una copia de
lo que dice el contrato


## Pruebas

```
pytest tests/ -v
```

17 pruebas
