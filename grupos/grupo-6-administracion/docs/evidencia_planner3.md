# Evidencia del Planner No.3 (04-nov-2026)

Se probó con `main` del repositorio original en `de5c6ae` (ya monta el G3 y el
G6) más los cambios de esta versión del G6 (0.4.1). MySQL 8.0 vacío, base
creada con `python -m g1_bd crear`. La prueba de punta a punta usa el
`main.py` de la raíz tal cual: login del G2, workflow del G3 y rutas del G6.

## Resultados por escenario

| Escenario | Cómo se verificó | Resultado |
|---|---|---|
| G6-04 (tarea publicada) | `test_flujo_e2e.py`: coordinación crea y publica una tarea con el G3 | Al docente le llega un aviso |
| G6-05 (por vencer) | La misma tarea vence en 2 días; al consultar, el G6 llama a `sp_generar_eventos_vencimiento` del G1 | Al docente le llega un aviso |
| G6-06 (entregada) | El docente empieza y entrega | Al revisor le llega un aviso |
| G6-07 (devuelta) | El revisor revisa y devuelve con observación | Al docente le llega con la observación |
| G6-08 (aprobada) | El docente reenvía; el revisor revisa y aprueba | Le llega al docente y a coordinación |
| G6-09 (programa autorizado) | La semilla del G1 autoriza el programa 1 y su trigger deja el evento | Le llega al docente responsable y a coordinación. Las rutas de programas son del G5 y aún no están montadas en `main.py` |
| G6-10 (cancelada) | Coordinación cancela una tarea publicada | Al docente le llega un aviso |
| G6-11 (sin duplicados) | Consultar otra vez y `POST /notifications/process` | No se repite ningún aviso; otro docente no recibe nada de esa tarea |
| G6-12 y G6-13 (marcar leída) | El dueño marca su aviso; otro docente intenta marcarlo | El dueño: 200 y queda leída. El otro: 404 y no cambia nada |
| G6-14 (acciones) | `test_auditoria.py` y `test_mysql_g1.py` | Cada alta y cambio de catálogo queda con quién, cuándo y qué cambió |
| G6-15 (transiciones) | `GET /api/v1/audit?action=transition&entity=tarea_destinatario` después del flujo | Aparecen las 8 transiciones en orden, con quién hizo cada una. Antes salía vacío porque el G3 guarda su historial en `tarea_transicion` |
| G6-16 (flujo completo) | El flujo de arriba, de crear a aprobar, incluido el reenvío de la entrega devuelta | Pasa completo. Ver la nota de Railway abajo |
| G6-18 (nada a medias) | Aprobar sin revisar (409) y un docente que intenta devolver (403) | El historial y los avisos quedan igual que antes. Además, `test_transacciones.py` y `test_eventos.py` |
| G6-37 a G6-40 | Hechos en el Planner No.2 (`evidencia_planner2.md`) | Sin cambios |

## Pruebas automáticas

| Conjunto | Resultado |
|---|---|
| `python -m pytest` (sin MySQL) | 252 pasan, 21 se omiten (las de MySQL) |
| `python -m pytest tests/integracion` con `G6_MYSQL_URL` | 21 pasan en una base nueva, y vuelven a pasar si se corren otra vez en la misma base |
| `python -m g6_admin.regresion` contra `uvicorn main:app` | 24 de 24 |

Para comprobar que la prueba de punta a punta de verdad revisa la auditoría,
se quitó a propósito la lectura del historial del G3: la prueba falló al no
encontrar las 8 transiciones.

## Nota sobre Railway (G6-16)

QA recibió un 409 al reenviar una entrega devuelta (`returned → submitted`).
Con una base nueva desde `main` el reenvío funciona, así que el código del G1
y del G3 está bien. El G3 responde ese 409 cuando el workflow de la tarea no
tiene la fila `returned → submitted` en `workflow_detalle`; la semilla del G1
sí la trae. El G1 o el PM pueden revisar la base de Railway con esta consulta,
que solo lee:

```sql
SELECT w.id, w.nombre FROM workflow w
WHERE NOT EXISTS (SELECT 1 FROM workflow_detalle wd WHERE wd.workflow_id = w.id
  AND wd.estado_origen = 'returned' AND wd.estado_destino = 'submitted');
```

Si devuelve filas, a esos workflows les falta la transición de la semilla del G1.

## Cómo repetirlo

En una base de pruebas, nunca la compartida (la prueba crea tareas):

```bash
cd grupos/grupo-1-base-de-datos
python -m g1_bd crear --host 127.0.0.1 --port 3306 --user root --password <clave>
cd ../grupo-6-administracion
set G6_MYSQL_URL=mysql+pymysql://root:<clave>@127.0.0.1:3306/db_udv
python -m pytest tests/integracion
```
