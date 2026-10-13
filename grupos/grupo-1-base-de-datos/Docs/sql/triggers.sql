-- 02_triggers.sql | Grupo 1 - Base de datos | Workflow docente UDV | version 1.1.0
-- Triggers y procedimientos de db_udv. Ejecutar despues de crear las tablas (01_schema.sql).
-- Los errores usan SQLSTATE 45000 e indican el codigo HTTP sugerido (409 o 422).

USE db_udv;
SET NAMES utf8mb4;

DELIMITER $$

-- Historial inmutable (bitacoras)

CREATE TRIGGER trg_auditoria_no_update BEFORE UPDATE ON auditoria FOR EACH ROW
BEGIN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'auditoria es de solo insercion: no se permite UPDATE';
END$$

CREATE TRIGGER trg_auditoria_no_delete BEFORE DELETE ON auditoria FOR EACH ROW
BEGIN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'auditoria es de solo insercion: no se permite DELETE';
END$$

CREATE TRIGGER trg_tarea_transicion_no_update BEFORE UPDATE ON tarea_transicion FOR EACH ROW
BEGIN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El historial de transiciones no se modifica';
END$$

CREATE TRIGGER trg_tarea_transicion_no_delete BEFORE DELETE ON tarea_transicion FOR EACH ROW
BEGIN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El historial de transiciones no se elimina';
END$$

CREATE TRIGGER trg_programa_aprobacion_no_update BEFORE UPDATE ON programa_aprobacion FOR EACH ROW
BEGIN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El historial de aprobaciones no se modifica';
END$$

CREATE TRIGGER trg_programa_aprobacion_no_delete BEFORE DELETE ON programa_aprobacion FOR EACH ROW
BEGIN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El historial de aprobaciones no se elimina';
END$$

CREATE TRIGGER trg_entrega_no_update BEFORE UPDATE ON entrega FOR EACH ROW
BEGIN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: Una entrega no se modifica. Registre un nuevo intento.';
END$$

CREATE TRIGGER trg_entrega_valor_no_update BEFORE UPDATE ON entrega_valor FOR EACH ROW
BEGIN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: Los valores de una entrega no se modifican. Registre un nuevo intento.';
END$$

CREATE TRIGGER trg_entrega_valor_no_delete BEFORE DELETE ON entrega_valor FOR EACH ROW
BEGIN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: Los valores de una entrega no se eliminan.';
END$$

-- Eliminacion logica: no se permite DELETE fisico

CREATE TRIGGER trg_usuario_no_delete BEFORE DELETE ON usuario FOR EACH ROW
BEGIN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: usuario usa eliminacion logica (eliminado_en). No se permite ELIMINAR';
END$$

CREATE TRIGGER trg_curso_no_delete BEFORE DELETE ON curso FOR EACH ROW
BEGIN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: curso usa eliminacion logica (eliminado_en). No se permite ELIMINAR';
END$$

CREATE TRIGGER trg_tarea_no_delete BEFORE DELETE ON tarea FOR EACH ROW
BEGIN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: tarea usa eliminacion logica (eliminado_en). No se permite ELIMINAR';
END$$

CREATE TRIGGER trg_tarea_destinatario_no_delete BEFORE DELETE ON tarea_destinatario FOR EACH ROW
BEGIN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: una asignacion no se elimina; se cambia a estado cancelled.';
END$$

CREATE TRIGGER trg_entrega_no_delete BEFORE DELETE ON entrega FOR EACH ROW
BEGIN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: Una entrega no se elimina.';
END$$

CREATE TRIGGER trg_comentario_no_delete BEFORE DELETE ON comentario FOR EACH ROW
BEGIN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: comentario usa eliminacion logica (eliminado_en). No se permite ELIMINAR';
END$$

CREATE TRIGGER trg_archivo_no_delete BEFORE DELETE ON archivo FOR EACH ROW
BEGIN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: archivo usa eliminacion logica (eliminado_en). No se permite ELIMINAR';
END$$

CREATE TRIGGER trg_notificacion_no_delete BEFORE DELETE ON notificacion FOR EACH ROW
BEGIN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: Una notificacion no se elimina; se marca como leida.';
END$$

CREATE TRIGGER trg_programa_curso_no_delete BEFORE DELETE ON programa_curso FOR EACH ROW
BEGIN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: programa_curso no se elimina.';
END$$

CREATE TRIGGER trg_programa_version_no_delete BEFORE DELETE ON programa_version FOR EACH ROW
BEGIN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Una version de programa no se elimina';
END$$

CREATE TRIGGER trg_archivo_eliminacion_audit AFTER UPDATE ON archivo FOR EACH ROW
BEGIN
  IF OLD.eliminado_en IS NULL AND NEW.eliminado_en IS NOT NULL THEN
    INSERT INTO auditoria (tabla, registro_id, accion, actor_id, detalle)
    VALUES ('archivo', NEW.id, 'soft_delete', NEW.eliminado_por,
            JSON_OBJECT('nombre_original', NEW.nombre_original, 'tipo_mime', NEW.tipo_mime,
                        'ubicacion', NEW.ubicacion, 'hash_sha256', NEW.hash_sha256,
                        'autor_id', NEW.autor_id, 'tamano_bytes', NEW.tamano_bytes));
  END IF;
END$$

-- Workflow de tareas

CREATE TRIGGER trg_tt_valida BEFORE INSERT ON tarea_transicion FOR EACH ROW
BEGIN
  DECLARE v_estado_actual VARCHAR(20);
  DECLARE v_workflow_tarea INT;
  DECLARE v_ok INT DEFAULT 0;

  SELECT td.estado_codigo, t.workflow_id INTO v_estado_actual, v_workflow_tarea
  FROM tarea_destinatario td JOIN tarea t ON t.id = td.tarea_id
  WHERE td.id = NEW.tarea_destinatario_id;

  IF NEW.estado_anterior IS NULL THEN

    IF EXISTS (SELECT 1 FROM tarea_transicion WHERE tarea_destinatario_id = NEW.tarea_destinatario_id) THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: la asignacion ya tiene transicion inicial (409)';
    END IF;
  ELSEIF NOT (NEW.estado_anterior <=> v_estado_actual) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: estado_anterior no coincide con el estado actual de la asignacion (409)';
  END IF;

  SELECT COUNT(*) INTO v_ok FROM workflow_detalle wd
  WHERE wd.id = NEW.workflow_detalle_id
    AND wd.workflow_id = v_workflow_tarea
    AND wd.estado_origen <=> NEW.estado_anterior
    AND wd.estado_destino = NEW.estado_nuevo;
  IF v_ok = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: transicion no permitida por el workflow de la tarea (409)';
  END IF;

  SET NEW.secuencia = (SELECT COUNT(*) + 1 FROM tarea_transicion WHERE tarea_destinatario_id = NEW.tarea_destinatario_id);

  IF NEW.estado_nuevo = 'returned' AND (NEW.comentario IS NULL OR TRIM(NEW.comentario) = '') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: una devolucion exige una observacion (422)';
  END IF;
END$$

-- Programas de curso
CREATE FUNCTION fn_pv_bloqueada(p_pv_id INT) RETURNS TINYINT(1)
READS SQL DATA
BEGIN

  RETURN (SELECT COUNT(*) FROM programa_version
          WHERE id = p_pv_id AND estado_codigo IN ('authorized', 'superseded')) > 0;
END$$

CREATE TRIGGER trg_pv_inmutable BEFORE UPDATE ON programa_version FOR EACH ROW
BEGIN
  DECLARE v_total DECIMAL(7,2);
  DECLARE v_mismo_contenido TINYINT(1);

  SET v_mismo_contenido = (NEW.programa_curso_id = OLD.programa_curso_id
              AND NEW.nombre = OLD.nombre
              AND NEW.periodo_id = OLD.periodo_id
              AND NEW.numero_version = OLD.numero_version
              AND NEW.descripcion <=> OLD.descripcion
              AND NEW.resumen_cambios <=> OLD.resumen_cambios
              AND NEW.unidad_academica_id <=> OLD.unidad_academica_id
              AND NEW.programa_academico <=> OLD.programa_academico
              AND NEW.departamento <=> OLD.departamento
              AND NEW.nivel <=> OLD.nivel
              AND NEW.area_id <=> OLD.area_id
              AND NEW.pensum <=> OLD.pensum
              AND NEW.horas_clase_semanal <=> OLD.horas_clase_semanal
              AND NEW.docente_responsable_id <=> OLD.docente_responsable_id
              AND NEW.revisor_id <=> OLD.revisor_id
              AND NEW.observaciones_autorizacion <=> OLD.observaciones_autorizacion
              AND NEW.autorizado_por <=> OLD.autorizado_por
              AND NEW.autorizado_en <=> OLD.autorizado_en);

  IF OLD.estado_codigo = 'superseded' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version reemplazada: es historica y no se modifica (409)';
  END IF;

  IF NEW.estado_codigo <> OLD.estado_codigo
     AND NOT EXISTS (SELECT 1 FROM flujo_programa
                     WHERE estado_origen = OLD.estado_codigo AND estado_destino = NEW.estado_codigo) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: cambio de estado del programa no permitido por flujo_programa (409)';
  END IF;

  IF OLD.estado_codigo = 'authorized' THEN
    IF NOT v_mismo_contenido
       OR NOT (

            (NEW.estado_codigo = 'superseded'
             AND NEW.pdf_archivo_id <=> OLD.pdf_archivo_id AND NEW.pdf_hash <=> OLD.pdf_hash)

         OR (NEW.estado_codigo = 'authorized' AND OLD.pdf_hash IS NULL)
          ) THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Version autorizada: no se modifica, cree una nueva version (409)';
    END IF;
  END IF;

  IF NEW.estado_codigo = 'submitted' AND OLD.estado_codigo <> 'submitted' THEN
    SELECT IFNULL(SUM(ponderacion), 0) INTO v_total
    FROM programa_evaluacion WHERE programa_version_id = NEW.id;
    IF v_total <> 100 THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: las evaluaciones deben sumar 100 para enviar el programa (422)';
    END IF;
  END IF;

  IF NEW.estado_codigo = 'authorized' AND OLD.estado_codigo <> 'authorized'
     AND (NEW.autorizado_por IS NULL OR NEW.autorizado_en IS NULL) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: autorizar requiere autorizado_por y autorizado_en';
  END IF;
END$$

CREATE TRIGGER trg_aprobacion_valida BEFORE INSERT ON programa_aprobacion FOR EACH ROW
BEGIN
  IF NEW.estado_nuevo = 'returned' AND (NEW.comentario IS NULL OR TRIM(NEW.comentario) = '') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: una devolucion exige una observacion (422)';
  END IF;
END$$

CREATE TRIGGER trg_competencia_bi BEFORE INSERT ON programa_competencia FOR EACH ROW
BEGIN IF fn_pv_bloqueada(NEW.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$
CREATE TRIGGER trg_competencia_bu BEFORE UPDATE ON programa_competencia FOR EACH ROW
BEGIN IF fn_pv_bloqueada(OLD.programa_version_id) OR fn_pv_bloqueada(NEW.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$
CREATE TRIGGER trg_competencia_bd BEFORE DELETE ON programa_competencia FOR EACH ROW
BEGIN IF fn_pv_bloqueada(OLD.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$

CREATE TRIGGER trg_prereq_bi BEFORE INSERT ON programa_prerrequisito FOR EACH ROW
BEGIN IF fn_pv_bloqueada(NEW.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$
CREATE TRIGGER trg_prereq_bu BEFORE UPDATE ON programa_prerrequisito FOR EACH ROW
BEGIN IF fn_pv_bloqueada(OLD.programa_version_id) OR fn_pv_bloqueada(NEW.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$
CREATE TRIGGER trg_prereq_bd BEFORE DELETE ON programa_prerrequisito FOR EACH ROW
BEGIN IF fn_pv_bloqueada(OLD.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$

CREATE TRIGGER trg_unidad_bi BEFORE INSERT ON programa_unidad FOR EACH ROW
BEGIN IF fn_pv_bloqueada(NEW.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$
CREATE TRIGGER trg_unidad_bu BEFORE UPDATE ON programa_unidad FOR EACH ROW
BEGIN IF fn_pv_bloqueada(OLD.programa_version_id) OR fn_pv_bloqueada(NEW.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$
CREATE TRIGGER trg_unidad_bd BEFORE DELETE ON programa_unidad FOR EACH ROW
BEGIN IF fn_pv_bloqueada(OLD.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$

CREATE TRIGGER trg_unidad_item_bi BEFORE INSERT ON programa_unidad_item FOR EACH ROW
BEGIN
  IF fn_pv_bloqueada((SELECT programa_version_id FROM programa_unidad WHERE id = NEW.programa_unidad_id)) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version';
  END IF;

  IF NEW.competencia_id IS NOT NULL AND NOT EXISTS (
       SELECT 1 FROM programa_competencia c JOIN programa_unidad u ON u.programa_version_id = c.programa_version_id
       WHERE c.id = NEW.competencia_id AND u.id = NEW.programa_unidad_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: la competencia del item es de otra version del programa (422)';
  END IF;
END$$
CREATE TRIGGER trg_unidad_item_bu BEFORE UPDATE ON programa_unidad_item FOR EACH ROW
BEGIN
  IF fn_pv_bloqueada((SELECT programa_version_id FROM programa_unidad WHERE id = OLD.programa_unidad_id))
     OR fn_pv_bloqueada((SELECT programa_version_id FROM programa_unidad WHERE id = NEW.programa_unidad_id)) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version';
  END IF;
  IF NEW.competencia_id IS NOT NULL AND NOT EXISTS (
       SELECT 1 FROM programa_competencia c JOIN programa_unidad u ON u.programa_version_id = c.programa_version_id
       WHERE c.id = NEW.competencia_id AND u.id = NEW.programa_unidad_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: la competencia del item es de otra version del programa (422)';
  END IF;
END$$
CREATE TRIGGER trg_unidad_item_bd BEFORE DELETE ON programa_unidad_item FOR EACH ROW
BEGIN IF fn_pv_bloqueada((SELECT programa_version_id FROM programa_unidad WHERE id = OLD.programa_unidad_id)) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$

CREATE TRIGGER trg_bibliografia_bi BEFORE INSERT ON programa_bibliografia FOR EACH ROW
BEGIN IF fn_pv_bloqueada(NEW.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$
CREATE TRIGGER trg_bibliografia_bu BEFORE UPDATE ON programa_bibliografia FOR EACH ROW
BEGIN IF fn_pv_bloqueada(OLD.programa_version_id) OR fn_pv_bloqueada(NEW.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$
CREATE TRIGGER trg_bibliografia_bd BEFORE DELETE ON programa_bibliografia FOR EACH ROW
BEGIN IF fn_pv_bloqueada(OLD.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$

CREATE TRIGGER trg_perfil_egreso_bi BEFORE INSERT ON programa_perfil_egreso FOR EACH ROW
BEGIN IF fn_pv_bloqueada(NEW.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$
CREATE TRIGGER trg_perfil_egreso_bu BEFORE UPDATE ON programa_perfil_egreso FOR EACH ROW
BEGIN IF fn_pv_bloqueada(OLD.programa_version_id) OR fn_pv_bloqueada(NEW.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$
CREATE TRIGGER trg_perfil_egreso_bd BEFORE DELETE ON programa_perfil_egreso FOR EACH ROW
BEGIN IF fn_pv_bloqueada(OLD.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$

CREATE TRIGGER trg_programa_pdf_bi BEFORE INSERT ON programa_pdf FOR EACH ROW
BEGIN
  IF NOT EXISTS (SELECT 1 FROM programa_version WHERE id = NEW.programa_version_id AND estado_codigo = 'authorized') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: solo se genera el PDF de una version autorizada (409)';
  END IF;
END$$
CREATE TRIGGER trg_programa_pdf_no_update BEFORE UPDATE ON programa_pdf FOR EACH ROW
BEGIN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El historial de PDF no se modifica'; END$$
CREATE TRIGGER trg_programa_pdf_no_delete BEFORE DELETE ON programa_pdf FOR EACH ROW
BEGIN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El historial de PDF no se elimina'; END$$

CREATE TRIGGER trg_evaluacion_bi BEFORE INSERT ON programa_evaluacion FOR EACH ROW
BEGIN
  IF fn_pv_bloqueada(NEW.programa_version_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version';
  END IF;
  IF (SELECT IFNULL(SUM(ponderacion), 0) FROM programa_evaluacion
      WHERE programa_version_id = NEW.programa_version_id) + NEW.ponderacion > 100 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: el total de evaluaciones no puede pasar de 100 (422)';
  END IF;
END$$
CREATE TRIGGER trg_evaluacion_bu BEFORE UPDATE ON programa_evaluacion FOR EACH ROW
BEGIN
  IF fn_pv_bloqueada(OLD.programa_version_id) OR fn_pv_bloqueada(NEW.programa_version_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version';
  END IF;
  IF (SELECT IFNULL(SUM(ponderacion), 0) FROM programa_evaluacion
      WHERE programa_version_id = NEW.programa_version_id AND id <> OLD.id) + NEW.ponderacion > 100 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: el total de evaluaciones no puede pasar de 100 (422)';
  END IF;
END$$
CREATE TRIGGER trg_evaluacion_bd BEFORE DELETE ON programa_evaluacion FOR EACH ROW
BEGIN IF fn_pv_bloqueada(OLD.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$

-- Procedimiento de autorizacion

CREATE PROCEDURE sp_autorizar_version(IN p_pv_id INT, IN p_actor_id INT, IN p_comentario VARCHAR(1000))
BEGIN
  DECLARE v_estado VARCHAR(20);
  DECLARE v_programa INT;
  DECLARE v_periodo INT;
  DECLARE v_anterior INT DEFAULT NULL;

  DECLARE v_propia TINYINT(1) DEFAULT (@@in_transaction = 0);
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    IF v_propia THEN ROLLBACK; ELSE ROLLBACK TO SAVEPOINT sp_autorizar; END IF;
    RESIGNAL;
  END;

  IF v_propia THEN START TRANSACTION; ELSE SAVEPOINT sp_autorizar; END IF;
  SELECT estado_codigo, programa_curso_id, periodo_id INTO v_estado, v_programa, v_periodo
  FROM programa_version WHERE id = p_pv_id FOR UPDATE;

  IF v_estado IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: la version no existe (404)';
  END IF;
  IF v_estado <> 'approved' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: solo se autoriza una version en estado approved (409)';
  END IF;

  SELECT id INTO v_anterior FROM programa_version
  WHERE programa_curso_id = v_programa AND periodo_id = v_periodo
    AND estado_codigo = 'authorized' AND id <> p_pv_id
  FOR UPDATE;

  IF v_anterior IS NOT NULL THEN
    UPDATE programa_version SET estado_codigo = 'superseded' WHERE id = v_anterior;
    INSERT INTO programa_aprobacion (programa_version_id, actor_id, estado_anterior, estado_nuevo, comentario)
    VALUES (v_anterior, p_actor_id, 'authorized', 'superseded', CONCAT('Reemplazada por la version id ', p_pv_id));
  END IF;

  UPDATE programa_version
     SET estado_codigo = 'authorized', autorizado_por = p_actor_id, autorizado_en = CURRENT_TIMESTAMP(3),
         observaciones_autorizacion = p_comentario
   WHERE id = p_pv_id;
  INSERT INTO programa_aprobacion (programa_version_id, actor_id, estado_anterior, estado_nuevo, comentario)
  VALUES (p_pv_id, p_actor_id, 'approved', 'authorized', p_comentario);
  IF v_propia THEN COMMIT; END IF;
END$$

-- Publicacion masiva

CREATE PROCEDURE sp_publicar_tarea(IN p_tarea_id INT, IN p_actor_id INT)
BEGIN
  DECLARE v_estado VARCHAR(20);
  DECLARE v_alcance VARCHAR(12);
  DECLARE v_rol INT; DECLARE v_sede INT; DECLARE v_unidad INT; DECLARE v_workflow INT;
  DECLARE v_curso INT; DECLARE v_periodo INT;
  DECLARE v_wd_inicial INT;
  DECLARE v_total INT;
  DECLARE v_propia TINYINT(1) DEFAULT (@@in_transaction = 0);
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    IF v_propia THEN ROLLBACK; ELSE ROLLBACK TO SAVEPOINT sp_publicar; END IF;
    RESIGNAL;
  END;

  IF v_propia THEN START TRANSACTION; ELSE SAVEPOINT sp_publicar; END IF;
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
  UPDATE tarea SET estado_codigo = 'assigned', publicada_en = CURRENT_TIMESTAMP(3) WHERE id = p_tarea_id;
  IF v_propia THEN COMMIT; END IF;
END$$

-- Borrador de entrega

CREATE TRIGGER trg_entrega_borrador_bi BEFORE INSERT ON entrega_borrador FOR EACH ROW
BEGIN
  IF NOT EXISTS (SELECT 1 FROM tarea_destinatario WHERE id = NEW.tarea_destinatario_id
                 AND estado_codigo IN ('assigned', 'in_progress', 'returned')) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: solo se guarda borrador de una asignacion pendiente (409)';
  END IF;
END$$
CREATE TRIGGER trg_entrega_borrador_bu BEFORE UPDATE ON entrega_borrador FOR EACH ROW
BEGIN
  IF NOT EXISTS (SELECT 1 FROM tarea_destinatario WHERE id = NEW.tarea_destinatario_id
                 AND estado_codigo IN ('assigned', 'in_progress', 'returned')) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: solo se guarda borrador de una asignacion pendiente (409)';
  END IF;
END$$

-- Eventos para notificaciones (Grupo 6)

CREATE TRIGGER trg_evento_no_delete BEFORE DELETE ON evento FOR EACH ROW
BEGIN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un evento no se elimina'; END$$
CREATE TRIGGER trg_evento_bu BEFORE UPDATE ON evento FOR EACH ROW
BEGIN
  IF OLD.procesado_en IS NOT NULL
     OR NOT (NEW.nombre <=> OLD.nombre AND NEW.clave_unica <=> OLD.clave_unica AND NEW.payload <=> OLD.payload
             AND NEW.tarea_id <=> OLD.tarea_id AND NEW.tarea_destinatario_id <=> OLD.tarea_destinatario_id
             AND NEW.programa_version_id <=> OLD.programa_version_id AND NEW.actor_id <=> OLD.actor_id
             AND NEW.creado_en <=> OLD.creado_en) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un evento solo admite marcar procesado_en una vez (409)';
  END IF;
END$$

CREATE TRIGGER trg_tt_evento AFTER INSERT ON tarea_transicion FOR EACH ROW
BEGIN
  DECLARE v_nombre VARCHAR(40) DEFAULT NULL;
  SET v_nombre = CASE NEW.estado_nuevo
                   WHEN 'submitted' THEN 'assignment.submitted'
                   WHEN 'returned'  THEN 'assignment.returned'
                   WHEN 'approved'  THEN 'assignment.approved'
                 END;
  IF v_nombre IS NOT NULL THEN
    INSERT INTO evento (nombre, clave_unica, tarea_id, tarea_destinatario_id, actor_id, payload)
    SELECT v_nombre, CONCAT(v_nombre, ':', NEW.tarea_destinatario_id, ':', NEW.secuencia),
           td.tarea_id, td.id, NEW.actor_id,
           JSON_OBJECT('usuario_id', td.usuario_id, 'estado_anterior', NEW.estado_anterior,
                       'estado_nuevo', NEW.estado_nuevo, 'comentario', NEW.comentario)
    FROM tarea_destinatario td WHERE td.id = NEW.tarea_destinatario_id;
  END IF;
END$$

CREATE TRIGGER trg_tarea_evento AFTER UPDATE ON tarea FOR EACH ROW
BEGIN
  IF OLD.estado_codigo = 'draft' AND NEW.estado_codigo = 'assigned' THEN
    INSERT INTO evento (nombre, clave_unica, tarea_id, actor_id, payload)
    VALUES ('task.published', CONCAT('task.published:', NEW.id), NEW.id, @actor_id,
            JSON_OBJECT('titulo', NEW.titulo, 'fecha_limite', NEW.fecha_limite));
  ELSEIF NEW.estado_codigo = 'cancelled' AND OLD.estado_codigo <> 'cancelled' THEN
    INSERT INTO evento (nombre, clave_unica, tarea_id, actor_id, payload)
    VALUES ('task.cancelled', CONCAT('task.cancelled:', NEW.id), NEW.id, @actor_id,
            JSON_OBJECT('titulo', NEW.titulo));
  END IF;
END$$

CREATE TRIGGER trg_pv_evento AFTER UPDATE ON programa_version FOR EACH ROW
BEGIN
  IF NEW.estado_codigo = 'authorized' AND OLD.estado_codigo <> 'authorized' THEN
    INSERT INTO evento (nombre, clave_unica, programa_version_id, actor_id, payload)
    VALUES ('program.authorized', CONCAT('program.authorized:', NEW.id), NEW.id, NEW.autorizado_por,
            JSON_OBJECT('programa_curso_id', NEW.programa_curso_id, 'numero_version', NEW.numero_version,
                        'periodo_id', NEW.periodo_id));
  END IF;
END$$

CREATE PROCEDURE sp_generar_eventos_vencimiento(OUT p_creados INT)
BEGIN
  DECLARE v_dias INT;
  SELECT CAST(valor AS UNSIGNED) INTO v_dias FROM parametro WHERE codigo = 'dias_aviso_vencimiento';
  INSERT IGNORE INTO evento (nombre, clave_unica, tarea_id, tarea_destinatario_id, payload)
  SELECT 'assignment.due_soon',
         CONCAT('assignment.due_soon:', td.id, ':', DATE_FORMAT(COALESCE(td.fecha_limite, t.fecha_limite), '%Y%m%d%H%i')),
         t.id, td.id,
         JSON_OBJECT('usuario_id', td.usuario_id, 'fecha_limite', COALESCE(td.fecha_limite, t.fecha_limite))
  FROM tarea_destinatario td
  JOIN tarea t ON t.id = td.tarea_id
  WHERE t.estado_codigo <> 'draft' AND t.eliminado_en IS NULL
    AND td.estado_codigo IN ('assigned', 'in_progress', 'returned')
    AND COALESCE(td.fecha_limite, t.fecha_limite) >= NOW(3)
    AND COALESCE(td.fecha_limite, t.fecha_limite) < NOW(3) + INTERVAL IFNULL(v_dias, 3) DAY;
  SET p_creados = ROW_COUNT();
END$$

-- Auditoria de altas y cambios

CREATE TRIGGER trg_tarea_audit_ai AFTER INSERT ON tarea FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla, registro_id, accion, actor_id, ip_origen, detalle)
  VALUES ('tarea', NEW.id, 'insert', @actor_id, @ip_origen,
          JSON_OBJECT('despues', JSON_OBJECT('titulo', NEW.titulo, 'estado', NEW.estado_codigo, 'fecha_limite', NEW.fecha_limite, 'revisor_id', NEW.revisor_id)));
END$$
CREATE TRIGGER trg_tarea_audit_au AFTER UPDATE ON tarea FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla, registro_id, accion, actor_id, ip_origen, detalle)
  VALUES ('tarea', NEW.id, IF(OLD.eliminado_en IS NULL AND NEW.eliminado_en IS NOT NULL, 'soft_delete', 'update'),
          COALESCE(NEW.eliminado_por, @actor_id), @ip_origen,
          JSON_OBJECT('antes',   JSON_OBJECT('titulo', OLD.titulo, 'estado', OLD.estado_codigo, 'fecha_limite', OLD.fecha_limite, 'revisor_id', OLD.revisor_id, 'eliminado_en', OLD.eliminado_en),
                      'despues', JSON_OBJECT('titulo', NEW.titulo, 'estado', NEW.estado_codigo, 'fecha_limite', NEW.fecha_limite, 'revisor_id', NEW.revisor_id, 'eliminado_en', NEW.eliminado_en)));
END$$

CREATE TRIGGER trg_pv_audit_ai AFTER INSERT ON programa_version FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla, registro_id, accion, actor_id, ip_origen, detalle)
  VALUES ('programa_version', NEW.id, 'insert', COALESCE(@actor_id, NEW.creado_por), @ip_origen,
          JSON_OBJECT('despues', JSON_OBJECT('programa_curso_id', NEW.programa_curso_id, 'numero_version', NEW.numero_version, 'estado', NEW.estado_codigo, 'version_origen_id', NEW.version_origen_id)));
END$$
CREATE TRIGGER trg_pv_audit_au AFTER UPDATE ON programa_version FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla, registro_id, accion, actor_id, ip_origen, detalle)
  VALUES ('programa_version', NEW.id, 'update', @actor_id, @ip_origen,
          JSON_OBJECT('antes',   JSON_OBJECT('nombre', OLD.nombre, 'estado', OLD.estado_codigo, 'pdf_hash', OLD.pdf_hash),
                      'despues', JSON_OBJECT('nombre', NEW.nombre, 'estado', NEW.estado_codigo, 'pdf_hash', NEW.pdf_hash)));
END$$

CREATE TRIGGER trg_usuario_audit_ai AFTER INSERT ON usuario FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla, registro_id, accion, actor_id, ip_origen, detalle)
  VALUES ('usuario', NEW.id, 'insert', @actor_id, @ip_origen,
          JSON_OBJECT('despues', JSON_OBJECT('correo', NEW.correo, 'activo', NEW.activo)));
END$$
CREATE TRIGGER trg_usuario_audit_au AFTER UPDATE ON usuario FOR EACH ROW
BEGIN

  INSERT INTO auditoria (tabla, registro_id, accion, actor_id, ip_origen, detalle)
  VALUES ('usuario', NEW.id, IF(OLD.eliminado_en IS NULL AND NEW.eliminado_en IS NOT NULL, 'soft_delete', 'update'),
          COALESCE(NEW.eliminado_por, @actor_id), @ip_origen,
          JSON_OBJECT('antes',   JSON_OBJECT('correo', OLD.correo, 'activo', OLD.activo, 'eliminado_en', OLD.eliminado_en),
                      'despues', JSON_OBJECT('correo', NEW.correo, 'activo', NEW.activo, 'eliminado_en', NEW.eliminado_en),
                      'cambio_contrasena', OLD.hash_contrasena <> NEW.hash_contrasena));
END$$

DELIMITER ;
