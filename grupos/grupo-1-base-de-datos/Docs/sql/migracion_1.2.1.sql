-- migracion_1.2.1.sql | Grupo 1 - Base de datos | Workflow docente UDV
-- Se aplica sobre una base 1.2.0 que ya existe, sin perder datos:
--   mysql -u root db_udv < migracion_1.2.1.sql
-- Una base nueva no lo necesita: 01_schema.sql ya trae el cambio.
-- Cambios (no hay tablas ni columnas nuevas):
--   1. Los triggers de auditoria y eventos tratan @actor_id = 0 como NULL (antes fallaba fk_auditoria_actor).
--   2. sp_publicar_tarea deja el actor (p_actor_id) en el evento task.published si la API no fijo @actor_id.
--   3. Los scripts trabajan en UTC (SET time_zone = '+00:00').
USE db_udv;
SET NAMES utf8mb4;
SET time_zone = '+00:00';

DROP TRIGGER IF EXISTS trg_tarea_evento;
DROP TRIGGER IF EXISTS trg_tarea_audit_ai;
DROP TRIGGER IF EXISTS trg_tarea_audit_au;
DROP TRIGGER IF EXISTS trg_pv_audit_ai;
DROP TRIGGER IF EXISTS trg_pv_audit_au;
DROP TRIGGER IF EXISTS trg_usuario_audit_ai;
DROP TRIGGER IF EXISTS trg_usuario_audit_au;
DROP PROCEDURE IF EXISTS sp_publicar_tarea;

DELIMITER $$

CREATE TRIGGER trg_tarea_evento AFTER UPDATE ON tarea FOR EACH ROW
BEGIN
  IF OLD.estado_codigo = 'draft' AND NEW.estado_codigo = 'assigned' THEN
    INSERT INTO evento (nombre, clave_unica, tarea_id, actor_id, payload)
    VALUES ('task.published', CONCAT('task.published:', NEW.id), NEW.id, NULLIF(@actor_id, 0),
            JSON_OBJECT('titulo', NEW.titulo, 'fecha_limite', NEW.fecha_limite));
  ELSEIF NEW.estado_codigo = 'cancelled' AND OLD.estado_codigo <> 'cancelled' THEN
    INSERT INTO evento (nombre, clave_unica, tarea_id, actor_id, payload)
    VALUES ('task.cancelled', CONCAT('task.cancelled:', NEW.id), NEW.id, NULLIF(@actor_id, 0),
            JSON_OBJECT('titulo', NEW.titulo));
  END IF;
END$$

CREATE TRIGGER trg_tarea_audit_ai AFTER INSERT ON tarea FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla, registro_id, accion, actor_id, ip_origen, detalle)
  VALUES ('tarea', NEW.id, 'insert', NULLIF(@actor_id, 0), @ip_origen,
          JSON_OBJECT('despues', JSON_OBJECT('titulo', NEW.titulo, 'estado', NEW.estado_codigo, 'fecha_limite', NEW.fecha_limite, 'revisor_id', NEW.revisor_id)));
END$$

CREATE TRIGGER trg_tarea_audit_au AFTER UPDATE ON tarea FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla, registro_id, accion, actor_id, ip_origen, detalle)
  VALUES ('tarea', NEW.id, IF(OLD.eliminado_en IS NULL AND NEW.eliminado_en IS NOT NULL, 'soft_delete', 'update'),
          COALESCE(NEW.eliminado_por, NULLIF(@actor_id, 0)), @ip_origen,
          JSON_OBJECT('antes',   JSON_OBJECT('titulo', OLD.titulo, 'estado', OLD.estado_codigo, 'fecha_limite', OLD.fecha_limite, 'revisor_id', OLD.revisor_id, 'eliminado_en', OLD.eliminado_en),
                      'despues', JSON_OBJECT('titulo', NEW.titulo, 'estado', NEW.estado_codigo, 'fecha_limite', NEW.fecha_limite, 'revisor_id', NEW.revisor_id, 'eliminado_en', NEW.eliminado_en)));
END$$

CREATE TRIGGER trg_pv_audit_ai AFTER INSERT ON programa_version FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla, registro_id, accion, actor_id, ip_origen, detalle)
  VALUES ('programa_version', NEW.id, 'insert', COALESCE(NULLIF(@actor_id, 0), NEW.creado_por), @ip_origen,
          JSON_OBJECT('despues', JSON_OBJECT('programa_curso_id', NEW.programa_curso_id, 'numero_version', NEW.numero_version, 'estado', NEW.estado_codigo, 'version_origen_id', NEW.version_origen_id)));
END$$

CREATE TRIGGER trg_pv_audit_au AFTER UPDATE ON programa_version FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla, registro_id, accion, actor_id, ip_origen, detalle)
  VALUES ('programa_version', NEW.id, 'update', NULLIF(@actor_id, 0), @ip_origen,
          JSON_OBJECT('antes',   JSON_OBJECT('nombre', OLD.nombre, 'estado', OLD.estado_codigo, 'pdf_hash', OLD.pdf_hash),
                      'despues', JSON_OBJECT('nombre', NEW.nombre, 'estado', NEW.estado_codigo, 'pdf_hash', NEW.pdf_hash)));
END$$

CREATE TRIGGER trg_usuario_audit_ai AFTER INSERT ON usuario FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla, registro_id, accion, actor_id, ip_origen, detalle)
  VALUES ('usuario', NEW.id, 'insert', NULLIF(@actor_id, 0), @ip_origen,
          JSON_OBJECT('despues', JSON_OBJECT('correo', NEW.correo, 'activo', NEW.activo)));
END$$

CREATE TRIGGER trg_usuario_audit_au AFTER UPDATE ON usuario FOR EACH ROW
BEGIN

  INSERT INTO auditoria (tabla, registro_id, accion, actor_id, ip_origen, detalle)
  VALUES ('usuario', NEW.id, IF(OLD.eliminado_en IS NULL AND NEW.eliminado_en IS NOT NULL, 'soft_delete', 'update'),
          COALESCE(NEW.eliminado_por, NULLIF(@actor_id, 0)), @ip_origen,
          JSON_OBJECT('antes',   JSON_OBJECT('correo', OLD.correo, 'activo', OLD.activo, 'eliminado_en', OLD.eliminado_en),
                      'despues', JSON_OBJECT('correo', NEW.correo, 'activo', NEW.activo, 'eliminado_en', NEW.eliminado_en),
                      'cambio_contrasena', OLD.hash_contrasena <> NEW.hash_contrasena));
END$$

CREATE PROCEDURE sp_publicar_tarea(IN p_tarea_id INT, IN p_actor_id INT)
BEGIN
  DECLARE v_estado VARCHAR(20);
  DECLARE v_alcance VARCHAR(12);
  DECLARE v_rol INT; DECLARE v_sede INT; DECLARE v_unidad INT; DECLARE v_workflow INT;
  DECLARE v_curso INT; DECLARE v_periodo INT;
  DECLARE v_wd_inicial INT;
  DECLARE v_total INT;
  DECLARE v_actor_previo INT;
  DECLARE v_propia TINYINT(1) DEFAULT 0;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    IF v_propia THEN ROLLBACK; ELSE ROLLBACK TO SAVEPOINT sp_publicar; END IF;
    RESIGNAL;
  END;

  -- Si quien llama ya abrio una transaccion, el savepoint sobrevive y se usa;
  -- si no, el ROLLBACK TO falla y el procedimiento abre su propia transaccion.
  BEGIN
    DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET v_propia = 1;
    SAVEPOINT sp_publicar;
    ROLLBACK TO SAVEPOINT sp_publicar;
  END;
  IF v_propia THEN START TRANSACTION; END IF;
  SELECT estado_codigo, alcance, rol_destino_id, sede_destino_id, unidad_destino_id, workflow_id, curso_id, periodo_id
    INTO v_estado, v_alcance, v_rol, v_sede, v_unidad, v_workflow, v_curso, v_periodo
  FROM tarea WHERE id = p_tarea_id AND eliminado_en IS NULL FOR UPDATE;

  IF v_estado IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: la tarea no existe (404)';
  END IF;
  IF v_estado <> 'draft' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: solo se publica una tarea en borrador (409)';
  END IF;

  SELECT id INTO v_wd_inicial FROM workflow_detalle
  WHERE workflow_id = v_workflow AND estado_origen IS NULL AND estado_destino = 'assigned';
  IF v_wd_inicial IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: el workflow no tiene transicion inicial a assigned';
  END IF;

  IF v_alcance IN ('rol', 'sede', 'unidad', 'todos') THEN
    INSERT INTO tarea_destinatario (tarea_id, usuario_id, estado_codigo)
    SELECT DISTINCT p_tarea_id, u.id, 'assigned'
    FROM usuario u
    JOIN usuario_rol ur ON ur.usuario_id = u.id
    JOIN rol r ON r.id = ur.rol_id
    LEFT JOIN unidad_academica ua ON ua.id = u.unidad_academica_id
    WHERE u.activo = 1 AND u.eliminado_en IS NULL
      AND ( (v_alcance = 'rol'    AND ur.rol_id = v_rol)
         OR (v_alcance = 'sede'   AND r.codigo = 'teacher' AND ua.sede_id = v_sede)
         OR (v_alcance = 'unidad' AND r.codigo = 'teacher' AND u.unidad_academica_id = v_unidad)
         OR (v_alcance = 'todos'  AND r.codigo = 'teacher') )
      AND NOT EXISTS (SELECT 1 FROM tarea_destinatario x WHERE x.tarea_id = p_tarea_id AND x.usuario_id = u.id);
  END IF;

  IF v_alcance = 'curso' THEN
    INSERT INTO tarea_destinatario (tarea_id, usuario_id, estado_codigo)
    SELECT DISTINCT p_tarea_id, u.id, 'assigned'
    FROM docente_curso dc JOIN usuario u ON u.id = dc.usuario_id
    WHERE dc.curso_id = v_curso AND dc.periodo_id = v_periodo AND dc.activo = 1
      AND u.activo = 1 AND u.eliminado_en IS NULL
      AND NOT EXISTS (SELECT 1 FROM tarea_destinatario x WHERE x.tarea_id = p_tarea_id AND x.usuario_id = u.id);
  END IF;

  IF v_alcance = 'seleccion' THEN
    INSERT INTO tarea_destinatario (tarea_id, usuario_id, estado_codigo)
    SELECT DISTINCT p_tarea_id, u.id, 'assigned'
    FROM usuario u
    LEFT JOIN unidad_academica ua ON ua.id = u.unidad_academica_id
    WHERE u.activo = 1 AND u.eliminado_en IS NULL
      AND EXISTS (
        SELECT 1 FROM tarea_seleccion ts
        WHERE ts.tarea_id = p_tarea_id
          AND ( (ts.tipo = 'usuario' AND ts.usuario_id = u.id)
             OR (ts.tipo IN ('todos', 'unidad', 'sede')
                 AND EXISTS (SELECT 1 FROM usuario_rol ur JOIN rol r ON r.id = ur.rol_id
                             WHERE ur.usuario_id = u.id AND r.codigo = 'teacher')
                 AND ( ts.tipo = 'todos'
                    OR (ts.tipo = 'unidad' AND u.unidad_academica_id = ts.unidad_academica_id)
                    OR (ts.tipo = 'sede'   AND ua.sede_id = ts.sede_id)))
             OR (ts.tipo = 'curso' AND EXISTS (SELECT 1 FROM docente_curso dc
                                               WHERE dc.usuario_id = u.id AND dc.curso_id = ts.curso_id
                                                 AND dc.periodo_id = v_periodo AND dc.activo = 1))))
      AND NOT EXISTS (SELECT 1 FROM tarea_destinatario x WHERE x.tarea_id = p_tarea_id AND x.usuario_id = u.id);
  END IF;

  SELECT COUNT(*) INTO v_total FROM tarea_destinatario WHERE tarea_id = p_tarea_id;
  IF v_total = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: la tarea no tiene destinatarios (422)';
  END IF;

  INSERT INTO tarea_transicion (tarea_destinatario_id, workflow_detalle_id, actor_id, estado_anterior, estado_nuevo, comentario)
  SELECT td.id, v_wd_inicial, p_actor_id, NULL, 'assigned', 'Publicacion de la tarea'
  FROM tarea_destinatario td
  WHERE td.tarea_id = p_tarea_id
    AND NOT EXISTS (SELECT 1 FROM tarea_transicion tt WHERE tt.tarea_destinatario_id = td.id);

  UPDATE tarea_destinatario SET estado_codigo = 'assigned', asignado_en = CURRENT_TIMESTAMP(3)
  WHERE tarea_id = p_tarea_id;
  -- El evento task.published toma el actor de @actor_id; si la API no lo fijo, se usa p_actor_id.
  SET v_actor_previo = @actor_id;
  SET @actor_id = COALESCE(NULLIF(@actor_id, 0), p_actor_id);
  UPDATE tarea SET estado_codigo = 'assigned', publicada_en = CURRENT_TIMESTAMP(3) WHERE id = p_tarea_id;
  SET @actor_id = v_actor_previo;
  IF v_propia THEN COMMIT; END IF;
END$$

DELIMITER ;

INSERT INTO schema_migracion (version, descripcion) VALUES
('1.2.1', 'Fechas en UTC; @actor_id = 0 se trata como NULL en auditoria y eventos; actor de task.published desde sp_publicar_tarea');
