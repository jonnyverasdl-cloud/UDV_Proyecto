-- 02_seed.sql | Grupo 1 - Base de datos | Workflow docente UDV | version 1.2.0
-- Datos semilla: catalogos, roles, permisos, workflow, usuarios demo, tareas y un programa de ejemplo.
-- Ejecutar despues de 01_schema.sql. Usuarios demo: contrasena Demo2026!

USE db_udv;
SET NAMES utf8mb4;

-- Catalogos academicos
insert into facultad (id, codigo, nombre, activo) values
(1, 'FING', 'Facultad de Ingeniería', 1),
(2, 'FCE', 'Facultad de Ciencias Económicas', 1);

insert into sede (id, codigo, nombre, direccion, activo) values
(1, 'S-CEN', 'Sede Central', NULL, 1),
(2, 'S-REG', 'Sede Regional', NULL, 1);

insert into unidad_academica (id, facultad_id, sede_id, codigo, nombre, activo) values
(1, 1, 1, 'UA-ING-C', 'Ingeniería en Sistemas - Sede Central', 1),
(2, 1, 2, 'UA-ING-R', 'Ingeniería en Sistemas - Sede Regional', 1),
(3, 2, 1, 'UA-CE-C',  'Administración de Empresas - Sede Central', 1);

insert into curso (id, codigo, nombre, creditos, activo) values
(1, 'ISW-301', 'Programación Web', 4, 1),
(2, 'ISW-205', 'Redes de Computadoras', 4, 1),
(3, 'ISW-210', 'Bases de Datos I', 4, 1),
(4, 'ISW-101', 'Programación I', 5, 1);

insert into unidad_academica_curso (unidad_academica_id, curso_id) values
(1, 1), (1, 2), (1, 3), (1, 4), (2, 1), (2, 4);

insert into periodo (id, codigo, anio, ciclo, fecha_inicio, fecha_fin) values
(1, '2026-1', 2026, 1, '2026-01-12', '2026-06-12'),
(2, '2026-2', 2026, 2, '2026-07-06', '2026-11-27'),
(3, '2027-1', 2027, 1, '2027-01-11', '2027-06-11');

insert into modalidad (id, codigo, nombre) values
(1, 'PRESENCIAL', 'Presencial'),
(2, 'VIRTUAL',    'Virtual'),
(3, 'HIBRIDA',    'Híbrida');

insert into area (id, codigo, nombre) values
(1, 'DES-SW', 'Desarrollo de software'),
(2, 'INFRA',  'Infraestructura y redes'),
(3, 'DATOS',  'Datos y bases de datos');

-- Estados (CONTRATO_COMUN.md §2)
insert into estado_programa (codigo, nombre, es_final, orden) values
('draft','Borrador',0,1), ('submitted','Enviado',0,2), ('under_review','En revisión',0,3),
('returned','Devuelto',0,4), ('approved','Aprobado',0,5), ('authorized','Autorizado',0,6),
('superseded','Reemplazado',1,7);

insert into flujo_programa (estado_origen, estado_destino, accion) values
('draft',        'submitted',    'submit'),
('submitted',    'under_review', 'review'),
('under_review', 'returned',     'return'),
('returned',     'submitted',    'resubmit'),
('under_review', 'approved',     'approve'),
('approved',     'authorized',   'authorize'),
('authorized',   'superseded',   'supersede');

insert into estado_tarea (codigo, nombre, es_final, orden) values
('draft', 'Borrador', 0, 1),('assigned','Asignada',0,2),('in_progress','En progreso',0,3),
('submitted', 'Entregada', 0, 4),('under_review','En revisión',0,5),('returned','Devuelta',0,6),
('approved', 'Aprobada', 0, 7),('closed','Cerrada',1,8),('cancelled','Cancelada',1,9);

insert into prioridad_tarea (codigo, nombre, orden) values
('low', 'Baja', 1), ('medium', 'Media', 2), ('high', 'Alta', 3), ('urgent', 'Urgente', 4);

-- Seguridad: roles de la matriz del proyecto

insert into rol (id, codigo, nombre, descripcion, activo) values
(1, 'admin',       'Administrador',         'Usuarios, roles, catálogos, tipos de tarea, parámetros y auditoría', 1),
(2, 'coordinator', 'Coordinador académico', 'Crea tareas, selecciona destinatarios, fija plazos, monitorea y asigna revisores', 1),
(3, 'teacher',     'Docente',               'Consulta su inbox, completa formularios, adjunta evidencias y atiende devoluciones', 1),
(4, 'reviewer',    'Revisor',               'Revisa, comenta, aprueba o devuelve entregas', 1),
(5, 'authority',   'Autoridad académica',   'Autoriza la versión final del programa y declara cuál es la vigente', 1),
(6, 'auditor',     'Auditor',               'Consulta versiones, historial y reportes sin modificar', 1);

insert into permiso (id, codigo, descripcion) values
(1,  'users.read',         'Consultar usuarios'),
(2,  'users.create',       'Crear usuarios'),
(3,  'users.update',       'Modificar usuarios'),
(4,  'users.delete',       'Eliminar usuarios (eliminacion logica)'),
(5,  'roles.read',         'Consultar roles'),
(6,  'roles.manage',       'Asignar y quitar roles'),
(7,  'files.upload',       'Subir archivos'),
(8,  'files.download',     'Descargar archivos'),
(9,  'audit.read',         'Consultar historial y auditoria'),
(10, 'tasks.create',       'Crear, editar y publicar tareas'),
(11, 'tasks.assign',       'Elegir destinatarios, plazos y revisores'),
(12, 'tasks.submit',       'Iniciar, completar y entregar asignaciones'),
(13, 'tasks.review',       'Revisar, aprobar o devolver entregas'),
(14, 'programs.manage',    'Crear y editar versiones de programa en borrador'),

(15, 'tasks.monitor',      'Ver panel de estados y cumplimiento'),
(16, 'comments.create',    'Comentar en asignaciones y versiones'),
(17, 'programs.read',      'Consultar programas, versiones y PDF'),
(18, 'programs.review',    'Revisar, aprobar o devolver versiones de programa'),
(19, 'programs.authorize', 'Autorizar la version vigente de un programa'),
(20, 'catalogs.manage',    'Administrar sedes, cursos, periodos y tipos de tarea'),
(21, 'parameters.manage',  'Modificar parametros del sistema');

insert into rol_permiso (rol_id, permiso_id) values

(1,1),(1,2),(1,3),(1,4),(1,5),(1,6),(1,7),(1,8),(1,9),(1,10),(1,11),(1,12),(1,13),(1,14),(1,15),(1,17),(1,20),(1,21),

(2,1),(2,5),(2,7),(2,8),(2,10),(2,11),(2,13),(2,14),(2,15),(2,16),(2,17),

(3,7),(3,8),(3,12),(3,16),(3,17),

(4,1),(4,8),(4,13),(4,14),(4,16),(4,17),(4,18),

(5,8),(5,15),(5,16),(5,17),(5,19),

(6,1),(6,8),(6,9),(6,15),(6,17);

insert into usuario (id, correo, id_academico, nombres, apellidos, hash_contrasena, unidad_academica_id, activo) values
(1, 'admin@demo.udv.edu.gt',        'U-0001', 'Ana',    'Administradora', '$2b$10$IrPNlu9CPcXlLL.viZRic.z3vaku4uuI6eiWVXOoTa.HulL7SJyCu', 1, 1),
(2, 'coordinacion@demo.udv.edu.gt', 'U-0002', 'Carlos', 'Coordinador',    '$2b$10$IrPNlu9CPcXlLL.viZRic.z3vaku4uuI6eiWVXOoTa.HulL7SJyCu', 1, 1),
(3, 'docente1@demo.udv.edu.gt',     'U-0003', 'Diana',  'Pérez',          '$2b$10$IrPNlu9CPcXlLL.viZRic.z3vaku4uuI6eiWVXOoTa.HulL7SJyCu', 1, 1),
(4, 'docente2@demo.udv.edu.gt',     'U-0004', 'Daniel', 'López',          '$2b$10$IrPNlu9CPcXlLL.viZRic.z3vaku4uuI6eiWVXOoTa.HulL7SJyCu', 1, 1),
(5, 'revisor@demo.udv.edu.gt',      'U-0005', 'Rosa',   'Revisora',       '$2b$10$IrPNlu9CPcXlLL.viZRic.z3vaku4uuI6eiWVXOoTa.HulL7SJyCu', 1, 1),
(6, 'direccion@demo.udv.edu.gt',    'U-0006', 'Alberto','Director',       '$2b$10$IrPNlu9CPcXlLL.viZRic.z3vaku4uuI6eiWVXOoTa.HulL7SJyCu', 1, 1),
(7, 'auditoria@demo.udv.edu.gt',    'U-0007', 'Laura',  'Auditora',       '$2b$10$IrPNlu9CPcXlLL.viZRic.z3vaku4uuI6eiWVXOoTa.HulL7SJyCu', 1, 1),
(8, 'docente3@demo.udv.edu.gt',     'U-0008', 'María',  'García',         '$2b$10$IrPNlu9CPcXlLL.viZRic.z3vaku4uuI6eiWVXOoTa.HulL7SJyCu', 2, 1);

insert into usuario_rol (usuario_id, rol_id, asignado_por) values
(1, 1, NULL),
(2, 2, 1),
(3, 3, 1),
(4, 3, 1),
(5, 4, 1),
(5, 3, 1),
(6, 5, 1),
(7, 6, 1),
(8, 3, 1);

insert into docente_curso (usuario_id, curso_id, periodo_id, sede_id, asignado_por) values
(3, 1, 2, 1, 2),
(4, 1, 2, 1, 2),
(8, 1, 2, 2, 2),
(5, 3, 2, 1, 2),
(3, 4, 1, 1, 2);

insert into parametro (codigo, valor, descripcion, actualizado_por) values
('zona_horaria',            'America/Guatemala', 'Zona horaria institucional para mostrar fechas (en BD se guardan en UTC)', 1),
('dias_aviso_vencimiento',  '3',                 'Dias antes del vencimiento en que se envia aviso', 1),
('paginacion_max_por_pagina','100',              'Maximo de per_page en la API', 1),
('archivo_tamano_max_mb',   '20',                'Tamano maximo global de un archivo', 1);

-- Tipos iniciales de tarea
insert into tipo_tarea (id, codigo, nombre, descripcion, modalidad_entrega, requiere_archivo, extensiones, tamano_max_mb) values
(1, 'ACTUALIZAR_PROGRAMA', 'Actualizar programa',  'Entrega del programa de curso por secciones',        'programa',   0, NULL,             10),
(2, 'SUBIR_CV',            'Subir ficha o CV',     'Archivo PDF del CV y fecha de vigencia',             'ambos',      1, 'pdf',            5),
(3, 'ENTREGAR_FACTURA',    'Entregar factura',     'Archivo de la factura con numero, fecha y monto',    'formulario', 1, 'pdf,jpg,png',    5),
(4, 'CONFIRMAR_ACTIVIDAD', 'Confirmar actividad',  'Respuesta de confirmacion y fecha',                  'formulario', 0, NULL,             5),
(5, 'CARGAR_EVIDENCIA',    'Cargar evidencia',     'Uno o varios archivos con su descripcion',           'ambos',      1, 'pdf,docx,jpg,png,xlsx', 20);

insert into tipo_tarea_campo (tipo_tarea_id, codigo, etiqueta, tipo_dato, obligatorio, orden) values
(2, 'vigencia_hasta',  'Vigente hasta',            'fecha',   1, 1),
(3, 'numero_factura',  'Número de factura',        'texto',   1, 1),
(3, 'fecha_factura',   'Fecha de la factura',      'fecha',   1, 2),
(3, 'monto',           'Monto (Q)',                'decimal', 1, 3),
(4, 'respuesta',       'Respuesta',                'opcion',  1, 1),
(4, 'fecha_actividad', 'Fecha de la actividad',    'fecha',   1, 2),
(5, 'descripcion',     'Descripción de la evidencia','texto', 1, 1);

-- Workflow por tipo de tarea (transiciones y roles segun la tabla del CONTRATO del Grupo 3)

insert into workflow (id, nombre, tipo_tarea_id)
select id, concat('Flujo estandar - ', nombre), id from tipo_tarea;

insert into workflow_detalle (workflow_id, estado_origen, estado_destino, accion)
select w.id, t.origen, t.destino, t.accion
from workflow w
cross join (
  select NULL as origen, 'assigned' as destino, 'publish' as accion
  union all select 'assigned',     'in_progress',  'start'
  union all select 'in_progress',  'submitted',    'submit'
  union all select 'submitted',    'under_review', 'review'
  union all select 'under_review', 'returned',     'return'
  union all select 'returned',     'submitted',    'resubmit'
  union all select 'under_review', 'approved',     'approve'
  union all select 'approved',     'closed',       'close'
  union all select 'assigned',     'cancelled',    'cancel'
) t;

insert into workflow_detalle_rol (workflow_detalle_id, rol_id)
select wd.id, r.id
from workflow_detalle wd
join rol r on r.codigo = case
    when wd.accion in ('publish', 'close', 'cancel')           then 'coordinator'
    when wd.accion in ('start', 'submit', 'resubmit')          then 'teacher'
    when wd.accion in ('review', 'return', 'approve')          then 'reviewer'
  end;

insert into workflow_detalle_rol (workflow_detalle_id, rol_id)
select wd.id, (select id from rol where codigo = 'authority') from workflow_detalle wd where wd.accion = 'approve';

-- Programa de curso de ejemplo
insert into programa_curso (id, curso_id, sede_id, modalidad_id, creado_por) values
(1, 1, 1, 1, 2);

insert into programa_version (id, programa_curso_id, numero_version, nombre, periodo_id, estado_codigo,
                              descripcion, resumen_cambios, unidad_academica_id, programa_academico, departamento,
                              nivel, area_id, pensum, horas_clase_semanal, docente_responsable_id, revisor_id, creado_por) values
(1, 1, 1, 'Programación Web - 2026-1', 1, 'draft',
 'Curso teórico-práctico sobre el desarrollo de aplicaciones web con arquitectura cliente-servidor, API REST y bases de datos relacionales.',
 'Versión inicial', 1, 'Ingeniería en Sistemas', 'Departamento de Ciencias de la Computación',
 'licenciatura', 1, '2020', 4.0, 3, 5, 3);

insert into perfil_egreso (id, programa_academico, codigo, descripcion) values
(1, 'Ingeniería en Sistemas', 'PE-03', 'Desarrolla soluciones de software que responden a necesidades de las organizaciones.'),
(2, 'Ingeniería en Sistemas', 'PE-07', 'Trabaja en equipos multidisciplinarios con prácticas profesionales de ingeniería.'),
(3, 'Ingeniería en Sistemas', 'PE-09', 'Asegura la calidad del software mediante pruebas y estándares.');

insert into programa_perfil_egreso (programa_version_id, orden, perfil_egreso_id, contribucion) values
(1, 1, 1, 'Diseña, construye y documenta aplicaciones web seguras e integradas con servicios REST.'),
(1, 2, 2, 'Trabaja en equipo con control de versiones y revisión de código.');

insert into programa_prerrequisito (programa_version_id, curso_requerido_id, orden, tipo) values
(1, 4, 1, 'obligatorio'), (1, 3, 2, 'obligatorio');

insert into programa_competencia (programa_version_id, orden, tipo, descripcion) values
(1, 1, 'general',    'Trabaja en equipo aplicando control de versiones y revisión de código.'),
(1, 2, 'especifica', 'Diseña e implementa endpoints REST con validación, autenticación y manejo uniforme de errores.'),
(1, 3, 'especifica', 'Integra frontend, backend y base de datos mediante un contrato de API documentado en OpenAPI.');

insert into programa_unidad (id, programa_version_id, unidad_padre_id, orden, titulo, horas) values
(1, 1, NULL, 1, 'Fundamentos de la web y HTTP', 12),
(2, 1, NULL, 2, 'Diseño de API REST', 16),
(3, 1, NULL, 3, 'Persistencia y modelo relacional', 16),
(4, 1, NULL, 4, 'Seguridad, pruebas y despliegue', 12);

insert into programa_unidad_item (programa_unidad_id, orden, item, descripcion, competencia_id, actividad, evidencia, punteo) values
(1, 1, 'Protocolo HTTP', 'Métodos, códigos de estado y cabeceras', NULL, NULL, NULL, NULL),
(1, 2, 'HTML, CSS y JavaScript', 'Estructura y comportamiento en el cliente', NULL, NULL, NULL, NULL),
(2, 1, 'Recursos y rutas', 'Convenciones REST y versionado /api/v1', 2, 'Laboratorio de endpoints', 'Repositorio con la API', 5),
(2, 2, 'OpenAPI', 'Documentación del contrato', 3, 'Documentar la API', 'Archivo openapi.yaml', 5);
insert into programa_unidad_item (programa_unidad_id, orden, item, descripcion) values
(3, 1, 'Modelo entidad-relación', 'Claves, índices y restricciones'),
(3, 2, 'Transacciones', 'Integridad y concurrencia'),
(4, 1, 'Autenticación y autorización', 'Tokens, roles y permisos'),
(4, 2, 'Pruebas de endpoints', 'Pruebas automatizadas y despliegue');

insert into programa_bibliografia (programa_version_id, orden, tipo, referencia, isbn, url) values
(1, 1, 'basica',        'Fielding, R. (2000). Architectural Styles and the Design of Network-based Software Architectures.', NULL, 'https://www.ics.uci.edu/~fielding/pubs/dissertation/top.htm'),
(1, 2, 'basica',        'Elmasri, R. y Navathe, S. (2016). Fundamentals of Database Systems (7.a ed.). Pearson.', '9780133970777', NULL),
(1, 3, 'complementaria','MDN Web Docs. HTTP.', NULL, 'https://developer.mozilla.org/es/docs/Web/HTTP');

insert into programa_evaluacion (programa_version_id, orden, nombre, descripcion, ponderacion, semana) values
(1, 1, 'Primer parcial',  'Fundamentos y diseño REST', 20, 6),
(1, 2, 'Segundo parcial', 'Persistencia y seguridad',  20, 12),
(1, 3, 'Proyecto integrador', 'Entrega por grupos con demostración', 35, 16),
(1, 4, 'Examen final',    'Contenido completo',        25, 18);

update programa_version set estado_codigo = 'submitted'    where id = 1;
insert into programa_aprobacion (programa_version_id, actor_id, estado_anterior, estado_nuevo, comentario) values (1, 3, 'draft', 'submitted', 'Envío a revisión');
update programa_version set estado_codigo = 'under_review' where id = 1;
insert into programa_aprobacion (programa_version_id, actor_id, estado_anterior, estado_nuevo, comentario) values (1, 5, 'submitted', 'under_review', NULL);
update programa_version set estado_codigo = 'approved'     where id = 1;
insert into programa_aprobacion (programa_version_id, actor_id, estado_anterior, estado_nuevo, comentario) values (1, 5, 'under_review', 'approved', 'Cumple con el formato institucional');
call sp_autorizar_version(1, 6, 'Se autoriza como versión vigente');

insert into archivo (id, nombre_original, nombre_interno, tipo_mime, tamano_bytes, hash_sha256, ubicacion, autor_id, programa_version_id) values
(1, 'Programa_ISW-301_2026-1.pdf', 'pv1-7f3a2c.pdf', 'application/pdf', 184320,
 'a3f1c2d4e5b6978877665544332211aabbccddeeff00112233445566778899aa', 'programas/2026-1/pv1-7f3a2c.pdf', 6, 1);
update programa_version set pdf_archivo_id = 1, pdf_hash = 'a3f1c2d4e5b6978877665544332211aabbccddeeff00112233445566778899aa',
       pdf_generado_en = CURRENT_TIMESTAMP(3) where id = 1;
insert into programa_pdf (programa_version_id, archivo_id, aprobacion_id, hash_contenido, generado_por)
select 1, 1, max(id), 'a3f1c2d4e5b6978877665544332211aabbccddeeff00112233445566778899aa', 6
from programa_aprobacion where programa_version_id = 1 and estado_nuevo = 'authorized';

insert into programa_version (id, programa_curso_id, numero_version, nombre, periodo_id, estado_codigo,
                              version_origen_id, descripcion, resumen_cambios, unidad_academica_id, programa_academico,
                              departamento, nivel, area_id, pensum, horas_clase_semanal, docente_responsable_id, revisor_id,
                              tarea_destinatario_origen_id, creado_por)
select 2, programa_curso_id, 2, nombre, periodo_id, 'draft', id, descripcion,
       'Actualización de bibliografía', unidad_academica_id, programa_academico, departamento, nivel, area_id,
       pensum, horas_clase_semanal, docente_responsable_id, revisor_id, NULL, 3
from programa_version where id = 1;

insert into programa_perfil_egreso (programa_version_id, orden, perfil_egreso_id, contribucion)
select 2, orden, perfil_egreso_id, contribucion from programa_perfil_egreso where programa_version_id = 1;

insert into programa_prerrequisito (programa_version_id, curso_requerido_id, orden, tipo)
select 2, curso_requerido_id, orden, tipo from programa_prerrequisito where programa_version_id = 1;
insert into programa_competencia (programa_version_id, orden, tipo, descripcion)
select 2, orden, tipo, descripcion from programa_competencia where programa_version_id = 1;
insert into programa_unidad (programa_version_id, unidad_padre_id, orden, titulo, horas)
select 2, NULL, orden, titulo, horas from programa_unidad where programa_version_id = 1 and unidad_padre_id is null;
insert into programa_unidad_item (programa_unidad_id, orden, item, descripcion, competencia_id, actividad, evidencia, punteo)
select u2.id, i.orden, i.item, i.descripcion, c2.id, i.actividad, i.evidencia, i.punteo
from programa_unidad_item i
join programa_unidad u1 on u1.id = i.programa_unidad_id and u1.programa_version_id = 1
join programa_unidad u2 on u2.programa_version_id = 2 and u2.orden = u1.orden and u2.unidad_padre_id is null
left join programa_competencia c1 on c1.id = i.competencia_id
left join programa_competencia c2 on c2.programa_version_id = 2 and c2.orden = c1.orden;
insert into programa_bibliografia (programa_version_id, orden, tipo, referencia, isbn, url)
select 2, orden, tipo, referencia, isbn, url from programa_bibliografia where programa_version_id = 1;
insert into programa_evaluacion (programa_version_id, orden, nombre, descripcion, ponderacion, semana)
select 2, orden, nombre, descripcion, ponderacion, semana from programa_evaluacion where programa_version_id = 1;

-- Escenario minimo de tareas

insert into tarea (id, workflow_id, estado_codigo, creado_por, curso_id, periodo_id, programa_version_id,
                   titulo, descripcion, prioridad, alcance, unidad_destino_id, revisor_id, fecha_limite, publicada_en) values
(1, 1, 'assigned', 2, 1, 1, 2, 'Actualizar programa de Programación Web',
 'Revise y actualice la bibliografía y las evaluaciones del programa vigente.', 'high', 'unidad', 1, 5,
 '2026-12-15 23:59:59', '2026-10-01 08:00:00');

insert into tarea (id, workflow_id, estado_codigo, creado_por, titulo, descripcion, alcance,
                   rol_destino_id, revisor_id, fecha_limite, publicada_en) values
(2, 2, 'assigned', 2, 'Actualizar CV docente 2026',
 'Suba su CV actualizado en PDF e indique la fecha de vigencia.', 'rol', 3, 5,
 '2026-09-30 23:59:59', '2026-09-01 08:00:00');

insert into tarea (id, workflow_id, estado_codigo, creado_por, titulo, alcance, rol_destino_id) values
(3, 4, 'draft', 2, 'Confirmar asistencia a capacitación', 'rol', 3);

insert into tarea_destinatario (id, tarea_id, usuario_id, estado_codigo, asignado_en) values
(1, 1, 3, 'assigned', '2026-10-01 08:00:00'),
(2, 1, 4, 'assigned', '2026-10-01 08:00:00'),
(3, 2, 3, 'assigned', '2026-09-01 08:00:00'),
(4, 2, 4, 'assigned', '2026-09-01 08:00:00');

DELIMITER $$
CREATE PROCEDURE sp_seed_transicion(IN p_td INT, IN p_destino VARCHAR(20), IN p_actor INT, IN p_comentario VARCHAR(1000))
BEGIN
  DECLARE v_origen VARCHAR(20);
  DECLARE v_wd INT;
  SELECT td.estado_codigo INTO v_origen FROM tarea_destinatario td WHERE td.id = p_td;
  SELECT wd.id INTO v_wd FROM workflow_detalle wd
    JOIN tarea t ON t.workflow_id = wd.workflow_id
    JOIN tarea_destinatario td ON td.tarea_id = t.id
   WHERE td.id = p_td AND wd.estado_origen <=> v_origen AND wd.estado_destino = p_destino;
  INSERT INTO tarea_transicion (tarea_destinatario_id, workflow_detalle_id, actor_id, estado_anterior, estado_nuevo, comentario)
  VALUES (p_td, v_wd, p_actor, v_origen, p_destino, p_comentario);
  UPDATE tarea_destinatario SET estado_codigo = p_destino WHERE id = p_td;
END$$
DELIMITER ;

insert into tarea_transicion (tarea_destinatario_id, workflow_detalle_id, actor_id, estado_anterior, estado_nuevo, comentario)
select td.id, wd.id, 2, NULL, 'assigned', 'Publicación de la tarea'
from tarea_destinatario td join tarea t on t.id = td.tarea_id
join workflow_detalle wd on wd.workflow_id = t.workflow_id and wd.estado_origen is null and wd.estado_destino = 'assigned';

call sp_seed_transicion(1, 'in_progress', 3, NULL);
insert into entrega (id, tarea_destinatario_id, numero_intento, entregado_por, contenido_texto, programa_version_id) values
(1, 1, 1, 3, 'Se actualizó la bibliografía (versión 2 del programa).', 2);
call sp_seed_transicion(1, 'submitted', 3, 'Primera entrega');
call sp_seed_transicion(1, 'under_review', 5, NULL);
call sp_seed_transicion(1, 'returned', 5, 'Agregue al menos una referencia publicada en los últimos 5 años.');
insert into comentario (autor_id, tarea_destinatario_id, contenido) values
(5, 1, 'Agregue al menos una referencia publicada en los últimos 5 años.');
insert into comentario (autor_id, tarea_destinatario_id, comentario_padre_id, contenido) values
(3, 1, 1, 'Listo, agregué la referencia de 2023.');
insert into entrega (id, tarea_destinatario_id, numero_intento, entregado_por, contenido_texto, programa_version_id) values
(2, 1, 2, 3, 'Bibliografía actualizada con referencia reciente.', 2);
call sp_seed_transicion(1, 'submitted', 3, 'Segunda entrega');

call sp_seed_transicion(3, 'in_progress', 3, NULL);
insert into entrega (id, tarea_destinatario_id, numero_intento, entregado_por) values (3, 3, 1, 3);
insert into entrega_valor (entrega_id, campo_id, valor)
select 3, id, '2027-12-31' from tipo_tarea_campo where tipo_tarea_id = 2 and codigo = 'vigencia_hasta';
insert into archivo (id, nombre_original, nombre_interno, tipo_mime, tamano_bytes, hash_sha256, ubicacion, autor_id, entrega_id) values
(2, 'CV Diana Pérez.pdf', 'e3-91bd0f.pdf', 'application/pdf', 96256,
 'b4e2d3c4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2', 'entregas/2026/e3-91bd0f.pdf', 3, 3);
call sp_seed_transicion(3, 'submitted', 3, NULL);

DROP PROCEDURE sp_seed_transicion;

update programa_version set tarea_destinatario_origen_id = 1 where id = 2;

insert into entrega_borrador (tarea_destinatario_id, contenido_texto, guardado_por) values
(2, 'Borrador: revisar unidades 3 y 4.', 4);

update tarea_destinatario set fecha_limite = '2026-10-15 23:59:59' where id = 4;

insert into notificacion (usuario_id, tipo, titulo, mensaje, tarea_destinatario_id, evento_id)
select 3, 'assignment.returned', 'Tarea devuelta', 'Su entrega de "Actualizar programa de Programación Web" fue devuelta con observaciones.', 1, id
from evento where nombre = 'assignment.returned' and tarea_destinatario_id = 1;
insert into notificacion (usuario_id, tipo, titulo, mensaje, tarea_destinatario_id) values
(4, 'assignment.due_soon', 'Tarea vencida', 'La tarea "Actualizar CV docente 2026" venció el 30/09/2026.', 4),
(5, 'assignment.submitted', 'Nueva entrega', 'Diana Pérez entregó "Actualizar programa de Programación Web".', 1);

update evento set procesado_en = CURRENT_TIMESTAMP(3) where nombre = 'assignment.returned' and tarea_destinatario_id = 1;
