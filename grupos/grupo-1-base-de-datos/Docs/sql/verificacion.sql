/* =====================================================================
   verificacion.sql | Pruebas de las restricciones
   Ejecutar despues de 01_schema.sql y 02_seed.sql. Todo corre dentro de una transaccion
   que se deshace al final: los datos semilla quedan intactos.
   Resultado esperado: la primera fila dice 'pasan 75, fallan 0'.
   ===================================================================== */
USE db_udv;
SET NAMES utf8mb4;

DROP TABLE IF EXISTS tmp_resultado_prueba;
CREATE TABLE tmp_resultado_prueba (
    n          INT AUTO_INCREMENT PRIMARY KEY,
    prueba     VARCHAR(120),
    esperado   VARCHAR(5),
    obtenido   VARCHAR(5),
    resultado  VARCHAR(5),
    mensaje    VARCHAR(500)
) ENGINE=MyISAM;   -- MyISAM: no se deshace con el ROLLBACK, asi conservamos los resultados

DROP PROCEDURE IF EXISTS sp_prueba;
DELIMITER $$
CREATE PROCEDURE sp_prueba(IN p_nombre VARCHAR(120), IN p_esperado VARCHAR(5), IN p_sql TEXT)
BEGIN
  DECLARE v_msg VARCHAR(500) DEFAULT NULL;
  BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
      GET DIAGNOSTICS CONDITION 1 v_msg = MESSAGE_TEXT;
      INSERT INTO tmp_resultado_prueba (prueba, esperado, obtenido, resultado, mensaje)
      VALUES (p_nombre, p_esperado, 'error', IF(p_esperado = 'error', 'PASA', 'FALLA'), v_msg);
    END;
    SET @sql_prueba = p_sql;
    PREPARE st FROM @sql_prueba;
    EXECUTE st;
    DEALLOCATE PREPARE st;
    INSERT INTO tmp_resultado_prueba (prueba, esperado, obtenido, resultado, mensaje)
    VALUES (p_nombre, p_esperado, 'ok', IF(p_esperado = 'ok', 'PASA', 'FALLA'), NULL);
  END;
END$$
DELIMITER ;

START TRANSACTION;

-- Usuarios y asignaciones
CALL sp_prueba('Correo duplicado (otra capitalizacion)', 'error',
  "INSERT INTO usuario (correo, nombres, apellidos, hash_contrasena) VALUES ('DOCENTE1@demo.udv.edu.gt','X','Y','h')");
CALL sp_prueba('Asignacion duplicada tarea+docente', 'error',
  "INSERT INTO tarea_destinatario (tarea_id, usuario_id) VALUES (1, 3)");
CALL sp_prueba('FK huerfana: asignacion a tarea inexistente', 'error',
  "INSERT INTO tarea_destinatario (tarea_id, usuario_id) VALUES (999, 3)");
CALL sp_prueba('Tarea publicada sin fecha de publicacion', 'error',
  "INSERT INTO tarea (workflow_id, estado_codigo, titulo, creado_por) VALUES (1, 'assigned', 'X', 2)");

-- Workflow de tareas
CALL sp_prueba('Transicion no definida (assigned -> approved)', 'error',
  "INSERT INTO tarea_transicion (tarea_destinatario_id, workflow_detalle_id, actor_id, estado_anterior, estado_nuevo)
   SELECT 2, id, 4, 'assigned', 'approved' FROM workflow_detalle WHERE workflow_id = 1 LIMIT 1");
CALL sp_prueba('Transicion desde un estado que no es el actual', 'error',
  "INSERT INTO tarea_transicion (tarea_destinatario_id, workflow_detalle_id, actor_id, estado_anterior, estado_nuevo)
   SELECT 2, id, 4, 'in_progress', 'submitted' FROM workflow_detalle WHERE workflow_id = 1 AND estado_origen = 'in_progress' AND estado_destino = 'submitted'");
CALL sp_prueba('Segunda transicion inicial para la misma asignacion', 'error',
  "INSERT INTO tarea_transicion (tarea_destinatario_id, workflow_detalle_id, actor_id, estado_anterior, estado_nuevo)
   SELECT 2, id, 2, NULL, 'assigned' FROM workflow_detalle WHERE workflow_id = 1 AND estado_origen IS NULL");
CALL sp_prueba('Transicion valida assigned -> in_progress', 'ok',
  "INSERT INTO tarea_transicion (tarea_destinatario_id, workflow_detalle_id, actor_id, estado_anterior, estado_nuevo)
   SELECT 2, id, 4, 'assigned', 'in_progress' FROM workflow_detalle WHERE workflow_id = 1 AND estado_origen = 'assigned' AND estado_destino = 'in_progress'");
CALL sp_prueba('Revisor toma la entrega (submitted -> under_review)', 'ok',
  "INSERT INTO tarea_transicion (tarea_destinatario_id, workflow_detalle_id, actor_id, estado_anterior, estado_nuevo)
   SELECT 1, id, 5, 'submitted', 'under_review' FROM workflow_detalle WHERE workflow_id = 1 AND estado_origen = 'submitted' AND estado_destino = 'under_review'");
UPDATE tarea_destinatario SET estado_codigo = 'under_review' WHERE id = 1;
CALL sp_prueba('Devolucion sin observacion', 'error',
  "INSERT INTO tarea_transicion (tarea_destinatario_id, workflow_detalle_id, actor_id, estado_anterior, estado_nuevo)
   SELECT 1, id, 5, 'under_review', 'returned' FROM workflow_detalle WHERE workflow_id = 1 AND estado_origen = 'under_review' AND estado_destino = 'returned'");
CALL sp_prueba('Devolucion con observacion', 'ok',
  "INSERT INTO tarea_transicion (tarea_destinatario_id, workflow_detalle_id, actor_id, estado_anterior, estado_nuevo, comentario)
   SELECT 1, id, 5, 'under_review', 'returned', 'Falta la firma' FROM workflow_detalle WHERE workflow_id = 1 AND estado_origen = 'under_review' AND estado_destino = 'returned'");
CALL sp_prueba('Transicion inicial duplicada en workflow_detalle', 'error',
  "INSERT INTO workflow_detalle (workflow_id, estado_origen, estado_destino, accion) VALUES (1, NULL, 'assigned', 'publish')");
CALL sp_prueba('Transicion con accion desconocida', 'error',
  "INSERT INTO workflow_detalle (workflow_id, estado_origen, estado_destino, accion) VALUES (1, 'submitted', 'closed', 'borrar')");

-- Historial y eliminacion logica
CALL sp_prueba('UPDATE al historial de transiciones', 'error', "UPDATE tarea_transicion SET comentario = 'x' WHERE id = 1");
CALL sp_prueba('DELETE al historial de transiciones', 'error', "DELETE FROM tarea_transicion WHERE id = 1");
CALL sp_prueba('DELETE fisico de usuario', 'error', "DELETE FROM usuario WHERE id = 8");
CALL sp_prueba('DELETE fisico de tarea', 'error', "DELETE FROM tarea WHERE id = 3");
CALL sp_prueba('Modificar una entrega ya enviada', 'error', "UPDATE entrega SET contenido_texto = 'x' WHERE id = 1");
CALL sp_prueba('Eliminacion logica de archivo', 'ok', "UPDATE archivo SET eliminado_en = NOW(3), eliminado_por = 3 WHERE id = 2");
SET @audit_archivo = (SELECT COUNT(*) FROM auditoria WHERE tabla = 'archivo' AND registro_id = '2' AND accion = 'soft_delete');
CALL sp_prueba('UPDATE a la auditoria', 'error', "UPDATE auditoria SET accion = 'x'");
CALL sp_prueba('Archivo de 0 bytes', 'error',
  "INSERT INTO archivo (nombre_original, nombre_interno, tipo_mime, tamano_bytes, hash_sha256, ubicacion, autor_id) VALUES ('a','b','c',0,'d','e',3)");
CALL sp_prueba('Archivo asociado a dos destinos a la vez', 'error',
  "INSERT INTO archivo (nombre_original, nombre_interno, tipo_mime, tamano_bytes, hash_sha256, ubicacion, autor_id, entrega_id, comentario_id)
   VALUES ('a.pdf', 'dos-destinos.pdf', 'application/pdf', 10, REPEAT('a', 64), 'x/a.pdf', 3, 1, 1)");
CALL sp_prueba('Codigo de rol en mayusculas', 'error', "INSERT INTO rol (codigo, nombre) VALUES ('DOCENTE', 'Docente')");
CALL sp_prueba('Codigo de permiso sin formato recurso.accion', 'error', "INSERT INTO permiso (codigo) VALUES ('Tareas Crear')");
CALL sp_prueba('Intento de login fallido en auditoria (usuario inexistente)', 'ok',
  "INSERT INTO auditoria (tabla, registro_id, accion, actor_id, ip_origen, detalle)
   VALUES ('usuario', '0', 'login_failed', NULL, '10.0.0.5', JSON_OBJECT('correo', 'noexiste@udv.edu.gt', 'motivo', 'usuario_inexistente'))");
CALL sp_prueba('Comentario sin asignacion ni version', 'error',
  "INSERT INTO comentario (autor_id, contenido) VALUES (3, 'hola')");

-- Programas y versiones
CALL sp_prueba('Segunda version vigente del mismo programa y periodo', 'error',
  "INSERT INTO programa_version (programa_curso_id, numero_version, nombre, periodo_id, estado_codigo, creado_por) VALUES (1, 3, 'X', 1, 'authorized', 3)");
CALL sp_prueba('Modificar una version autorizada', 'error', "UPDATE programa_version SET nombre = 'otro' WHERE id = 1");
CALL sp_prueba('Registrar el PDF otra vez', 'error', "UPDATE programa_version SET pdf_hash = REPEAT('0', 64) WHERE id = 1");
CALL sp_prueba('Agregar evaluacion a version autorizada', 'error',
  "INSERT INTO programa_evaluacion (programa_version_id, orden, nombre, ponderacion) VALUES (1, 9, 'Extra', 1)");
CALL sp_prueba('Borrar bibliografia de version autorizada', 'error', "DELETE FROM programa_bibliografia WHERE programa_version_id = 1");
CALL sp_prueba('Editar item de unidad de version autorizada', 'error',
  "UPDATE programa_unidad_item SET item = 'x' WHERE programa_unidad_id = 1");
CALL sp_prueba('Editar version en borrador (coexiste con la autorizada)', 'ok', "UPDATE programa_bibliografia SET referencia = 'Nueva referencia 2025' WHERE programa_version_id = 2 AND orden = 3");
CALL sp_prueba('Evaluaciones que pasan de 100', 'error',
  "INSERT INTO programa_evaluacion (programa_version_id, orden, nombre, ponderacion) VALUES (2, 5, 'Extra', 5)");
CALL sp_prueba('Unidad con orden repetido', 'error',
  "INSERT INTO programa_unidad (programa_version_id, orden, titulo) VALUES (2, 1, 'Repetida')");
CALL sp_prueba('Crear version 3 con evaluaciones al 50%', 'ok',
  "INSERT INTO programa_version (id, programa_curso_id, numero_version, nombre, periodo_id, creado_por) VALUES (99, 1, 3, 'v3', 2, 3)");
CALL sp_prueba('...agregar una evaluacion de 50', 'ok',
  "INSERT INTO programa_evaluacion (programa_version_id, orden, nombre, ponderacion) VALUES (99, 1, 'Unica', 50)");
CALL sp_prueba('Enviar a revision con total distinto de 100', 'error', "UPDATE programa_version SET estado_codigo = 'submitted' WHERE id = 99");
INSERT INTO programa_version (id, programa_curso_id, numero_version, nombre, periodo_id, estado_codigo, creado_por) VALUES (98, 1, 4, 'v4', 3, 'approved', 3);
CALL sp_prueba('Autorizar sin indicar quien', 'error', "UPDATE programa_version SET estado_codigo = 'authorized' WHERE id = 98");

-- Aportes del esquema de Pablo (version 1.1.0)
CALL sp_prueba('Programa duplicado curso+sede+modalidad', 'error',
  "INSERT INTO programa_curso (curso_id, sede_id, modalidad_id, creado_por) VALUES (1, 1, 1, 2)");
CALL sp_prueba('Mismo curso y sede en otra modalidad', 'ok',
  "INSERT INTO programa_curso (curso_id, sede_id, modalidad_id, creado_por) VALUES (1, 1, 2, 2)");
CALL sp_prueba('Nivel academico invalido', 'error', "UPDATE programa_version SET nivel = 'bachillerato' WHERE id = 2");
CALL sp_prueba('Perfil de egreso en version autorizada', 'error',
  "INSERT INTO programa_perfil_egreso (programa_version_id, orden, perfil_egreso_id, contribucion) VALUES (1, 9, 3, 'x')");
CALL sp_prueba('Perfil de egreso con orden repetido', 'error',
  "INSERT INTO programa_perfil_egreso (programa_version_id, orden, perfil_egreso_id, contribucion) VALUES (2, 1, 3, 'x')");
CALL sp_prueba('Perfil de egreso en borrador', 'ok',
  "INSERT INTO programa_perfil_egreso (programa_version_id, orden, perfil_egreso_id, contribucion) VALUES (2, 3, 3, 'Aplica pruebas automatizadas')");
CALL sp_prueba('Perfil de egreso con rasgo que no existe en el catalogo', 'error',
  "INSERT INTO programa_perfil_egreso (programa_version_id, orden, perfil_egreso_id, contribucion) VALUES (2, 4, 999, 'x')");
CALL sp_prueba('Mismo rasgo dos veces en la version', 'error',
  "INSERT INTO programa_perfil_egreso (programa_version_id, orden, perfil_egreso_id, contribucion) VALUES (2, 5, 1, 'x')");
CALL sp_prueba('Codigo de rasgo repetido en la misma carrera', 'error',
  "INSERT INTO perfil_egreso (programa_academico, codigo, descripcion) VALUES ('Ingeniería en Sistemas', 'PE-03', 'x')");
CALL sp_prueba('Item con competencia de otra version', 'error',
  "UPDATE programa_unidad_item i JOIN programa_unidad u ON u.id = i.programa_unidad_id
   SET i.competencia_id = (SELECT id FROM programa_competencia WHERE programa_version_id = 1 AND orden = 1)
   WHERE u.programa_version_id = 2 AND u.orden = 1 AND i.orden = 1");
CALL sp_prueba('Cambio de estado fuera de flujo_programa (draft -> approved)', 'error',
  "UPDATE programa_version SET estado_codigo = 'approved' WHERE id = 2");
CALL sp_prueba('PDF de una version en borrador', 'error',
  "INSERT INTO programa_pdf (programa_version_id, archivo_id, hash_contenido, generado_por) VALUES (2, 2, REPEAT('a', 64), 6)");
CALL sp_prueba('Modificar el historial de PDF', 'error', "UPDATE programa_pdf SET generado_por = 1");
CALL sp_prueba('Prioridad invalida', 'error', "UPDATE tarea SET prioridad = 'urgente' WHERE id = 3");
CALL sp_prueba('Prioridad urgent del catalogo prioridad_tarea', 'ok', "UPDATE tarea SET prioridad = 'urgent' WHERE id = 3");
CALL sp_prueba('Borrar una prioridad usada por una tarea', 'error', "DELETE FROM prioridad_tarea WHERE codigo = 'high'");
CALL sp_prueba('Alcance por rol sin rol destino', 'error', "UPDATE tarea SET rol_destino_id = NULL WHERE id = 3");
CALL sp_prueba('Seleccion tipo usuario sin usuario', 'error',
  "INSERT INTO tarea_seleccion (tarea_id, tipo) VALUES (3, 'usuario')");
CALL sp_prueba('Borrador en asignacion pendiente', 'ok',
  "INSERT INTO entrega_borrador (tarea_destinatario_id, contenido_texto, guardado_por) VALUES (4, 'avance', 4)");
CALL sp_prueba('Segundo borrador para la misma asignacion', 'error',
  "INSERT INTO entrega_borrador (tarea_destinatario_id, contenido_texto, guardado_por) VALUES (4, 'otro', 4)");
CALL sp_prueba('Borrador en asignacion ya entregada', 'error',
  "INSERT INTO entrega_borrador (tarea_destinatario_id, contenido_texto, guardado_por) VALUES (3, 'x', 3)");
CALL sp_prueba('Evento repetido (misma clave)', 'error',
  "INSERT INTO evento (nombre, clave_unica, programa_version_id) VALUES ('program.authorized', 'program.authorized:1', 1)");
CALL sp_prueba('Evento con nombre fuera del contrato del G6', 'error',
  "INSERT INTO evento (nombre, clave_unica) VALUES ('task.deleted', 'x:1')");
CALL sp_prueba('Marcar un evento como procesado', 'ok',
  "UPDATE evento SET procesado_en = NOW(3) WHERE nombre = 'program.authorized'");
CALL sp_prueba('Volver a modificar un evento procesado', 'error',
  "UPDATE evento SET procesado_en = NULL WHERE nombre = 'program.authorized'");
CALL sp_prueba('Borrar un evento', 'error', "DELETE FROM evento WHERE nombre = 'program.authorized'");
-- Publicar la tarea 3 a los docentes de Programacion Web en 2026-2 (docente_curso: Diana, Daniel y Maria)
UPDATE tarea SET alcance = 'curso', rol_destino_id = NULL, curso_id = 1, periodo_id = 2, fecha_limite = NOW(3) + INTERVAL 2 DAY WHERE id = 3;
CALL sp_prueba('Publicar tarea a los docentes de un curso', 'ok', "CALL sp_publicar_tarea(3, 2)");
SET @pub_curso = (SELECT COUNT(*) FROM tarea_destinatario WHERE tarea_id = 3);
SET @evt_publicada = (SELECT COUNT(*) FROM evento WHERE clave_unica = 'task.published:3');
CALL sp_generar_eventos_vencimiento(@creados1);
CALL sp_generar_eventos_vencimiento(@creados2);
SET @evt_vence = (SELECT COUNT(*) FROM evento WHERE nombre = 'assignment.due_soon');

ROLLBACK;

-- Chequeos de datos y vistas (se agregan a la misma lista de resultados)
INSERT INTO tmp_resultado_prueba (prueba, esperado, obtenido, resultado)
SELECT 'Eliminar un archivo deja su metadato en auditoria', 'ok', 'ok', IF(@audit_archivo = 1, 'PASA', 'FALLA')
UNION ALL
SELECT 'Las tareas en borrador no aparecen en el inbox', 'ok', 'ok',
       IF((SELECT COUNT(*) FROM v_inbox WHERE tarea_id = 3) = 0, 'PASA', 'FALLA')
UNION ALL
SELECT 'Historial completo de la tarea 1', 'ok', 'ok',
       IF((SELECT COUNT(*) FROM v_historial_tarea WHERE tarea_id = 1) > 0, 'PASA', 'FALLA')
UNION ALL
SELECT 'Una sola version vigente por programa y periodo', 'ok', 'ok',
       IF((SELECT MAX(n) FROM (SELECT COUNT(*) n FROM programa_version WHERE estado_codigo = 'authorized'
                               GROUP BY programa_curso_id, periodo_id) x) = 1, 'PASA', 'FALLA')
UNION ALL
SELECT 'Publicar por curso asigna a los 3 docentes del curso', 'ok', 'ok', IF(@pub_curso = 3, 'PASA', 'FALLA')
UNION ALL
SELECT 'Publicar genera el evento task.published', 'ok', 'ok', IF(@evt_publicada = 1, 'PASA', 'FALLA')
UNION ALL
-- vencen en 3 dias o menos: las 3 asignaciones de la tarea 3 y la prorroga de Daniel (15/10) si aun no pasa
SELECT 'Avisos de vencimiento sin duplicados', 'ok', 'ok',
       IF(@evt_vence = 3 + (SELECT COUNT(*) FROM tarea_destinatario WHERE id = 4
                            AND fecha_limite >= NOW(3) AND fecha_limite < NOW(3) + INTERVAL 3 DAY), 'PASA', 'FALLA')
UNION ALL
SELECT 'Entregas y devoluciones generan eventos', 'ok', 'ok',
       IF((SELECT COUNT(*) FROM evento WHERE nombre = 'assignment.submitted') = 3
          AND (SELECT COUNT(*) FROM evento WHERE nombre = 'assignment.returned') = 1
          AND (SELECT COUNT(*) FROM evento WHERE nombre = 'program.authorized') = 1, 'PASA', 'FALLA')
UNION ALL
SELECT 'La prorroga individual se ve en el inbox', 'ok', 'ok',
       IF((SELECT DATE(fecha_limite) FROM v_inbox WHERE asignacion_id = 4) = '2026-10-15', 'PASA', 'FALLA');

DROP PROCEDURE sp_prueba;

-- Resultado final. Es la ULTIMA instruccion del archivo para que phpMyAdmin la muestre.
-- La primera fila es el resumen: debe decir "pasan 73, fallan 0".
SELECT 0 AS n,
       CONCAT('pasan ', SUM(resultado = 'PASA'), ', fallan ', SUM(resultado = 'FALLA')) AS resultado,
       'RESUMEN' AS prueba, NULL AS esperado, NULL AS obtenido, NULL AS mensaje
FROM tmp_resultado_prueba
UNION ALL
SELECT n, resultado, prueba, esperado, obtenido, mensaje FROM tmp_resultado_prueba
ORDER BY n;

/* Uso de indices en las consultas principales: ejecutelas aparte y revise la columna key.
   Con pocas filas el optimizador puede preferir recorrer la tabla; con datos reales usa el indice.
EXPLAIN SELECT * FROM tarea_destinatario WHERE usuario_id = 3 AND estado_codigo = 'submitted' ORDER BY asignado_en;
EXPLAIN SELECT * FROM tarea_transicion WHERE tarea_destinatario_id = 1 ORDER BY creado_en;
EXPLAIN SELECT * FROM notificacion WHERE usuario_id = 3 AND leida_en IS NULL ORDER BY creado_en DESC;
EXPLAIN SELECT * FROM programa_version WHERE programa_curso_id = 1 AND periodo_id = 1 AND vigente = 1;
*/
