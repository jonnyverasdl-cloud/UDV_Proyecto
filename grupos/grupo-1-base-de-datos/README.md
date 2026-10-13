# Grupo 1 · Base de datos

Base de datos del sistema de solicitudes a docentes (`db_udv`, versión 1.1.0). Motor: MariaDB 10.4 o superior (el que trae XAMPP).

## Contenido

```
Docs/
├─ sql/
│  ├─ db_udv_completo.sql   tablas, triggers, procedimientos, datos semilla y vistas
│  └─ triggers.sql          solo los triggers y procedimientos (para consulta)
├─ Diagramas/               diagramas entidad-relación en PDF
└─ diccionario/             diccionario de datos (abrir el .html en el navegador)
```

Para montar la base solo se usa `db_udv_completo.sql`. `triggers.sql` ya está incluido en ese archivo; no hay que ejecutarlo aparte.

## Montar la base

`db_udv_completo.sql` borra la base `db_udv` si ya existe y la crea desde cero.

### Con phpMyAdmin

1. En XAMPP, iniciar **MySQL**.
2. Abrir `http://localhost/phpmyadmin`.
3. Pestaña **Importar**, elegir `Docs/sql/db_udv_completo.sql` y pulsar **Importar**.

### Con la consola

Desde la carpeta `Docs/sql`:

```
mysql -u root < db_udv_completo.sql
```

Si el usuario `root` tiene contraseña, agregar `-p`.

### Comprobar que quedó bien

```sql
USE db_udv;
SELECT COUNT(*) FROM information_schema.tables
WHERE table_schema = 'db_udv' AND table_type = 'BASE TABLE';   -- 49
SELECT * FROM v_inbox WHERE usuario_id = 3;                     -- 2 tareas
```

## Usuarios de prueba

Todos con la contraseña `Demo2026!`.

| Correo | Rol |
|---|---|
| admin@demo.udv.edu.gt | admin |
| coordinacion@demo.udv.edu.gt | coordinator |
| docente1@demo.udv.edu.gt | teacher |
| docente2@demo.udv.edu.gt | teacher |
| docente3@demo.udv.edu.gt | teacher |
| revisor@demo.udv.edu.gt | reviewer y teacher |
| direccion@demo.udv.edu.gt | authority |
| auditoria@demo.udv.edu.gt | auditor |

## Respaldo y restauración

Respaldar:

```
mysqldump -u root --routines --triggers db_udv > respaldo_db_udv.sql
```

Restaurar:

```
mysql -u root -e "CREATE DATABASE IF NOT EXISTS db_udv CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
mysql -u root db_udv < respaldo_db_udv.sql
```

`--routines --triggers` es obligatorio. Sin esas opciones el respaldo pierde los triggers y procedimientos.

## Lo que deben saber los otros grupos

- Identificadores enteros (`INT AUTO_INCREMENT`).
- Estados en inglés y minúsculas, como en `CONTRATO_COMUN.md`.
- Roles: `admin`, `coordinator`, `teacher`, `reviewer`, `authority`, `auditor`.
- Nada con historial se borra con `DELETE`: se marca `eliminado_en` y `eliminado_por`.
- Después de autenticar, la API ejecuta `SET @actor_id = <id del usuario>;` en la conexión. Así la auditoría guarda quién hizo cada cambio.
- Los errores de las reglas usan `SQLSTATE 45000` y el mensaje indica el código HTTP que corresponde (409 o 422).

| Grupo | Qué usa |
|---|---|
| G2 | `usuario`, `rol`, `permiso`, `usuario_rol`, `rol_permiso`, `sesion_token`, `auditoria` |
| G3 | `tarea`, `tarea_destinatario`, `tarea_transicion`, `workflow_detalle`, `entrega`. Publicar: `CALL sp_publicar_tarea(tarea_id, actor_id)` |
| G4 | Vistas `v_inbox`, `v_panel_tarea`, `v_historial_tarea` |
| G5 | `programa_curso`, `programa_version` y su contenido. Autorizar: `CALL sp_autorizar_version(version_id, actor_id, comentario)`. Vistas `v_programa_vigente`, `v_programa_versiones` |
| G6 | `evento`, `notificacion`, `parametro`, catálogos. Vista `v_evento_pendiente`. Avisos de vencimiento: `CALL sp_generar_eventos_vencimiento(@creados)` |

Cambiar el estado de una asignación (G3), dentro de una transacción:

1. `INSERT` en `tarea_transicion` con el estado actual como `estado_anterior`.
2. `UPDATE tarea_destinatario SET estado_codigo = ...`.

Si la transición no existe en el workflow, la base la rechaza.

## Índices

| Índice | Consulta que acelera |
|---|---|
| `tarea_destinatario (usuario_id, estado_codigo, asignado_en)` | Inbox del docente |
| `tarea_destinatario (tarea_id, estado_codigo)` | Panel de cumplimiento por tarea |
| `tarea_transicion (tarea_destinatario_id, creado_en)` | Historial de una asignación |
| `tarea (creado_por, estado_codigo, creado_en)` | Tareas de un coordinador |
| `tarea (revisor_id, estado_codigo)` | Pendientes de un revisor |
| `programa_version (estado_codigo)` | Versiones por estado |
| `programa_aprobacion (programa_version_id, creado_en)` | Historial de aprobación de un programa |
| `notificacion (usuario_id, leida_en, creado_en)` | Notificaciones no leídas |
| `evento (procesado_en, id)` | Eventos pendientes de notificar |
| `auditoria (tabla, registro_id, creado_en)` | Auditoría de un registro |
| `sesion_token (usuario_id, expira_en)` | Sesiones activas de un usuario |

## Cambios de la versión 1.1.0

- Se eliminó `tarea.tipo_tarea_id`. El tipo de una tarea se obtiene por `tarea.workflow_id → workflow.tipo_tarea_id`.
- Nuevo catálogo `perfil_egreso`. `programa_perfil_egreso` guarda `perfil_egreso_id` en lugar del código escrito a mano.
- Nuevas tablas: `modalidad`, `area`, `docente_curso`, `flujo_programa`, `tarea_seleccion`, `entrega_borrador`, `evento`, `programa_pdf`, `workflow_detalle_rol`.
