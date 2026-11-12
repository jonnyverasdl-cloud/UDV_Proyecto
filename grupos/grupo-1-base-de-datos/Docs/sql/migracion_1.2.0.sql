-- migracion_1.2.0.sql | Grupo 1 - Base de datos | Workflow docente UDV
-- Catalogo prioridad_tarea y FK en tarea.prioridad (reemplaza el CHECK low/medium/high).
-- Se aplica sobre una base 1.1.0 que ya existe, sin perder datos:
--   mysql -u root db_udv < migracion_1.2.0.sql
-- Una base nueva no lo necesita: 01_schema.sql y 02_seed.sql ya traen el cambio.
USE db_udv;
SET NAMES utf8mb4;

CREATE TABLE prioridad_tarea (
    codigo  VARCHAR(20)       NOT NULL,
    nombre  VARCHAR(60)       NOT NULL,
    orden   TINYINT UNSIGNED  NOT NULL,
    activo  TINYINT(1)        NOT NULL DEFAULT 1,
    PRIMARY KEY (codigo),
    CONSTRAINT uq_prioridad_orden UNIQUE (orden)
) ENGINE=InnoDB;

INSERT INTO prioridad_tarea (codigo, nombre, orden) VALUES
('low', 'Baja', 1), ('medium', 'Media', 2), ('high', 'Alta', 3), ('urgent', 'Urgente', 4);

ALTER TABLE tarea DROP CONSTRAINT ck_tarea_prioridad;
ALTER TABLE tarea
    MODIFY prioridad VARCHAR(20) NOT NULL DEFAULT 'medium',
    ADD CONSTRAINT fk_tarea_prioridad FOREIGN KEY (prioridad) REFERENCES prioridad_tarea(codigo);

-- Vistas con el nombre de la prioridad (prioridad_nombre)
CREATE OR REPLACE VIEW v_inbox AS
SELECT
    td.id                AS asignacion_id,
    td.usuario_id,
    td.estado_codigo,
    et.nombre            AS estado_nombre,
    t.id                 AS tarea_id,
    t.titulo,
    tt.codigo            AS tipo_codigo,
    tt.nombre            AS tipo_nombre,
    t.prioridad,
    pt.nombre            AS prioridad_nombre,
    COALESCE(td.fecha_limite, t.fecha_limite) AS fecha_limite,
    t.publicada_en,
    td.asignado_en,
    td.actualizado_en,
    CONCAT(c.nombres, ' ', c.apellidos) AS creado_por_nombre,
    CASE WHEN COALESCE(td.fecha_limite, t.fecha_limite) < NOW(3) AND et.es_final = 0
              AND td.estado_codigo IN ('assigned', 'in_progress', 'returned') THEN 1 ELSE 0 END AS vencida,
    DATEDIFF(COALESCE(td.fecha_limite, t.fecha_limite), NOW()) AS dias_restantes,
    (SELECT COUNT(*) FROM entrega_borrador eb WHERE eb.tarea_destinatario_id = td.id) AS tiene_borrador,
    (SELECT COUNT(*) FROM comentario cm
      WHERE cm.tarea_destinatario_id = td.id AND cm.eliminado_en IS NULL) AS total_comentarios
FROM tarea_destinatario td
JOIN tarea        t  ON t.id = td.tarea_id
JOIN workflow     w  ON w.id = t.workflow_id
JOIN tipo_tarea   tt ON tt.id = w.tipo_tarea_id
JOIN estado_tarea et ON et.codigo = td.estado_codigo
JOIN usuario      c  ON c.id = t.creado_por
JOIN prioridad_tarea pt ON pt.codigo = t.prioridad
WHERE t.estado_codigo <> 'draft'
  AND t.eliminado_en IS NULL;

CREATE OR REPLACE VIEW v_panel_tarea AS
SELECT
    t.id            AS tarea_id,
    t.titulo,
    tt.nombre       AS tipo_nombre,
    t.estado_codigo AS estado_tarea,
    t.prioridad,
    pt.nombre       AS prioridad_nombre,
    t.creado_por,
    t.revisor_id,
    t.fecha_limite,
    COUNT(td.id)                                                      AS total_asignaciones,
    SUM(td.estado_codigo = 'assigned')                                AS asignadas,
    SUM(td.estado_codigo = 'in_progress')                             AS en_progreso,
    SUM(td.estado_codigo = 'submitted')                               AS entregadas,
    SUM(td.estado_codigo = 'under_review')                            AS en_revision,
    SUM(td.estado_codigo = 'returned')                                AS devueltas,
    SUM(td.estado_codigo IN ('approved', 'closed'))                   AS aprobadas,
    SUM(td.estado_codigo = 'cancelled')                               AS canceladas,
    SUM(COALESCE(td.fecha_limite, t.fecha_limite) < NOW(3) AND td.estado_codigo IN ('assigned', 'in_progress', 'returned')) AS vencidas,

    SUM(COALESCE(td.fecha_limite, t.fecha_limite) >= NOW(3)
        AND COALESCE(td.fecha_limite, t.fecha_limite) < NOW(3) + INTERVAL (SELECT CAST(valor AS UNSIGNED) FROM parametro WHERE codigo = 'dias_aviso_vencimiento') DAY
        AND td.estado_codigo IN ('assigned', 'in_progress', 'returned')) AS proximas_a_vencer,
    ROUND(100 * SUM(td.estado_codigo IN ('submitted', 'under_review', 'approved', 'closed'))
          / NULLIF(SUM(td.estado_codigo <> 'cancelled'), 0), 1)       AS porcentaje_cumplimiento
FROM tarea t
JOIN workflow w ON w.id = t.workflow_id
JOIN tipo_tarea tt ON tt.id = w.tipo_tarea_id
JOIN prioridad_tarea pt ON pt.codigo = t.prioridad
LEFT JOIN tarea_destinatario td ON td.tarea_id = t.id
WHERE t.eliminado_en IS NULL
GROUP BY t.id, t.titulo, tt.nombre, t.estado_codigo, t.prioridad, pt.nombre, t.creado_por, t.revisor_id, t.fecha_limite;

CREATE OR REPLACE VIEW v_historial_tarea AS
SELECT
    tr.id                AS transicion_id,
    td.tarea_id,
    td.id                AS asignacion_id,
    CONCAT(d.nombres, ' ', d.apellidos) AS destinatario,
    tr.estado_anterior,
    tr.estado_nuevo,
    tr.actor_id,
    CONCAT(a.nombres, ' ', a.apellidos) AS actor,
    tr.comentario,
    tr.creado_en,
    t.prioridad,
    pt.nombre            AS prioridad_nombre
FROM tarea_transicion tr
JOIN tarea_destinatario td ON td.id = tr.tarea_destinatario_id
JOIN tarea t ON t.id = td.tarea_id
JOIN prioridad_tarea pt ON pt.codigo = t.prioridad
JOIN usuario d ON d.id = td.usuario_id
JOIN usuario a ON a.id = tr.actor_id;

INSERT INTO schema_migracion (version, descripcion) VALUES
('1.2.0', 'Catalogo prioridad_tarea (low, medium, high, urgent) y FK en tarea.prioridad');
