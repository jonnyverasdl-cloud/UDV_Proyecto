# Evidencia del Planner No.2 (28-oct-2026)

Se probó con `main` del repositorio original en `3dc943c` (ya trae el G2), esta
versión del G6 (0.4.0) y la línea del G6 activada en `main.py` solo en la copia
de prueba. MySQL 8.0 vacío, base creada con `python -m g1_bd crear`.

## Resultados por escenario

| Escenario | Cómo se verificó | Resultado |
|---|---|---|
| G6-21 a G6-25 (crear unidad académica, sede, curso, período, modalidades y áreas) | `tests/integracion`: login real del G2, `POST` y `PATCH` sobre las tablas del G1 en MySQL, con su registro de auditoría | Pasa. Era lo que el retest del 25-oct dejó como "pendiente integración con BD G1 y autenticación G2" |
| G6-34 (`/health`) | `GET /api/v1/health` con `DATABASE_URL` de MySQL | `"database": "ok"`, versión `0.4.0` y commit. Antes salía `not_configured` porque no había base configurada |
| G6-26 (tareas por estado) | `test_panel.py` con datos armados a mano; en MySQL, contra `SELECT ... GROUP BY estado_codigo` | Coincide |
| G6-27 y G6-28 (vencidas y próximas) | `test_panel.py` (bordes: entregadas, fecha propia de la asignación, justo al final del plazo, tarea eliminada o cancelada); en MySQL, contra `v_panel_tarea` | Coincide |
| G6-29 (cumplimiento) | `test_panel.py`; en MySQL, contra `v_panel_tarea` | Coincide |
| G6-30 a G6-33 (filtros de auditoría) | `test_auditoria.py` (usuario, entidad, acción, fecha con los bordes del día, combinados, 422 con filtros inválidos); en MySQL con el login real | Pasa. El rol `auditor` también consulta; `coordinator`, `reviewer` y `authority` reciben 403 |
| G6-37 (archivos tras reiniciar) | `python -m g6_admin.persistencia marcar` / `comprobar` (`test_persistencia.py`) | La herramienta funciona. **Hallazgo:** hoy la app no tiene volumen y el G2 no usa `UPLOAD_DIR` (ver `recuperacion.md`) |
| G6-38 (recuperación) | Respaldo con `mysqldump`, restauración en otro MySQL y la API apuntando a la restaurada | Iguales en tablas, vistas, triggers, rutinas y datos; regresión 24 de 24 |
| G6-39 (versión final) | `/api/v1/health` muestra versión y commit; `docs/version_final.md` | Listo para que el PM ponga la etiqueta |
| G6-40 (regresión) | `python -m g6_admin.regresion --url http://127.0.0.1:8000` contra `uvicorn main:app` | 24 de 24 casos pasan |

## Pruebas automáticas

| Conjunto | Resultado |
|---|---|
| `python -m pytest` (sin MySQL) | 250 pasan, 16 se omiten (las de MySQL) |
| `python -m pytest tests/integracion` con `G6_MYSQL_URL` | 16 pasan en una base nueva (el del período se omite si ya se corrió en la misma base) |

Sin la advertencia de clave HMAC corta del retest (hallazgo 06): ahora una
clave de menos de 32 caracteres hace fallar las pruebas.

## Salida de la regresión

```
  ✓ G6-34      La API y la base responden en /api/v1/health
  ✓ G6-01      Sin sesión no se ven los catálogos (401)
  ✓ G2         Inicia sesión administración (admin@demo.udv.edu.gt)
  ✓ G2         Inicia sesión docente (docente1@demo.udv.edu.gt)
  ✓ G6-21..25  El docente consulta academic-units
  ✓ G6-21..25  El docente consulta campuses
  ✓ G6-21..25  El docente consulta courses
  ✓ G6-21..25  El docente consulta periods
  ✓ G6-21..25  El docente consulta modalities
  ✓ G6-21..25  El docente consulta areas
  ✓ G6-02      El docente no puede agregar a un catálogo (403)
  ✓ G6-04..13  El docente ve sus notificaciones
  ✓ G6-26..29  Administración ve el panel
  ✓ G6-26      Las tareas por estado suman el total
  ✓ G6-26      Las asignaciones por estado suman el total
  ✓ G6-27      Cada vencida ya pasó su fecha límite
  ✓ G6-28      Cada próxima a vencer está dentro del plazo de aviso
  ✓ G6-29      El cumplimiento es entregadas entre esperadas
  ✓ G6-26..29  El docente no ve el panel (403)
  ✓ G6-30      La auditoría filtra con user_id=1
  ✓ G6-31      La auditoría filtra con from=2026-10-28
  ✓ G6-32      La auditoría filtra con entity=usuario
  ✓ G6-33      La auditoría filtra con action=LOGIN_OK
  ✓ G6-30..33  El docente no consulta la auditoría (403)

24 de 24 casos pasaron en http://127.0.0.1:8000.
```

## Pantallas

`panel.html` y `auditoria.html` se probaron en Chromium a 1280 px y a 390 px
(teléfono), con admin, auditor y docente: sin errores en la consola y sin
desplazamiento horizontal. El docente ve el aviso de que no tiene permiso.

## Hallazgos para otros grupos

- **G1:** `v_panel_tarea` usa `NOW(3)`, que depende de la zona horaria del
  servidor; con `TZ: America/Guatemala` (como en `docker-compose.yml`) se
  corre 6 horas. Además, cancelar una tarea no cambia sus asignaciones, así que
  la vista cuenta como vencidas las de una tarea cancelada. El panel del G6 ya
  las excluye (ver `panel.md`).
- **G2:** `files.py` no usa `UPLOAD_DIR` (ver `recuperacion.md`).
- **PM:** la línea del G6 sigue comentada en `main.py` y falta servir
  `/g6`; volumen para archivos (ver los pedidos del README del G6).
