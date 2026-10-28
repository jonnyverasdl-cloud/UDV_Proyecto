# Grupo 1 · Base de datos

Base de datos del sistema de solicitudes a docentes (`db_udv`, versión 1.2.0). Motor: MySQL 8.0 o superior, o MariaDB 10.4 o superior (el que trae XAMPP).

## Contenido

```
g1_bd/                      comandos en Python para crear y verificar la base
Docs/
├─ sql/
│  ├─ 01_schema.sql         tablas, triggers, procedimientos y vistas
│  ├─ 02_seed.sql           datos semilla (catálogos, roles, usuarios demo, ejemplos)
│  ├─ triggers.sql          solo los triggers y procedimientos (para consulta)
│  ├─ verificacion.sql      pruebas de las restricciones
│  └─ migracion_1.2.0.sql   pasa una base 1.1.0 a 1.2.0 sin perder datos
├─ Diagramas/               diagramas entidad-relación en PDF
└─ diccionario/
   ├─ diccionario_db_udv.html   diccionario de datos (abrir en el navegador)
   ├─ generar_diccionario.py    vuelve a generar el .html leyendo la base
   ├─ descripciones.py          textos de cada tabla y columna
   └─ plantilla.html            diseño de la página
```

Para montar la base se usan `01_schema.sql` y luego `02_seed.sql`, en ese orden. `triggers.sql` ya está incluido en `01_schema.sql`; no hay que ejecutarlo aparte.

## Montar la base

`01_schema.sql` borra la base `db_udv` si ya existe y la crea desde cero. `02_seed.sql` carga los datos.

### Con phpMyAdmin

1. En XAMPP, iniciar **MySQL**.
2. Abrir `http://localhost/phpmyadmin`.
3. Pestaña **Importar**, elegir `Docs/sql/01_schema.sql` y pulsar **Importar**.
4. Repetir con `Docs/sql/02_seed.sql`.

### Con Docker (entorno del proyecto)

El `docker-compose.yml` de la raíz levanta MySQL 8 y carga estos scripts la primera vez. Para volver a crear la base desde cero: `docker compose down -v && docker compose up --build`.

### Con Python (paquete g1_bd)

Desde la carpeta del grupo:

```
pip install -r requirements.txt
python -m g1_bd crear --host localhost --port 3306 --user root --password <clave>
python -m g1_bd verificar --host localhost --port 3306 --user root --password <clave>
```

`crear` corre `01_schema.sql` y `02_seed.sql` y muestra cuántas tablas, vistas, triggers y procedimientos quedaron. `verificar` corre `verificacion.sql` y debe terminar con `pasan 75, fallan 0`. Si existe la variable `DATABASE_URL` (`mysql+pymysql://usuario:clave@host:puerto/db_udv`), se puede omitir `--host` y lo demás.

### Con la consola

Desde la carpeta `Docs/sql`:

```
mysql -u root < 01_schema.sql
mysql -u root < 02_seed.sql
```

Si el usuario `root` tiene contraseña, agregar `-p`.

### Comprobar que quedó bien

```sql
USE db_udv;
SELECT COUNT(*) FROM information_schema.tables
WHERE table_schema = 'db_udv' AND table_type = 'BASE TABLE';   -- 50
SELECT * FROM v_inbox WHERE usuario_id = 3;                     -- 2 tareas
```

### Pruebas de las restricciones

`verificacion.sql` intenta cosas que la base debe rechazar (correo repetido, dos versiones vigentes, modificar una versión autorizada, borrar historial, transiciones que no existen, etc.) y otras que debe aceptar. Corre todo dentro de una transacción y al final la deshace, así que no cambia los datos.

En phpMyAdmin: seleccionar `db_udv`, pestaña **SQL**, pegar el contenido del archivo y pulsar **Continuar**. Desde la consola:

```
mysql -u root db_udv < verificacion.sql
```

La primera fila del resultado debe decir `pasan 75, fallan 0`. Las demás filas muestran cada prueba con su resultado.

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

## Migrar

La tabla `schema_migracion` guarda qué versiones del esquema tiene aplicadas la base:

```sql
SELECT * FROM schema_migracion;
```

Para cambiar el esquema más adelante:

1. Crear un script nuevo en `Docs/sql` con la versión en el nombre, por ejemplo `migracion_1.2.0.sql`. Solo lleva el cambio (`ALTER TABLE`, `CREATE TABLE`, triggers nuevos), no la base completa.
2. Al final del script, registrar la versión:

   ```sql
   INSERT INTO schema_migracion (version, descripcion) VALUES ('1.2.0', 'Qué cambió');
   ```

3. Aplicarlo sobre la base que ya existe: `mysql -u root db_udv < migracion_1.2.0.sql`. No hace falta borrar la base ni perder datos.
4. Actualizar también `01_schema.sql` (o `02_seed.sql` si son datos), el diccionario y el diagrama, para que quien monte la base desde cero ya tenga el cambio.
5. Avisar a los grupos afectados antes de renombrar o quitar una tabla o columna.

| Versión | Script | Cambio |
|---|---|---|
| 1.2.0 | `migracion_1.2.0.sql` | Catálogo `prioridad_tarea` (low, medium, high, urgent). `tarea.prioridad` pasa de un `CHECK` a una llave foránea (`fk_tarea_prioridad`). Las vistas `v_inbox`, `v_panel_tarea` y `v_historial_tarea` agregan `prioridad_nombre`. |

Quien ya tiene la base 1.1.0 montada corre `mysql -u root db_udv < migracion_1.2.0.sql`. Quien la monta desde cero no lo necesita: `01_schema.sql` y `02_seed.sql` ya traen el cambio.

## Eliminación lógica

Lo que tiene historial no se borra con `DELETE`. La base lo impide con triggers: si alguien intenta un `DELETE`, devuelve un error.

| Tablas | Cómo se "borra" |
|---|---|
| `usuario`, `curso`, `tarea`, `comentario`, `archivo` | Se llenan `eliminado_en` (fecha) y `eliminado_por` (usuario). Las consultas filtran `eliminado_en IS NULL`. |
| `tarea_destinatario` | Se pasa a estado `cancelled` con su transición. |
| `programa_curso`, `programa_version` | No se borran. Una versión vieja queda como `superseded` cuando se autoriza la nueva. |
| `entrega`, `entrega_valor`, `notificacion`, `programa_pdf`, `evento` | No se borran nunca. |
| `tarea_transicion`, `programa_aprobacion`, `auditoria` | Historial: no se modifican ni se borran. |

El contenido de un programa (competencias, unidades, bibliografía, evaluación, prerrequisitos, perfil de egreso) sí se puede editar y borrar mientras la versión está en borrador. Cuando la versión se autoriza queda bloqueada y cualquier cambio da error.

## Diccionario de datos

`Docs/diccionario/diccionario_db_udv.html` se genera con `generar_diccionario.py`, que lee la estructura real de la base (tablas, columnas, llaves, restricciones, índices y triggers) y le agrega los textos de `descripciones.py`.

Después de cambiar el esquema, con la base ya montada:

```
pip install -r requirements.txt
cd Docs/diccionario
python generar_diccionario.py --host localhost --port 3306 --user root --password <clave>
```

Con el Docker del proyecto el puerto es `3307`. Hay que usar `root` u otro usuario que pueda ver los triggers; con un usuario de solo lectura el diccionario sale sin ellos. Si una tabla o columna nueva no tiene texto, el script lo avisa: se agrega en `descripciones.py` y se vuelve a correr.

## Lo que deben saber los otros grupos

- Identificadores enteros (`INT AUTO_INCREMENT`).
- Estados en inglés y minúsculas, como en `CONTRATO_COMUN.md`.
- Roles: `admin`, `coordinator`, `teacher`, `reviewer`, `authority`, `auditor`.
- Prioridades de tarea: `low`, `medium`, `high`, `urgent`, del catálogo `prioridad_tarea`. Una prioridad que no esté en el catálogo se rechaza. Las vistas traen además `prioridad_nombre` (Baja, Media, Alta, Urgente).
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
| `tarea_destinatario (usuario_id, fecha_limite)` | Asignaciones por vencer en la bandeja del docente |
| `tarea_destinatario (revisor_id, estado_codigo)` | Asignaciones pendientes de un revisor |
| `tarea_transicion (tarea_destinatario_id, creado_en)` | Historial de una asignación |
| `tarea (creado_por, estado_codigo, creado_en)` | Tareas de un coordinador |
| `tarea (revisor_id, estado_codigo)` | Pendientes de un revisor |
| `tarea (eliminado_en, estado_codigo, fecha_limite)` | Tareas vigentes por estado y plazo |
| `tarea (prioridad, fecha_limite)` | Búsqueda por prioridad y fecha límite |
| `programa_version (estado_codigo)` | Versiones por estado |
| `programa_aprobacion (programa_version_id, creado_en)` | Historial de aprobación de un programa |
| `notificacion (usuario_id, leida_en, creado_en)` | Notificaciones no leídas |
| `evento (procesado_en, id)` | Eventos pendientes de notificar |
| `auditoria (tabla, registro_id, creado_en)` | Auditoría de un registro |
| `sesion_token (usuario_id, expira_en)` | Sesiones activas de un usuario |
