-- db_udv_completo.sql: 01_schema + 02_triggers + 03_inserts + 04_vistas en un solo archivo (generado).
/* =====================================================================
   01_schema.sql | Grupo 1 - Base de datos | Workflow docente UDV
   Motor: MariaDB 10.4+ (XAMPP)  |  utf8mb4
   Orden: 01_schema -> 02_triggers -> 03_inserts -> 04_vistas -> 05_verificacion
   ATENCION: borra y recrea la base db_udv desde cero.
   Convenciones:
   - IDs enteros AUTO_INCREMENT (pendiente confirmar con el Grupo 2).
   - Estados en ingles y minusculas (CONTRATO_COMUN.md §2).
   - creado_en / actualizado_en con CURRENT_TIMESTAMP(3).
   - Eliminacion logica con eliminado_en / eliminado_por; los DELETE fisicos se bloquean en 02_triggers.sql.
   Version 1.1.0: incorpora aportes del esquema de Pablo (modalidad, area, docente_curso,
   flujo_programa, perfil de egreso, datos del encabezado del programa, seleccion de
   destinatarios, borrador de entrega, eventos para notificaciones, historial de PDF,
   bloqueo de login y accion/roles por transicion).
   ===================================================================== */
DROP DATABASE IF EXISTS db_udv;
SET NAMES utf8mb4;
CREATE DATABASE db_udv CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE db_udv;

/* ============================== 1. ACADEMICO ============================== */
CREATE TABLE facultad (
    id              INT          NOT NULL AUTO_INCREMENT,
    codigo          VARCHAR(20)  NOT NULL,
    nombre          VARCHAR(150) NOT NULL,
    activo          TINYINT(1)   NOT NULL DEFAULT 1,
    creado_en       DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    actualizado_en  DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    CONSTRAINT uq_facultad_codigo UNIQUE (codigo)
) ENGINE=InnoDB;

CREATE TABLE sede (
    id              INT          NOT NULL AUTO_INCREMENT,
    codigo          VARCHAR(20)  NOT NULL,
    nombre          VARCHAR(150) NOT NULL,
    direccion       VARCHAR(300) NULL,
    activo          TINYINT(1)   NOT NULL DEFAULT 1,
    creado_en       DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    actualizado_en  DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    CONSTRAINT uq_sede_codigo UNIQUE (codigo)
) ENGINE=InnoDB;

CREATE TABLE unidad_academica (
    id              INT          NOT NULL AUTO_INCREMENT,
    facultad_id     INT          NOT NULL,
    sede_id         INT          NOT NULL,
    codigo          VARCHAR(20)  NOT NULL,
    nombre          VARCHAR(150) NOT NULL,
    activo          TINYINT(1)   NOT NULL DEFAULT 1,
    creado_en       DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    actualizado_en  DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    CONSTRAINT uq_unidad_academica_codigo UNIQUE (codigo),
    CONSTRAINT fk_ua_facultad FOREIGN KEY (facultad_id) REFERENCES facultad(id),
    CONSTRAINT fk_ua_sede     FOREIGN KEY (sede_id)     REFERENCES sede(id)
) ENGINE=InnoDB;

CREATE TABLE periodo (
    id            INT               NOT NULL AUTO_INCREMENT,
    codigo        VARCHAR(20)       NOT NULL,            -- ej. 2026-S1
    anio          SMALLINT          NOT NULL,
    ciclo         TINYINT UNSIGNED  NOT NULL,
    fecha_inicio  DATE              NOT NULL,
    fecha_fin     DATE              NOT NULL,
    activo        TINYINT(1)        NOT NULL DEFAULT 1,
    creado_en     DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    CONSTRAINT uq_periodo_codigo UNIQUE (codigo),
    CONSTRAINT uq_periodo_anio_ciclo UNIQUE (anio, ciclo),
    CONSTRAINT ck_periodo_fechas CHECK (fecha_fin > fecha_inicio)
) ENGINE=InnoDB;

-- Modalidad en que se imparte un curso (presencial, virtual...). Distingue programas del mismo curso y sede.
CREATE TABLE modalidad (
    id              INT          NOT NULL AUTO_INCREMENT,
    codigo          VARCHAR(20)  NOT NULL,
    nombre          VARCHAR(100) NOT NULL,
    activo          TINYINT(1)   NOT NULL DEFAULT 1,
    creado_en       DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    actualizado_en  DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    CONSTRAINT uq_modalidad_codigo UNIQUE (codigo)
) ENGINE=InnoDB;

-- Area de conocimiento del curso (aparece en el encabezado del programa)
CREATE TABLE area (
    id              INT          NOT NULL AUTO_INCREMENT,
    codigo          VARCHAR(20)  NOT NULL,
    nombre          VARCHAR(100) NOT NULL,
    activo          TINYINT(1)   NOT NULL DEFAULT 1,
    creado_en       DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    actualizado_en  DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    CONSTRAINT uq_area_codigo UNIQUE (codigo)
) ENGINE=InnoDB;

/* ============================== 2. SEGURIDAD ============================== */
CREATE TABLE usuario (
    id                   INT          NOT NULL AUTO_INCREMENT,
    correo               VARCHAR(254) NOT NULL,           -- unico; la collation _ci evita duplicados por mayusculas
    id_academico         VARCHAR(20)  NULL,
    nombres              VARCHAR(100) NOT NULL,
    apellidos            VARCHAR(100) NOT NULL,
    telefono             VARCHAR(20)  NULL,
    hash_contrasena      VARCHAR(255) NOT NULL,           -- bcrypt; nunca texto plano
    unidad_academica_id  INT          NULL,
    activo               TINYINT(1)   NOT NULL DEFAULT 1,
    ultimo_acceso_en     DATETIME(3)  NULL,
    intentos_fallidos    TINYINT UNSIGNED NOT NULL DEFAULT 0,  -- intentos de login fallidos seguidos
    bloqueado_hasta      DATETIME(3)  NULL,               -- bloqueo temporal tras varios intentos fallidos
    creado_en           DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    actualizado_en       DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    eliminado_en         DATETIME(3)  NULL,
    eliminado_por        INT          NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_usuario_correo UNIQUE (correo),
    CONSTRAINT uq_usuario_id_academico UNIQUE (id_academico),
    CONSTRAINT fk_usuario_ua            FOREIGN KEY (unidad_academica_id) REFERENCES unidad_academica(id),
    CONSTRAINT fk_usuario_eliminado_por FOREIGN KEY (eliminado_por)       REFERENCES usuario(id)
) ENGINE=InnoDB;

CREATE TABLE rol (
    id              INT          NOT NULL AUTO_INCREMENT,
    codigo          VARCHAR(30)  NOT NULL,
    nombre          VARCHAR(80)  NOT NULL,
    descripcion     VARCHAR(300) NULL,
    activo          TINYINT(1)   NOT NULL DEFAULT 1,
    creado_en       DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    actualizado_en  DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    CONSTRAINT uq_rol_codigo UNIQUE (codigo),
    CONSTRAINT ck_rol_codigo CHECK (codigo REGEXP BINARY '^[a-z][a-z_]*$')   -- ingles, minusculas, sin espacios (acuerdo con G2)
) ENGINE=InnoDB;

CREATE TABLE permiso (
    id           INT          NOT NULL AUTO_INCREMENT,
    codigo       VARCHAR(60)  NOT NULL,
    descripcion  VARCHAR(300) NULL,
    creado_en    DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    CONSTRAINT uq_permiso_codigo UNIQUE (codigo),
    CONSTRAINT ck_permiso_codigo CHECK (codigo REGEXP BINARY '^[a-z][a-z_]*\\.[a-z][a-z_]*$')   -- recurso.accion
) ENGINE=InnoDB;

CREATE TABLE usuario_rol (
    usuario_id    INT          NOT NULL,
    rol_id        INT          NOT NULL,
    asignado_por  INT          NULL,
    asignado_en   DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    PRIMARY KEY (usuario_id, rol_id),
    CONSTRAINT fk_ur_usuario      FOREIGN KEY (usuario_id)   REFERENCES usuario(id),
    CONSTRAINT fk_ur_rol          FOREIGN KEY (rol_id)       REFERENCES rol(id),
    CONSTRAINT fk_ur_asignado_por FOREIGN KEY (asignado_por) REFERENCES usuario(id)
) ENGINE=InnoDB;

CREATE TABLE rol_permiso (
    rol_id      INT          NOT NULL,
    permiso_id  INT          NOT NULL,
    creado_en   DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    PRIMARY KEY (rol_id, permiso_id),
    CONSTRAINT fk_rp_rol     FOREIGN KEY (rol_id)     REFERENCES rol(id),
    CONSTRAINT fk_rp_permiso FOREIGN KEY (permiso_id) REFERENCES permiso(id)
) ENGINE=InnoDB;

CREATE TABLE sesion_token (
    id           BIGINT       NOT NULL AUTO_INCREMENT,
    usuario_id   INT          NOT NULL,
    token_hash   CHAR(64)     NOT NULL,                   -- SHA-256 del token; el token en claro nunca se guarda
    tipo         VARCHAR(10)  NOT NULL,
    emitido_en   DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    expira_en    DATETIME(3)  NOT NULL,
    revocado_en  DATETIME(3)  NULL,
    ip_origen    VARCHAR(45)  NULL,
    user_agent   VARCHAR(300) NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_sesion_token_hash UNIQUE (token_hash),
    CONSTRAINT ck_sesion_tipo CHECK (tipo IN ('access', 'refresh', 'reset')),
    CONSTRAINT fk_sesion_usuario FOREIGN KEY (usuario_id) REFERENCES usuario(id),
    INDEX ix_sesion_usuario_expira (usuario_id, expira_en)   -- sesiones activas de un usuario
) ENGINE=InnoDB;

/* ============================== 3. CURSOS ============================== */
CREATE TABLE curso (
    id              INT               NOT NULL AUTO_INCREMENT,
    codigo          VARCHAR(20)       NOT NULL,
    nombre          VARCHAR(150)      NOT NULL,
    creditos        TINYINT UNSIGNED  NOT NULL,
    activo          TINYINT(1)        NOT NULL DEFAULT 1,
    creado_en       DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    actualizado_en  DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    eliminado_en    DATETIME(3)       NULL,
    eliminado_por   INT               NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_curso_codigo UNIQUE (codigo),
    CONSTRAINT fk_curso_eliminado_por FOREIGN KEY (eliminado_por) REFERENCES usuario(id)
) ENGINE=InnoDB;

CREATE TABLE unidad_academica_curso (
    unidad_academica_id  INT          NOT NULL,
    curso_id             INT          NOT NULL,
    activo               TINYINT(1)   NOT NULL DEFAULT 1,
    creado_en            DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    PRIMARY KEY (unidad_academica_id, curso_id),
    CONSTRAINT fk_uac_ua    FOREIGN KEY (unidad_academica_id) REFERENCES unidad_academica(id),
    CONSTRAINT fk_uac_curso FOREIGN KEY (curso_id)            REFERENCES curso(id)
) ENGINE=InnoDB;

-- Que docente imparte que curso, en que periodo y sede. Permite publicar tareas "a los docentes del curso X".
CREATE TABLE docente_curso (
    usuario_id    INT          NOT NULL,
    curso_id      INT          NOT NULL,
    periodo_id    INT          NOT NULL,
    sede_id       INT          NOT NULL,
    activo        TINYINT(1)   NOT NULL DEFAULT 1,
    asignado_por  INT          NULL,
    creado_en     DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    PRIMARY KEY (usuario_id, curso_id, periodo_id, sede_id),
    CONSTRAINT fk_dc_usuario  FOREIGN KEY (usuario_id)   REFERENCES usuario(id),
    CONSTRAINT fk_dc_curso    FOREIGN KEY (curso_id)     REFERENCES curso(id),
    CONSTRAINT fk_dc_periodo  FOREIGN KEY (periodo_id)   REFERENCES periodo(id),
    CONSTRAINT fk_dc_sede     FOREIGN KEY (sede_id)      REFERENCES sede(id),
    CONSTRAINT fk_dc_asignado FOREIGN KEY (asignado_por) REFERENCES usuario(id),
    INDEX ix_dc_curso_periodo (curso_id, periodo_id, sede_id)
) ENGINE=InnoDB;

/* ============================== 4. WORKFLOW ============================== */
CREATE TABLE estado_tarea (
    codigo    VARCHAR(20)       NOT NULL,
    nombre    VARCHAR(60)       NOT NULL,
    es_final  TINYINT(1)        NOT NULL DEFAULT 0,
    orden     TINYINT UNSIGNED  NOT NULL,
    PRIMARY KEY (codigo)
) ENGINE=InnoDB;

CREATE TABLE tipo_tarea (
    id                 INT               NOT NULL AUTO_INCREMENT,
    codigo             VARCHAR(30)       NOT NULL,
    nombre             VARCHAR(100)      NOT NULL,
    descripcion        VARCHAR(300)      NULL,
    modalidad_entrega  VARCHAR(10)       NOT NULL,
    requiere_archivo   TINYINT(1)        NOT NULL DEFAULT 0,   -- 1 = no se entrega sin adjunto (422)
    extensiones        VARCHAR(100)      NULL,                 -- ej. 'pdf,docx'
    tamano_max_mb      SMALLINT UNSIGNED NOT NULL DEFAULT 10,
    activo             TINYINT(1)        NOT NULL DEFAULT 1,
    creado_en          DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    actualizado_en     DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    CONSTRAINT uq_tipo_tarea_codigo UNIQUE (codigo),
    CONSTRAINT ck_tipo_tarea_modalidad CHECK (modalidad_entrega IN ('texto', 'archivo', 'ambos', 'formulario', 'programa'))
) ENGINE=InnoDB;

-- Campos propios de cada tipo (factura: numero, fecha, monto). Un tipo nuevo no obliga a cambiar el esquema.
CREATE TABLE tipo_tarea_campo (
    id             INT          NOT NULL AUTO_INCREMENT,
    tipo_tarea_id  INT          NOT NULL,
    codigo         VARCHAR(40)  NOT NULL,
    etiqueta       VARCHAR(100) NOT NULL,
    tipo_dato      VARCHAR(10)  NOT NULL,
    obligatorio    TINYINT(1)   NOT NULL DEFAULT 1,
    orden          SMALLINT     NOT NULL,
    activo         TINYINT(1)   NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT uq_ttc_codigo UNIQUE (tipo_tarea_id, codigo),
    CONSTRAINT uq_ttc_orden  UNIQUE (tipo_tarea_id, orden),
    CONSTRAINT ck_ttc_tipo_dato CHECK (tipo_dato IN ('texto', 'numero', 'decimal', 'fecha', 'booleano', 'opcion')),
    CONSTRAINT fk_ttc_tipo_tarea FOREIGN KEY (tipo_tarea_id) REFERENCES tipo_tarea(id)
) ENGINE=InnoDB;

-- Maquina de estados configurable por tipo de tarea
CREATE TABLE workflow (
    id              INT          NOT NULL AUTO_INCREMENT,
    nombre          VARCHAR(100) NOT NULL,
    tipo_tarea_id   INT          NOT NULL,
    activo          TINYINT(1)   NOT NULL DEFAULT 1,
    creado_en       DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    actualizado_en  DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    CONSTRAINT fk_workflow_tipo_tarea FOREIGN KEY (tipo_tarea_id) REFERENCES tipo_tarea(id)
) ENGINE=InnoDB;

CREATE TABLE workflow_detalle (
    id              INT          NOT NULL AUTO_INCREMENT,
    workflow_id     INT          NOT NULL,
    estado_origen   VARCHAR(20)  NULL,                    -- NULL = transicion inicial (al publicar)
    estado_destino  VARCHAR(20)  NOT NULL,
    accion          VARCHAR(20)  NOT NULL,                -- accion de la API que produce la transicion
    origen_clave    VARCHAR(20)  AS (IFNULL(estado_origen, '')) STORED,  -- los NULL no chocan en un UNIQUE
    PRIMARY KEY (id),
    CONSTRAINT uq_wd_transicion UNIQUE (workflow_id, origen_clave, estado_destino),
    CONSTRAINT ck_wd_accion CHECK (accion IN ('publish', 'start', 'submit', 'review', 'return', 'resubmit', 'approve', 'close', 'cancel')),
    CONSTRAINT fk_wd_workflow FOREIGN KEY (workflow_id)    REFERENCES workflow(id),
    CONSTRAINT fk_wd_origen   FOREIGN KEY (estado_origen)  REFERENCES estado_tarea(codigo),
    CONSTRAINT fk_wd_destino  FOREIGN KEY (estado_destino) REFERENCES estado_tarea(codigo)
) ENGINE=InnoDB;

-- Roles que pueden ejecutar cada transicion (una transicion puede tener varios roles)
CREATE TABLE workflow_detalle_rol (
    workflow_detalle_id  INT  NOT NULL,
    rol_id               INT  NOT NULL,
    PRIMARY KEY (workflow_detalle_id, rol_id),
    CONSTRAINT fk_wdr_detalle FOREIGN KEY (workflow_detalle_id) REFERENCES workflow_detalle(id),
    CONSTRAINT fk_wdr_rol     FOREIGN KEY (rol_id)              REFERENCES rol(id)
) ENGINE=InnoDB;

/* ============================== 5. PROGRAMAS DE CURSO ============================== */
CREATE TABLE estado_programa (
    codigo    VARCHAR(20)       NOT NULL,
    nombre    VARCHAR(60)       NOT NULL,
    es_final  TINYINT(1)        NOT NULL DEFAULT 0,
    orden     TINYINT UNSIGNED  NOT NULL,
    PRIMARY KEY (codigo)
) ENGINE=InnoDB;

-- Transiciones validas de una version de programa (las define el CONTRATO del G5)
CREATE TABLE flujo_programa (
    estado_origen   VARCHAR(20)  NOT NULL,
    estado_destino  VARCHAR(20)  NOT NULL,
    accion          VARCHAR(20)  NOT NULL,
    PRIMARY KEY (estado_origen, estado_destino),
    CONSTRAINT ck_fp_accion CHECK (accion IN ('submit', 'review', 'return', 'resubmit', 'approve', 'authorize', 'supersede')),
    CONSTRAINT fk_fp_origen  FOREIGN KEY (estado_origen)  REFERENCES estado_programa(codigo),
    CONSTRAINT fk_fp_destino FOREIGN KEY (estado_destino) REFERENCES estado_programa(codigo)
) ENGINE=InnoDB;

-- Identidad logica: un curso en una sede y una modalidad (el "contexto" del requerimiento)
CREATE TABLE programa_curso (
    id              INT          NOT NULL AUTO_INCREMENT,
    curso_id        INT          NOT NULL,
    sede_id         INT          NOT NULL,
    modalidad_id    INT          NOT NULL,
    activo          TINYINT(1)   NOT NULL DEFAULT 1,
    creado_por      INT          NOT NULL,
    creado_en       DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    actualizado_en  DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    CONSTRAINT uq_programa_curso_ctx UNIQUE (curso_id, sede_id, modalidad_id),
    CONSTRAINT fk_pc_curso      FOREIGN KEY (curso_id)     REFERENCES curso(id),
    CONSTRAINT fk_pc_sede       FOREIGN KEY (sede_id)      REFERENCES sede(id),
    CONSTRAINT fk_pc_modalidad  FOREIGN KEY (modalidad_id) REFERENCES modalidad(id),
    CONSTRAINT fk_pc_creado_por FOREIGN KEY (creado_por)   REFERENCES usuario(id)
) ENGINE=InnoDB;

-- Versiones independientes; solo una autorizada (vigente) por programa y periodo
CREATE TABLE programa_version (
    id                 INT           NOT NULL AUTO_INCREMENT,
    programa_curso_id  INT           NOT NULL,
    numero_version     SMALLINT      NOT NULL,
    periodo_id         INT           NOT NULL,
    estado_codigo      VARCHAR(20)   NOT NULL DEFAULT 'draft',
    version_origen_id  INT           NULL,                -- version de la que se clono
    nombre             VARCHAR(200)  NOT NULL,
    descripcion        TEXT          NULL,
    resumen_cambios    VARCHAR(1000) NULL,
    -- Datos del encabezado del PDF institucional
    unidad_academica_id     INT           NULL,
    programa_academico      VARCHAR(150)  NULL,          -- carrera, ej. Ingenieria en Sistemas
    departamento            VARCHAR(150)  NULL,
    nivel                   VARCHAR(15)   NULL,
    area_id                 INT           NULL,
    pensum                  VARCHAR(50)   NULL,
    horas_clase_semanal     DECIMAL(4,1)  NULL,
    docente_responsable_id  INT           NULL,
    revisor_id              INT           NULL,
    tarea_destinatario_origen_id INT      NULL,          -- asignacion "Actualizar programa" que produjo esta version
    creado_por         INT           NOT NULL,
    autorizado_por     INT           NULL,
    autorizado_en      DATETIME(3)   NULL,
    observaciones_autorizacion VARCHAR(1000) NULL,
    pdf_archivo_id     INT           NULL,                -- documento final (FK al final del script)
    pdf_hash           CHAR(64)      NULL,
    pdf_generado_en    DATETIME(3)   NULL,
    creado_en          DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    actualizado_en     DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    -- 1 solo si esta autorizada; NULL en otro caso (los NULL no chocan en el UNIQUE)
    vigente            TINYINT(1)    AS (IF(estado_codigo = 'authorized', 1, NULL)) STORED,
    PRIMARY KEY (id),
    CONSTRAINT uq_pv_numero  UNIQUE (programa_curso_id, numero_version),
    CONSTRAINT uq_pv_vigente UNIQUE (programa_curso_id, periodo_id, vigente),   -- una sola vigente
    CONSTRAINT ck_pv_numero CHECK (numero_version > 0),
    CONSTRAINT ck_pv_nivel  CHECK (nivel IS NULL OR nivel IN ('tecnico', 'licenciatura', 'maestria', 'doctorado')),
    CONSTRAINT ck_pv_horas  CHECK (horas_clase_semanal IS NULL OR horas_clase_semanal > 0),
    CONSTRAINT fk_pv_ua          FOREIGN KEY (unidad_academica_id)    REFERENCES unidad_academica(id),
    CONSTRAINT fk_pv_area        FOREIGN KEY (area_id)                REFERENCES area(id),
    CONSTRAINT fk_pv_docente     FOREIGN KEY (docente_responsable_id) REFERENCES usuario(id),
    CONSTRAINT fk_pv_revisor     FOREIGN KEY (revisor_id)             REFERENCES usuario(id),
    CONSTRAINT fk_pv_programa       FOREIGN KEY (programa_curso_id) REFERENCES programa_curso(id),
    CONSTRAINT fk_pv_periodo        FOREIGN KEY (periodo_id)        REFERENCES periodo(id),
    CONSTRAINT fk_pv_estado         FOREIGN KEY (estado_codigo)     REFERENCES estado_programa(codigo),
    CONSTRAINT fk_pv_origen         FOREIGN KEY (version_origen_id) REFERENCES programa_version(id),
    CONSTRAINT fk_pv_creado_por     FOREIGN KEY (creado_por)        REFERENCES usuario(id),
    CONSTRAINT fk_pv_autorizado_por FOREIGN KEY (autorizado_por)    REFERENCES usuario(id),
    INDEX ix_pv_estado (estado_codigo)
) ENGINE=InnoDB;

CREATE TABLE programa_prerrequisito (
    id                   INT          NOT NULL AUTO_INCREMENT,
    programa_version_id  INT          NOT NULL,
    curso_requerido_id   INT          NOT NULL,
    orden                SMALLINT     NOT NULL,
    tipo                 VARCHAR(15)  NOT NULL DEFAULT 'obligatorio',
    PRIMARY KEY (id),
    CONSTRAINT uq_prereq UNIQUE (programa_version_id, curso_requerido_id),
    CONSTRAINT uq_prereq_orden UNIQUE (programa_version_id, orden),
    CONSTRAINT ck_prereq_tipo CHECK (tipo IN ('obligatorio', 'correquisito', 'recomendado')),
    CONSTRAINT fk_prereq_pv    FOREIGN KEY (programa_version_id) REFERENCES programa_version(id),
    CONSTRAINT fk_prereq_curso FOREIGN KEY (curso_requerido_id)  REFERENCES curso(id)
) ENGINE=InnoDB;

CREATE TABLE programa_competencia (
    id                   INT           NOT NULL AUTO_INCREMENT,
    programa_version_id  INT           NOT NULL,
    orden                SMALLINT      NOT NULL,
    tipo                 VARCHAR(15)   NOT NULL,
    descripcion          VARCHAR(1000) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_competencia_orden UNIQUE (programa_version_id, orden),
    CONSTRAINT ck_competencia_tipo CHECK (tipo IN ('general', 'especifica')),
    CONSTRAINT fk_competencia_pv FOREIGN KEY (programa_version_id) REFERENCES programa_version(id)
) ENGINE=InnoDB;

-- Plan de contenidos: modulos (unidad_padre_id NULL) y unidades dentro de un modulo
CREATE TABLE programa_unidad (
    id                   INT           NOT NULL AUTO_INCREMENT,
    programa_version_id  INT           NOT NULL,
    unidad_padre_id      INT           NULL,
    orden                SMALLINT      NOT NULL,
    titulo               VARCHAR(200)  NOT NULL,
    horas                DECIMAL(5,1)  NULL,
    padre_clave          INT           AS (IFNULL(unidad_padre_id, 0)) STORED,
    PRIMARY KEY (id),
    CONSTRAINT uq_unidad_orden UNIQUE (programa_version_id, padre_clave, orden),
    CONSTRAINT ck_unidad_horas CHECK (horas IS NULL OR horas >= 0),
    CONSTRAINT fk_unidad_pv    FOREIGN KEY (programa_version_id) REFERENCES programa_version(id),
    CONSTRAINT fk_unidad_padre FOREIGN KEY (unidad_padre_id)     REFERENCES programa_unidad(id)
) ENGINE=InnoDB;

CREATE TABLE programa_unidad_item (
    id                  INT           NOT NULL AUTO_INCREMENT,
    programa_unidad_id  INT           NOT NULL,
    orden               SMALLINT      NOT NULL,
    item                VARCHAR(200)  NOT NULL,
    descripcion         VARCHAR(1000) NULL,
    competencia_id      INT           NULL,               -- competencia que desarrolla (de la misma version, ver trigger)
    actividad           VARCHAR(300)  NULL,
    evidencia           VARCHAR(300)  NULL,
    punteo              DECIMAL(5,2)  NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_unidad_item_orden UNIQUE (programa_unidad_id, orden),
    CONSTRAINT ck_unidad_item_punteo CHECK (punteo IS NULL OR (punteo >= 0 AND punteo <= 100)),
    CONSTRAINT fk_unidad_item_unidad      FOREIGN KEY (programa_unidad_id) REFERENCES programa_unidad(id),
    CONSTRAINT fk_unidad_item_competencia FOREIGN KEY (competencia_id)     REFERENCES programa_competencia(id)
) ENGINE=InnoDB;

-- Contribucion del curso al perfil de egreso, en orden
-- Catalogo de rasgos del perfil de egreso de cada carrera (se escriben una vez y los programas los referencian)
CREATE TABLE perfil_egreso (
    id                   INT           NOT NULL AUTO_INCREMENT,
    programa_academico   VARCHAR(150)  NOT NULL,          -- carrera, ej. Ingenieria en Sistemas
    codigo               VARCHAR(30)   NOT NULL,          -- codigo del rasgo, ej. PE-03
    descripcion          VARCHAR(1000) NOT NULL,          -- texto oficial del rasgo
    activo               TINYINT(1)    NOT NULL DEFAULT 1,
    creado_en            DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    actualizado_en       DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    CONSTRAINT uq_perfil_egreso_carrera_codigo UNIQUE (programa_academico, codigo)
) ENGINE=InnoDB;

-- Rasgos del perfil a los que contribuye una version del programa
CREATE TABLE programa_perfil_egreso (
    id                   INT           NOT NULL AUTO_INCREMENT,
    programa_version_id  INT           NOT NULL,
    orden                SMALLINT      NOT NULL,
    perfil_egreso_id     INT           NOT NULL,          -- rasgo del catalogo
    contribucion         VARCHAR(1000) NOT NULL,          -- como contribuye este curso al rasgo
    PRIMARY KEY (id),
    CONSTRAINT uq_perfil_egreso_orden  UNIQUE (programa_version_id, orden),
    CONSTRAINT uq_perfil_egreso_rasgo  UNIQUE (programa_version_id, perfil_egreso_id),
    CONSTRAINT fk_perfil_egreso_pv     FOREIGN KEY (programa_version_id) REFERENCES programa_version(id),
    CONSTRAINT fk_perfil_egreso_rasgo  FOREIGN KEY (perfil_egreso_id)    REFERENCES perfil_egreso(id)
) ENGINE=InnoDB;

CREATE TABLE programa_bibliografia (
    id                   INT           NOT NULL AUTO_INCREMENT,
    programa_version_id  INT           NOT NULL,
    orden                SMALLINT      NOT NULL,
    tipo                 VARCHAR(15)   NOT NULL,
    referencia           VARCHAR(1000) NOT NULL,
    isbn                 VARCHAR(17)   NULL,
    url                  VARCHAR(500)  NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_bibliografia_orden UNIQUE (programa_version_id, orden),
    CONSTRAINT ck_bibliografia_tipo CHECK (tipo IN ('basica', 'complementaria')),
    CONSTRAINT fk_bibliografia_pv FOREIGN KEY (programa_version_id) REFERENCES programa_version(id)
) ENGINE=InnoDB;

CREATE TABLE programa_evaluacion (
    id                   INT               NOT NULL AUTO_INCREMENT,
    programa_version_id  INT               NOT NULL,
    orden                SMALLINT          NOT NULL,
    nombre               VARCHAR(150)      NOT NULL,
    descripcion          VARCHAR(500)      NULL,
    ponderacion          DECIMAL(5,2)      NOT NULL,      -- porcentaje; total por version = 100 (ver triggers)
    semana               TINYINT UNSIGNED  NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_evaluacion_orden UNIQUE (programa_version_id, orden),
    CONSTRAINT ck_evaluacion_ponderacion CHECK (ponderacion > 0 AND ponderacion <= 100),
    CONSTRAINT fk_evaluacion_pv FOREIGN KEY (programa_version_id) REFERENCES programa_version(id)
) ENGINE=InnoDB;

/* ============================== 6. TAREAS, ASIGNACIONES Y ENTREGAS ============================== */
-- La solicitud que crea el coordinador
CREATE TABLE tarea (
    id                   INT          NOT NULL AUTO_INCREMENT,
    workflow_id          INT          NOT NULL,                  -- el tipo de tarea sale de workflow.tipo_tarea_id
    estado_codigo        VARCHAR(20)  NOT NULL DEFAULT 'draft',  -- draft = no visible en inbox
    titulo               VARCHAR(200) NOT NULL,
    descripcion          TEXT         NULL,                      -- instrucciones
    prioridad            VARCHAR(10)  NOT NULL DEFAULT 'medium',
    creado_por           INT          NOT NULL,
    revisor_id           INT          NULL,
    alcance              VARCHAR(12)  NOT NULL DEFAULT 'individual',  -- ver sp_publicar_tarea
    rol_destino_id       INT          NULL,                      -- publicacion masiva por rol
    sede_destino_id      INT          NULL,                      -- ... por sede
    unidad_destino_id    INT          NULL,                      -- ... por unidad academica
    curso_id             INT          NULL,                      -- alcance 'curso': docentes de docente_curso
    periodo_id           INT          NULL,
    programa_version_id  INT          NULL,                      -- para "Actualizar programa"
    fecha_limite         DATETIME(3)  NULL,
    publicada_en         DATETIME(3)  NULL,
    creado_en            DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    actualizado_en       DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    eliminado_en         DATETIME(3)  NULL,
    eliminado_por        INT          NULL,
    PRIMARY KEY (id),
    CONSTRAINT ck_tarea_alcance CHECK (alcance IN ('individual', 'rol', 'sede', 'unidad', 'todos', 'curso', 'seleccion')),
    CONSTRAINT ck_tarea_alcance_destino CHECK (
           (alcance <> 'rol'    OR rol_destino_id IS NOT NULL)
       AND (alcance <> 'sede'   OR sede_destino_id IS NOT NULL)
       AND (alcance <> 'unidad' OR unidad_destino_id IS NOT NULL)
       AND (alcance <> 'curso'  OR (curso_id IS NOT NULL AND periodo_id IS NOT NULL))),
    CONSTRAINT ck_tarea_prioridad CHECK (prioridad IN ('low', 'medium', 'high')),
    CONSTRAINT ck_tarea_publicada CHECK (estado_codigo = 'draft' OR publicada_en IS NOT NULL),
    CONSTRAINT fk_tarea_workflow       FOREIGN KEY (workflow_id)         REFERENCES workflow(id),
    CONSTRAINT fk_tarea_estado         FOREIGN KEY (estado_codigo)       REFERENCES estado_tarea(codigo),
    CONSTRAINT fk_tarea_creado_por     FOREIGN KEY (creado_por)          REFERENCES usuario(id),
    CONSTRAINT fk_tarea_revisor        FOREIGN KEY (revisor_id)          REFERENCES usuario(id),
    CONSTRAINT fk_tarea_rol_destino    FOREIGN KEY (rol_destino_id)      REFERENCES rol(id),
    CONSTRAINT fk_tarea_sede_destino   FOREIGN KEY (sede_destino_id)     REFERENCES sede(id),
    CONSTRAINT fk_tarea_unidad_destino FOREIGN KEY (unidad_destino_id)   REFERENCES unidad_academica(id),
    CONSTRAINT fk_tarea_curso          FOREIGN KEY (curso_id)            REFERENCES curso(id),
    CONSTRAINT fk_tarea_periodo        FOREIGN KEY (periodo_id)          REFERENCES periodo(id),
    CONSTRAINT fk_tarea_pv             FOREIGN KEY (programa_version_id) REFERENCES programa_version(id),
    CONSTRAINT fk_tarea_eliminado_por  FOREIGN KEY (eliminado_por)       REFERENCES usuario(id),
    INDEX ix_tarea_creador (creado_por, estado_codigo, creado_en),   -- "mis tareas" del coordinador
    INDEX ix_tarea_revisor (revisor_id, estado_codigo),              -- bandeja del revisor
    INDEX ix_tarea_curso_periodo (curso_id, periodo_id)
) ENGINE=InnoDB;

-- Criterios de destinatarios combinables (alcance 'seleccion'): usuarios sueltos, unidades, sedes, cursos o todos
CREATE TABLE tarea_seleccion (
    id                   INT          NOT NULL AUTO_INCREMENT,
    tarea_id             INT          NOT NULL,
    tipo                 VARCHAR(10)  NOT NULL,
    usuario_id           INT          NULL,
    unidad_academica_id  INT          NULL,
    sede_id              INT          NULL,
    curso_id             INT          NULL,               -- con tarea.periodo_id, via docente_curso
    valor_clave          INT          AS (COALESCE(usuario_id, unidad_academica_id, sede_id, curso_id, 0)) STORED,
    creado_en            DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    CONSTRAINT uq_tarea_seleccion UNIQUE (tarea_id, tipo, valor_clave),
    CONSTRAINT ck_ts_tipo CHECK (tipo IN ('usuario', 'todos', 'unidad', 'sede', 'curso')),
    CONSTRAINT ck_ts_valor CHECK (
           (tipo = 'todos'   AND usuario_id IS NULL AND unidad_academica_id IS NULL AND sede_id IS NULL AND curso_id IS NULL)
        OR (tipo = 'usuario' AND usuario_id IS NOT NULL AND unidad_academica_id IS NULL AND sede_id IS NULL AND curso_id IS NULL)
        OR (tipo = 'unidad'  AND unidad_academica_id IS NOT NULL AND usuario_id IS NULL AND sede_id IS NULL AND curso_id IS NULL)
        OR (tipo = 'sede'    AND sede_id IS NOT NULL AND usuario_id IS NULL AND unidad_academica_id IS NULL AND curso_id IS NULL)
        OR (tipo = 'curso'   AND curso_id IS NOT NULL AND usuario_id IS NULL AND unidad_academica_id IS NULL AND sede_id IS NULL)),
    CONSTRAINT fk_ts_tarea   FOREIGN KEY (tarea_id)            REFERENCES tarea(id),
    CONSTRAINT fk_ts_usuario FOREIGN KEY (usuario_id)          REFERENCES usuario(id),
    CONSTRAINT fk_ts_ua      FOREIGN KEY (unidad_academica_id) REFERENCES unidad_academica(id),
    CONSTRAINT fk_ts_sede    FOREIGN KEY (sede_id)             REFERENCES sede(id),
    CONSTRAINT fk_ts_curso   FOREIGN KEY (curso_id)            REFERENCES curso(id)
) ENGINE=InnoDB;

-- Asignacion individual: una fila por tarea y docente
CREATE TABLE tarea_destinatario (
    id              INT          NOT NULL AUTO_INCREMENT,
    tarea_id        INT          NOT NULL,
    usuario_id      INT          NOT NULL,
    estado_codigo   VARCHAR(20)  NOT NULL DEFAULT 'assigned',
    fecha_limite    DATETIME(3)  NULL,                    -- prorroga individual; NULL = la de la tarea
    revisor_id      INT          NULL,                    -- revisor de esta asignacion; NULL = el de la tarea
    asignado_en     DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    actualizado_en  DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    CONSTRAINT uq_td_tarea_usuario UNIQUE (tarea_id, usuario_id),   -- una asignacion por tarea y destinatario
    CONSTRAINT fk_td_tarea   FOREIGN KEY (tarea_id)      REFERENCES tarea(id),
    CONSTRAINT fk_td_usuario FOREIGN KEY (usuario_id)    REFERENCES usuario(id),
    CONSTRAINT fk_td_estado  FOREIGN KEY (estado_codigo) REFERENCES estado_tarea(codigo),
    CONSTRAINT fk_td_revisor FOREIGN KEY (revisor_id)    REFERENCES usuario(id),
    INDEX ix_td_inbox (usuario_id, estado_codigo, asignado_en),     -- inbox del docente filtrado por estado
    INDEX ix_td_tarea_estado (tarea_id, estado_codigo)              -- panel de cumplimiento por tarea
) ENGINE=InnoDB;

-- Historial inmutable de cambios de estado de una asignacion
CREATE TABLE tarea_transicion (
    id                     BIGINT        NOT NULL AUTO_INCREMENT,
    tarea_destinatario_id  INT           NOT NULL,
    workflow_detalle_id    INT           NOT NULL,
    actor_id               INT           NOT NULL,
    estado_anterior        VARCHAR(20)   NULL,
    estado_nuevo           VARCHAR(20)   NOT NULL,
    comentario             VARCHAR(1000) NULL,             -- obligatorio en devoluciones (trigger)
    secuencia              SMALLINT      NOT NULL DEFAULT 0, -- 1, 2, 3... por asignacion (lo calcula el trigger)
    creado_en              DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    CONSTRAINT uq_tt_secuencia UNIQUE (tarea_destinatario_id, secuencia),  -- evita dos transiciones simultaneas
    CONSTRAINT fk_tt_td       FOREIGN KEY (tarea_destinatario_id) REFERENCES tarea_destinatario(id),
    CONSTRAINT fk_tt_wd       FOREIGN KEY (workflow_detalle_id)   REFERENCES workflow_detalle(id),
    CONSTRAINT fk_tt_actor    FOREIGN KEY (actor_id)              REFERENCES usuario(id),
    CONSTRAINT fk_tt_anterior FOREIGN KEY (estado_anterior)       REFERENCES estado_tarea(codigo),
    CONSTRAINT fk_tt_nuevo    FOREIGN KEY (estado_nuevo)          REFERENCES estado_tarea(codigo),
    INDEX ix_tt_historial (tarea_destinatario_id, creado_en)
) ENGINE=InnoDB;

-- Cada envio es un intento nuevo; los anteriores se conservan como evidencia
CREATE TABLE entrega (
    id                     INT          NOT NULL AUTO_INCREMENT,
    tarea_destinatario_id  INT          NOT NULL,
    numero_intento         SMALLINT     NOT NULL,
    entregado_por          INT          NOT NULL,
    contenido_texto        TEXT         NULL,
    programa_version_id    INT          NULL,             -- version de programa entregada (tipo ACTUALIZAR_PROGRAMA)
    entregado_en           DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    CONSTRAINT uq_entrega_intento UNIQUE (tarea_destinatario_id, numero_intento),
    CONSTRAINT ck_entrega_intento CHECK (numero_intento > 0),
    CONSTRAINT fk_entrega_td  FOREIGN KEY (tarea_destinatario_id) REFERENCES tarea_destinatario(id),
    CONSTRAINT fk_entrega_por FOREIGN KEY (entregado_por)         REFERENCES usuario(id),
    CONSTRAINT fk_entrega_pv  FOREIGN KEY (programa_version_id)   REFERENCES programa_version(id)
) ENGINE=InnoDB;

CREATE TABLE entrega_valor (
    entrega_id  INT           NOT NULL,
    campo_id    INT           NOT NULL,
    valor       VARCHAR(2000) NULL,
    PRIMARY KEY (entrega_id, campo_id),
    CONSTRAINT fk_ev_entrega FOREIGN KEY (entrega_id) REFERENCES entrega(id),
    CONSTRAINT fk_ev_campo   FOREIGN KEY (campo_id)   REFERENCES tipo_tarea_campo(id)
) ENGINE=InnoDB;

-- Avance guardado sin enviar: uno por asignacion; se sobrescribe y se descarta al entregar
CREATE TABLE entrega_borrador (
    id                     INT          NOT NULL AUTO_INCREMENT,
    tarea_destinatario_id  INT          NOT NULL,
    contenido_texto        TEXT         NULL,
    valores                LONGTEXT     NULL,             -- JSON {codigo_campo: valor} del formulario
    programa_version_id    INT          NULL,
    guardado_por           INT          NOT NULL,
    creado_en              DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    actualizado_en         DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    CONSTRAINT uq_entrega_borrador_td UNIQUE (tarea_destinatario_id),
    CONSTRAINT ck_eb_valores CHECK (valores IS NULL OR JSON_VALID(valores)),
    CONSTRAINT fk_eb_td      FOREIGN KEY (tarea_destinatario_id) REFERENCES tarea_destinatario(id),
    CONSTRAINT fk_eb_pv      FOREIGN KEY (programa_version_id)   REFERENCES programa_version(id),
    CONSTRAINT fk_eb_usuario FOREIGN KEY (guardado_por)          REFERENCES usuario(id)
) ENGINE=InnoDB;

/* ============================== 7. COLABORACION ============================== */
CREATE TABLE comentario (
    id                     INT          NOT NULL AUTO_INCREMENT,
    autor_id               INT          NOT NULL,
    tarea_destinatario_id  INT          NULL,
    programa_version_id    INT          NULL,
    comentario_padre_id    INT          NULL,              -- respuestas en hilo
    contenido              TEXT         NOT NULL,
    creado_en              DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    actualizado_en         DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    eliminado_en           DATETIME(3)  NULL,
    eliminado_por          INT          NULL,
    PRIMARY KEY (id),
    CONSTRAINT ck_comentario_destino CHECK (tarea_destinatario_id IS NOT NULL OR programa_version_id IS NOT NULL),
    CONSTRAINT fk_com_autor         FOREIGN KEY (autor_id)              REFERENCES usuario(id),
    CONSTRAINT fk_com_td            FOREIGN KEY (tarea_destinatario_id) REFERENCES tarea_destinatario(id),
    CONSTRAINT fk_com_pv            FOREIGN KEY (programa_version_id)   REFERENCES programa_version(id),
    CONSTRAINT fk_com_padre         FOREIGN KEY (comentario_padre_id)   REFERENCES comentario(id),
    CONSTRAINT fk_com_eliminado_por FOREIGN KEY (eliminado_por)         REFERENCES usuario(id),
    INDEX ix_com_td (tarea_destinatario_id, creado_en),
    INDEX ix_com_pv (programa_version_id, creado_en)
) ENGINE=InnoDB;

CREATE TABLE archivo (
    id                   INT          NOT NULL AUTO_INCREMENT,
    nombre_original      VARCHAR(255) NOT NULL,
    nombre_interno       VARCHAR(100) NOT NULL,
    tipo_mime            VARCHAR(127) NOT NULL,
    tamano_bytes         BIGINT       NOT NULL,
    hash_sha256          CHAR(64)     NOT NULL,
    ubicacion            VARCHAR(500) NOT NULL,
    autor_id             INT          NOT NULL,
    entrega_id           INT          NULL,
    comentario_id        INT          NULL,
    programa_version_id  INT          NULL,
    reemplazado_por_id   INT          NULL,               -- reemplazo logico: apunta al archivo nuevo
    creado_en            DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    eliminado_en         DATETIME(3)  NULL,
    eliminado_por        INT          NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_archivo_nombre_interno UNIQUE (nombre_interno),
    CONSTRAINT ck_archivo_tamano CHECK (tamano_bytes > 0),
    -- a lo sumo un destino; los tres NULL = archivo subido antes de asociarlo (si el equipo elige ese flujo)
    CONSTRAINT ck_archivo_destino CHECK ((entrega_id IS NOT NULL) + (comentario_id IS NOT NULL) + (programa_version_id IS NOT NULL) <= 1),
    CONSTRAINT ck_archivo_hash CHECK (hash_sha256 REGEXP '^[0-9a-f]{64}$'),             -- SHA-256 en hexadecimal
    CONSTRAINT ck_archivo_nombre_interno CHECK (nombre_interno REGEXP '^[A-Za-z0-9._-]+$'), -- sin espacios ni rutas
    CONSTRAINT fk_archivo_reemplazo     FOREIGN KEY (reemplazado_por_id)  REFERENCES archivo(id),
    CONSTRAINT fk_archivo_autor         FOREIGN KEY (autor_id)            REFERENCES usuario(id),
    CONSTRAINT fk_archivo_entrega       FOREIGN KEY (entrega_id)          REFERENCES entrega(id),
    CONSTRAINT fk_archivo_comentario    FOREIGN KEY (comentario_id)       REFERENCES comentario(id),
    CONSTRAINT fk_archivo_pv            FOREIGN KEY (programa_version_id) REFERENCES programa_version(id),
    CONSTRAINT fk_archivo_eliminado_por FOREIGN KEY (eliminado_por)       REFERENCES usuario(id),
    INDEX ix_archivo_hash (hash_sha256)
) ENGINE=InnoDB;

-- Eventos de dominio para el Grupo 6 (CONTRATO del G6 §3). Los generan los triggers de 02_triggers.sql;
-- el proceso de notificaciones lee los pendientes (procesado_en IS NULL) y los marca al terminar.
-- clave_unica evita que el mismo hecho se notifique dos veces.
CREATE TABLE evento (
    id                     BIGINT        NOT NULL AUTO_INCREMENT,
    nombre                 VARCHAR(40)   NOT NULL,
    clave_unica            VARCHAR(120)  NOT NULL,
    tarea_id               INT           NULL,
    tarea_destinatario_id  INT           NULL,
    programa_version_id    INT           NULL,
    actor_id               INT           NULL,
    payload                LONGTEXT      NULL,
    creado_en              DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    procesado_en           DATETIME(3)   NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_evento_clave UNIQUE (clave_unica),
    CONSTRAINT ck_evento_nombre CHECK (nombre IN ('task.published', 'assignment.due_soon', 'assignment.submitted',
                                                  'assignment.returned', 'assignment.approved', 'program.authorized', 'task.cancelled')),
    CONSTRAINT ck_evento_payload CHECK (payload IS NULL OR JSON_VALID(payload)),
    CONSTRAINT fk_evento_tarea FOREIGN KEY (tarea_id)              REFERENCES tarea(id),
    CONSTRAINT fk_evento_td    FOREIGN KEY (tarea_destinatario_id) REFERENCES tarea_destinatario(id),
    CONSTRAINT fk_evento_pv    FOREIGN KEY (programa_version_id)   REFERENCES programa_version(id),
    CONSTRAINT fk_evento_actor FOREIGN KEY (actor_id)              REFERENCES usuario(id),
    INDEX ix_evento_pendientes (procesado_en, id)
) ENGINE=InnoDB;

CREATE TABLE notificacion (
    id                     BIGINT        NOT NULL AUTO_INCREMENT,
    usuario_id             INT           NOT NULL,
    tipo                   VARCHAR(40)   NOT NULL,        -- nombre del evento (CONTRATO del G6 §3)
    titulo                 VARCHAR(200)  NOT NULL,
    mensaje                VARCHAR(1000) NOT NULL,
    tarea_destinatario_id  INT           NULL,
    programa_version_id    INT           NULL,
    evento_id              BIGINT        NULL,            -- evento que origino el aviso
    leida_en               DATETIME(3)   NULL,
    creado_en              DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    CONSTRAINT fk_notif_usuario FOREIGN KEY (usuario_id)            REFERENCES usuario(id),
    CONSTRAINT fk_notif_td      FOREIGN KEY (tarea_destinatario_id) REFERENCES tarea_destinatario(id),
    CONSTRAINT fk_notif_pv      FOREIGN KEY (programa_version_id)   REFERENCES programa_version(id),
    CONSTRAINT fk_notif_evento  FOREIGN KEY (evento_id)             REFERENCES evento(id),
    CONSTRAINT uq_notif_evento_usuario UNIQUE (evento_id, usuario_id),   -- un aviso por evento y usuario
    INDEX ix_notif_usuario (usuario_id, leida_en, creado_en)
) ENGINE=InnoDB;

/* ============================== 8. APROBACION Y AUDITORIA ============================== */
CREATE TABLE programa_aprobacion (
    id                   BIGINT        NOT NULL AUTO_INCREMENT,
    programa_version_id  INT           NOT NULL,
    actor_id             INT           NOT NULL,
    estado_anterior      VARCHAR(20)   NULL,
    estado_nuevo         VARCHAR(20)   NOT NULL,
    comentario           VARCHAR(1000) NULL,
    creado_en            DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    CONSTRAINT fk_aprob_pv       FOREIGN KEY (programa_version_id) REFERENCES programa_version(id),
    CONSTRAINT fk_aprob_actor    FOREIGN KEY (actor_id)            REFERENCES usuario(id),
    CONSTRAINT fk_aprob_anterior FOREIGN KEY (estado_anterior)     REFERENCES estado_programa(codigo),
    CONSTRAINT fk_aprob_nuevo    FOREIGN KEY (estado_nuevo)        REFERENCES estado_programa(codigo),
    INDEX ix_aprob_historial (programa_version_id, creado_en)
) ENGINE=InnoDB;

-- Historial de PDF generados por version (el oficial vigente queda en programa_version.pdf_archivo_id)
CREATE TABLE programa_pdf (
    id                   INT          NOT NULL AUTO_INCREMENT,
    programa_version_id  INT          NOT NULL,
    archivo_id           INT          NOT NULL,
    aprobacion_id        BIGINT       NULL,               -- autorizacion que lo origino
    hash_contenido       CHAR(64)     NOT NULL,
    generado_por         INT          NOT NULL,
    generado_en          DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    CONSTRAINT uq_programa_pdf_archivo UNIQUE (archivo_id),
    CONSTRAINT ck_ppdf_hash CHECK (hash_contenido REGEXP '^[0-9a-f]{64}$'),
    CONSTRAINT fk_ppdf_pv         FOREIGN KEY (programa_version_id) REFERENCES programa_version(id),
    CONSTRAINT fk_ppdf_archivo    FOREIGN KEY (archivo_id)          REFERENCES archivo(id),
    CONSTRAINT fk_ppdf_aprobacion FOREIGN KEY (aprobacion_id)       REFERENCES programa_aprobacion(id),
    CONSTRAINT fk_ppdf_generado   FOREIGN KEY (generado_por)        REFERENCES usuario(id),
    INDEX ix_ppdf_version (programa_version_id, generado_en)
) ENGINE=InnoDB;

CREATE TABLE auditoria (
    id           BIGINT       NOT NULL AUTO_INCREMENT,
    tabla        VARCHAR(64)  NOT NULL,
    registro_id  VARCHAR(64)  NOT NULL,
    accion       VARCHAR(20)  NOT NULL,                   -- insert | update | soft_delete | login ...
    actor_id     INT          NULL,
    ip_origen    VARCHAR(45)  NULL,
    detalle      LONGTEXT     NULL,                       -- JSON con valores anteriores/nuevos
    creado_en    DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    CONSTRAINT ck_auditoria_detalle CHECK (detalle IS NULL OR JSON_VALID(detalle)),
    CONSTRAINT fk_auditoria_actor FOREIGN KEY (actor_id) REFERENCES usuario(id),
    INDEX ix_auditoria_registro (tabla, registro_id, creado_en),
    INDEX ix_auditoria_actor (actor_id, creado_en)
) ENGINE=InnoDB;

/* ============================== 9. ADMINISTRACION ============================== */
-- Control de versiones del esquema: cada migracion registra una fila
CREATE TABLE schema_migracion (
    version      VARCHAR(20)  NOT NULL,
    descripcion  VARCHAR(200) NOT NULL,
    aplicada_en  DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    PRIMARY KEY (version)
) ENGINE=InnoDB;

CREATE TABLE parametro (
    codigo           VARCHAR(60)  NOT NULL,
    valor            VARCHAR(500) NOT NULL,
    descripcion      VARCHAR(300) NULL,
    actualizado_por  INT          NULL,
    actualizado_en   DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (codigo),
    CONSTRAINT fk_parametro_usuario FOREIGN KEY (actualizado_por) REFERENCES usuario(id)
) ENGINE=InnoDB;

-- FK circulares de programa_version (archivo y asignacion se crean despues)
ALTER TABLE programa_version
    ADD CONSTRAINT fk_pv_pdf_archivo FOREIGN KEY (pdf_archivo_id) REFERENCES archivo(id),
    ADD CONSTRAINT fk_pv_td_origen   FOREIGN KEY (tarea_destinatario_origen_id) REFERENCES tarea_destinatario(id);

INSERT INTO schema_migracion (version, descripcion) VALUES
('1.0.0', 'Esquema inicial (01_schema.sql)'),
('1.1.0', 'Aportes del esquema de Pablo: modalidad, area, docente_curso, flujo_programa, perfil de egreso, seleccion, borrador, evento, programa_pdf');
/* =====================================================================
   02_triggers.sql | Reglas de integridad que la base hace cumplir por si misma
   Ejecutar despues de 01_schema.sql. Los errores usan SQLSTATE 45000; el texto
   indica el codigo HTTP que la API deberia devolver (409, 422...).
   ===================================================================== */
USE db_udv;
SET NAMES utf8mb4;

DELIMITER $$

/*------------------------------------------------ Historial inmutable (bitacoras) ------------------------------------------------*/
-- auditoria: solo se inserta
CREATE TRIGGER trg_auditoria_no_update BEFORE UPDATE ON auditoria FOR EACH ROW
BEGIN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'auditoria es de solo insercion: no se permite UPDATE';
END$$

CREATE TRIGGER trg_auditoria_no_delete BEFORE DELETE ON auditoria FOR EACH ROW
BEGIN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'auditoria es de solo insercion: no se permite DELETE';
END$$

-- tarea_transicion: solo se inserta
CREATE TRIGGER trg_tarea_transicion_no_update BEFORE UPDATE ON tarea_transicion FOR EACH ROW
BEGIN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El historial de transiciones no se modifica';
END$$

CREATE TRIGGER trg_tarea_transicion_no_delete BEFORE DELETE ON tarea_transicion FOR EACH ROW
BEGIN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El historial de transiciones no se elimina';
END$$

-- programa_aprobacion: solo se inserta
CREATE TRIGGER trg_programa_aprobacion_no_update BEFORE UPDATE ON programa_aprobacion FOR EACH ROW
BEGIN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El historial de aprobaciones no se modifica';
END$$

CREATE TRIGGER trg_programa_aprobacion_no_delete BEFORE DELETE ON programa_aprobacion FOR EACH ROW
BEGIN
SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El historial de aprobaciones no se elimina';
END$$

-- Las entregas son evidencia: una correccion es un nuevo intento, nunca se edita el anterior
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

/*------------------------------------------------ Eliminacion logica: no se permite DELETE fisico ------------------------------------------------*/
-- Se usa eliminado_en / eliminado_por (o el estado 'cancelled' en las asignaciones).
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

-- Al eliminar logicamente un archivo se audita su metadato (nombre, tipo, ubicacion, hash y autor)
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

/*------------------------------------------------ Workflow de tareas ------------------------------------------------*/
-- Toda transicion debe partir del estado actual de la asignacion y existir en el workflow de la tarea.
-- Orden en la API (dentro de una transaccion): 1) INSERT en tarea_transicion  2) UPDATE de tarea_destinatario.estado_codigo
CREATE TRIGGER trg_tt_valida BEFORE INSERT ON tarea_transicion FOR EACH ROW
BEGIN
  DECLARE v_estado_actual VARCHAR(20);
  DECLARE v_workflow_tarea INT;
  DECLARE v_ok INT DEFAULT 0;

  SELECT td.estado_codigo, t.workflow_id INTO v_estado_actual, v_workflow_tarea
  FROM tarea_destinatario td JOIN tarea t ON t.id = td.tarea_id
  WHERE td.id = NEW.tarea_destinatario_id;

  IF NEW.estado_anterior IS NULL THEN
    -- transicion inicial: solo una por asignacion
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

  -- Numero de transicion dentro de la asignacion. Es UNIQUE: si dos sesiones intentan
  -- transicionar la misma asignacion a la vez, ambas calculan el mismo numero y la segunda falla.
  SET NEW.secuencia = (SELECT COUNT(*) + 1 FROM tarea_transicion WHERE tarea_destinatario_id = NEW.tarea_destinatario_id);

  -- Toda devolucion exige una observacion
  IF NEW.estado_nuevo = 'returned' AND (NEW.comentario IS NULL OR TRIM(NEW.comentario) = '') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: una devolucion exige una observacion (422)';
  END IF;
END$$

/*------------------------------------------------ Programas de curso ------------------------------------------------*/
CREATE FUNCTION fn_pv_bloqueada(p_pv_id INT) RETURNS TINYINT(1)
READS SQL DATA
BEGIN
  -- Una version autorizada o reemplazada no admite cambios en su contenido
  RETURN (SELECT COUNT(*) FROM programa_version
          WHERE id = p_pv_id AND estado_codigo IN ('authorized', 'superseded')) > 0;
END$$

-- Inmutabilidad de una version autorizada
-- Solo se permite: pasar a 'superseded' sin cambiar contenido, o registrar el PDF una unica vez.
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

  -- Todo cambio de estado debe estar definido en flujo_programa
  IF NEW.estado_codigo <> OLD.estado_codigo
     AND NOT EXISTS (SELECT 1 FROM flujo_programa
                     WHERE estado_origen = OLD.estado_codigo AND estado_destino = NEW.estado_codigo) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: cambio de estado del programa no permitido por flujo_programa (409)';
  END IF;

  IF OLD.estado_codigo = 'authorized' THEN
    IF NOT v_mismo_contenido
       OR NOT (
            -- reemplazo por una nueva version autorizada
            (NEW.estado_codigo = 'superseded'
             AND NEW.pdf_archivo_id <=> OLD.pdf_archivo_id AND NEW.pdf_hash <=> OLD.pdf_hash)
            -- registro del PDF oficial (una sola vez)
         OR (NEW.estado_codigo = 'authorized' AND OLD.pdf_hash IS NULL)
          ) THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Version autorizada: no se modifica, cree una nueva version (409)';
    END IF;
  END IF;

  -- Al enviar a revision las evaluaciones deben sumar exactamente 100
  IF NEW.estado_codigo = 'submitted' AND OLD.estado_codigo <> 'submitted' THEN
    SELECT IFNULL(SUM(ponderacion), 0) INTO v_total
    FROM programa_evaluacion WHERE programa_version_id = NEW.id;
    IF v_total <> 100 THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: las evaluaciones deben sumar 100 para enviar el programa (422)';
    END IF;
  END IF;

  -- Al autorizar se exige quien y cuando
  IF NEW.estado_codigo = 'authorized' AND OLD.estado_codigo <> 'authorized'
     AND (NEW.autorizado_por IS NULL OR NEW.autorizado_en IS NULL) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: autorizar requiere autorizado_por y autorizado_en';
  END IF;
END$$

-- Una devolucion de programa exige observacion
CREATE TRIGGER trg_aprobacion_valida BEFORE INSERT ON programa_aprobacion FOR EACH ROW
BEGIN
  IF NEW.estado_nuevo = 'returned' AND (NEW.comentario IS NULL OR TRIM(NEW.comentario) = '') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ERROR: una devolucion exige una observacion (422)';
  END IF;
END$$

-- Contenido de una version bloqueada: competencias
CREATE TRIGGER trg_competencia_bi BEFORE INSERT ON programa_competencia FOR EACH ROW
BEGIN IF fn_pv_bloqueada(NEW.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$
CREATE TRIGGER trg_competencia_bu BEFORE UPDATE ON programa_competencia FOR EACH ROW
BEGIN IF fn_pv_bloqueada(OLD.programa_version_id) OR fn_pv_bloqueada(NEW.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$
CREATE TRIGGER trg_competencia_bd BEFORE DELETE ON programa_competencia FOR EACH ROW
BEGIN IF fn_pv_bloqueada(OLD.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$

-- prerrequisitos
CREATE TRIGGER trg_prereq_bi BEFORE INSERT ON programa_prerrequisito FOR EACH ROW
BEGIN IF fn_pv_bloqueada(NEW.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$
CREATE TRIGGER trg_prereq_bu BEFORE UPDATE ON programa_prerrequisito FOR EACH ROW
BEGIN IF fn_pv_bloqueada(OLD.programa_version_id) OR fn_pv_bloqueada(NEW.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$
CREATE TRIGGER trg_prereq_bd BEFORE DELETE ON programa_prerrequisito FOR EACH ROW
BEGIN IF fn_pv_bloqueada(OLD.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$

-- unidades
CREATE TRIGGER trg_unidad_bi BEFORE INSERT ON programa_unidad FOR EACH ROW
BEGIN IF fn_pv_bloqueada(NEW.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$
CREATE TRIGGER trg_unidad_bu BEFORE UPDATE ON programa_unidad FOR EACH ROW
BEGIN IF fn_pv_bloqueada(OLD.programa_version_id) OR fn_pv_bloqueada(NEW.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$
CREATE TRIGGER trg_unidad_bd BEFORE DELETE ON programa_unidad FOR EACH ROW
BEGIN IF fn_pv_bloqueada(OLD.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$

-- items de unidad (la version se obtiene a traves de la unidad)
CREATE TRIGGER trg_unidad_item_bi BEFORE INSERT ON programa_unidad_item FOR EACH ROW
BEGIN
  IF fn_pv_bloqueada((SELECT programa_version_id FROM programa_unidad WHERE id = NEW.programa_unidad_id)) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version';
  END IF;
  -- la competencia asociada debe ser de la misma version
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

-- bibliografia
CREATE TRIGGER trg_bibliografia_bi BEFORE INSERT ON programa_bibliografia FOR EACH ROW
BEGIN IF fn_pv_bloqueada(NEW.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$
CREATE TRIGGER trg_bibliografia_bu BEFORE UPDATE ON programa_bibliografia FOR EACH ROW
BEGIN IF fn_pv_bloqueada(OLD.programa_version_id) OR fn_pv_bloqueada(NEW.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$
CREATE TRIGGER trg_bibliografia_bd BEFORE DELETE ON programa_bibliografia FOR EACH ROW
BEGIN IF fn_pv_bloqueada(OLD.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$

-- perfil de egreso
CREATE TRIGGER trg_perfil_egreso_bi BEFORE INSERT ON programa_perfil_egreso FOR EACH ROW
BEGIN IF fn_pv_bloqueada(NEW.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$
CREATE TRIGGER trg_perfil_egreso_bu BEFORE UPDATE ON programa_perfil_egreso FOR EACH ROW
BEGIN IF fn_pv_bloqueada(OLD.programa_version_id) OR fn_pv_bloqueada(NEW.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$
CREATE TRIGGER trg_perfil_egreso_bd BEFORE DELETE ON programa_perfil_egreso FOR EACH ROW
BEGIN IF fn_pv_bloqueada(OLD.programa_version_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Version autorizada: el contenido no se modifica, cree una nueva version'; END IF; END$$

-- historial de PDF: solo de versiones autorizadas y nunca se modifica
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

-- evaluaciones: bloqueo + el total nunca pasa de 100
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

/*------------------------------------------------ Procedimiento de autorizacion ------------------------------------------------*/
-- Autoriza una version aprobada. Si ya habia una vigente para el mismo programa y periodo,
-- la pasa a 'superseded' en la misma transaccion. Deja el registro en programa_aprobacion.
CREATE PROCEDURE sp_autorizar_version(IN p_pv_id INT, IN p_actor_id INT, IN p_comentario VARCHAR(1000))
BEGIN
  DECLARE v_estado VARCHAR(20);
  DECLARE v_programa INT;
  DECLARE v_periodo INT;
  DECLARE v_anterior INT DEFAULT NULL;
  -- Si ya hay una transaccion abierta (la API o un script de pruebas) se usa un SAVEPOINT
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

/*------------------------------------------------ Publicacion masiva ------------------------------------------------*/
-- Publica una tarea en borrador: crea una asignacion individual por destinatario y su transicion inicial.
-- Todo o nada: si algo falla no queda ninguna asignacion.
-- alcance: rol | sede | unidad | todos (docentes activos) | curso (docentes del curso y periodo en docente_curso)
--          | seleccion (union de los criterios de tarea_seleccion) | individual (filas ya creadas por la API)
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

/*------------------------------------------------ Borrador de entrega ------------------------------------------------*/
-- Solo se guarda avance mientras la asignacion esta pendiente del docente
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

/*------------------------------------------------ Eventos para notificaciones (Grupo 6) ------------------------------------------------*/
-- Un evento no se borra ni se edita; solo se marca procesado una vez
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

-- Entregada, devuelta o aprobada: un evento por transicion
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

-- Tarea publicada o cancelada
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

-- Programa autorizado
CREATE TRIGGER trg_pv_evento AFTER UPDATE ON programa_version FOR EACH ROW
BEGIN
  IF NEW.estado_codigo = 'authorized' AND OLD.estado_codigo <> 'authorized' THEN
    INSERT INTO evento (nombre, clave_unica, programa_version_id, actor_id, payload)
    VALUES ('program.authorized', CONCAT('program.authorized:', NEW.id), NEW.id, NEW.autorizado_por,
            JSON_OBJECT('programa_curso_id', NEW.programa_curso_id, 'numero_version', NEW.numero_version,
                        'periodo_id', NEW.periodo_id));
  END IF;
END$$

-- Proximas a vencer: lo ejecuta el proceso programado del Grupo 6 (por ejemplo cada hora).
-- Crea un evento por asignacion pendiente que vence dentro de 'dias_aviso_vencimiento'.
-- Es idempotente: ejecutarlo varias veces no duplica avisos (si hay prorroga, se avisa de nuevo).
-- Uso: CALL sp_generar_eventos_vencimiento(@creados); SELECT @creados;
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
  SET p_creados = ROW_COUNT();   -- no devuelve filas: phpMyAdmin falla si un CALL devuelve resultados
END$$

/*------------------------------------------------ Auditoria de altas y cambios ------------------------------------------------*/
-- El actor se toma de la variable de sesion @actor_id, que la API fija despues de autenticar:
--   SET @actor_id = <id del usuario>;   (y @ip_origen si se desea)
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
  -- no se audita el hash de la contrasena; solo se indica si cambio
  INSERT INTO auditoria (tabla, registro_id, accion, actor_id, ip_origen, detalle)
  VALUES ('usuario', NEW.id, IF(OLD.eliminado_en IS NULL AND NEW.eliminado_en IS NOT NULL, 'soft_delete', 'update'),
          COALESCE(NEW.eliminado_por, @actor_id), @ip_origen,
          JSON_OBJECT('antes',   JSON_OBJECT('correo', OLD.correo, 'activo', OLD.activo, 'eliminado_en', OLD.eliminado_en),
                      'despues', JSON_OBJECT('correo', NEW.correo, 'activo', NEW.activo, 'eliminado_en', NEW.eliminado_en),
                      'cambio_contrasena', OLD.hash_contrasena <> NEW.hash_contrasena));
END$$

DELIMITER ;
/* =====================================================================
   03_inserts.sql | Datos semilla
   Datos base del sistema + un escenario minimo para probar inbox, panel,
   historial y version vigente. Ejecutar despues de 02_triggers.sql.
   Todos los usuarios demo tienen la contrasena: Demo2026!  (bcrypt, costo 10)
   ===================================================================== */
USE db_udv;
SET NAMES utf8mb4;

/*--------------------------------------------------- Catalogos academicos ---------------------------------------------------*/
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

/*--------------------------------------------------- Estados (CONTRATO_COMUN.md §2) ---------------------------------------------------*/
insert into estado_programa (codigo, nombre, es_final, orden) values
('draft','Borrador',0,1), ('submitted','Enviado',0,2), ('under_review','En revisión',0,3),
('returned','Devuelto',0,4), ('approved','Aprobado',0,5), ('authorized','Autorizado',0,6),
('superseded','Reemplazado',1,7);

-- Transiciones de una version de programa (ajustar al CONTRATO del G5 si cambia)
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

/*--------------------------------------------------- Seguridad: roles de la matriz del proyecto ---------------------------------------------------*/
-- Codigos en ingles, minusculas y sin espacios (acordado con el Grupo 2); nombres visibles en espanol.
-- Los 4 primeros roles y los permisos 1 a 14 son los del JSON del Grupo 2 (para_validar_grupo1).
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
-- Agregados por el Grupo 1 para cubrir la matriz de roles (confirmar con el Grupo 2)
(15, 'tasks.monitor',      'Ver panel de estados y cumplimiento'),
(16, 'comments.create',    'Comentar en asignaciones y versiones'),
(17, 'programs.read',      'Consultar programas, versiones y PDF'),
(18, 'programs.review',    'Revisar, aprobar o devolver versiones de programa'),
(19, 'programs.authorize', 'Autorizar la version vigente de un programa'),
(20, 'catalogs.manage',    'Administrar sedes, cursos, periodos y tipos de tarea'),
(21, 'parameters.manage',  'Modificar parametros del sistema');

insert into rol_permiso (rol_id, permiso_id) values
-- admin (Grupo 2) + catalogos, parametros, panel y programas
(1,1),(1,2),(1,3),(1,4),(1,5),(1,6),(1,7),(1,8),(1,9),(1,10),(1,11),(1,12),(1,13),(1,14),(1,15),(1,17),(1,20),(1,21),
-- coordinator (Grupo 2) + panel, comentarios y consulta de programas
(2,1),(2,5),(2,7),(2,8),(2,10),(2,11),(2,13),(2,14),(2,15),(2,16),(2,17),
-- teacher (Grupo 2) + comentarios y consulta de programas
(3,7),(3,8),(3,12),(3,16),(3,17),
-- reviewer (Grupo 2) + comentarios, consulta y revision de programas
(4,1),(4,8),(4,13),(4,14),(4,16),(4,17),(4,18),
-- authority
(5,8),(5,15),(5,16),(5,17),(5,19),
-- auditor
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
(1, 1, NULL), -- Administrador
(2, 2, 1),    -- Coordinador
(3, 3, 1),    -- Docente
(4, 3, 1),    -- Docente
(5, 4, 1),    -- Revisor
(5, 3, 1),    -- La revisora tambien es docente (un usuario puede tener varios roles)
(6, 5, 1),    -- Autoridad
(7, 6, 1),    -- Auditor
(8, 3, 1);    -- Docente de otra sede

-- Quien imparte que curso (para publicar tareas "a los docentes del curso")
insert into docente_curso (usuario_id, curso_id, periodo_id, sede_id, asignado_por) values
(3, 1, 2, 1, 2),   -- Diana: Programacion Web, 2026-2, Sede Central
(4, 1, 2, 1, 2),   -- Daniel: Programacion Web, 2026-2, Sede Central
(8, 1, 2, 2, 2),   -- Maria: Programacion Web, 2026-2, Sede Regional
(5, 3, 2, 1, 2),   -- Rosa: Bases de Datos I, 2026-2
(3, 4, 1, 1, 2);   -- Diana: Programacion I, 2026-1

insert into parametro (codigo, valor, descripcion, actualizado_por) values
('zona_horaria',            'America/Guatemala', 'Zona horaria institucional para mostrar fechas (en BD se guardan en UTC)', 1),
('dias_aviso_vencimiento',  '3',                 'Dias antes del vencimiento en que se envia aviso', 1),
('paginacion_max_por_pagina','100',              'Maximo de per_page en la API', 1),
('archivo_tamano_max_mb',   '20',                'Tamano maximo global de un archivo', 1);

/*--------------------------------------------------- Tipos iniciales de tarea ---------------------------------------------------*/
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

/*--------------------------------------------------- Workflow por tipo de tarea ---------------------------------------------------*/
-- Transiciones por defecto; las validas las define el CONTRATO del G3. Si cambian, se ajusta solo esta seccion.
insert into workflow (id, nombre, tipo_tarea_id)
select id, concat('Flujo estandar - ', nombre), id from tipo_tarea;

insert into workflow_detalle (workflow_id, estado_origen, estado_destino, accion)
select w.id, t.origen, t.destino, t.accion
from workflow w
cross join (
  select NULL as origen, 'assigned' as destino, 'publish' as accion  -- publicacion: se crea la asignacion
  union all select 'assigned',     'in_progress',  'start'           -- docente abre e inicia
  union all select 'in_progress',  'submitted',    'submit'          -- docente entrega
  union all select 'submitted',    'under_review', 'review'          -- revisor toma la entrega
  union all select 'under_review', 'returned',     'return'          -- revisor devuelve (exige observacion)
  union all select 'returned',     'in_progress',  'resubmit'        -- docente atiende la devolucion
  union all select 'under_review', 'approved',     'approve'         -- revisor aprueba
  union all select 'approved',     'closed',       'close'           -- coordinacion cierra
  union all select 'assigned',     'cancelled',    'cancel'
  union all select 'in_progress',  'cancelled',    'cancel'
) t;

-- Roles que pueden ejecutar cada accion
insert into workflow_detalle_rol (workflow_detalle_id, rol_id)
select wd.id, r.id
from workflow_detalle wd
join rol r on r.codigo = case
    when wd.accion in ('publish', 'close', 'cancel')           then 'coordinator'
    when wd.accion in ('start', 'submit', 'resubmit')          then 'teacher'
    when wd.accion in ('review', 'return', 'approve')          then 'reviewer'
  end;
-- La autoridad tambien puede cancelar
insert into workflow_detalle_rol (workflow_detalle_id, rol_id)
select wd.id, (select id from rol where codigo = 'authority') from workflow_detalle wd where wd.accion = 'cancel';

/*--------------------------------------------------- Programa de curso de ejemplo ---------------------------------------------------*/
insert into programa_curso (id, curso_id, sede_id, modalidad_id, creado_por) values
(1, 1, 1, 1, 2);

-- Version 1 (se autoriza abajo)
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

-- Flujo de aprobacion de la version 1
update programa_version set estado_codigo = 'submitted'    where id = 1;
insert into programa_aprobacion (programa_version_id, actor_id, estado_anterior, estado_nuevo, comentario) values (1, 3, 'draft', 'submitted', 'Envío a revisión');
update programa_version set estado_codigo = 'under_review' where id = 1;
insert into programa_aprobacion (programa_version_id, actor_id, estado_anterior, estado_nuevo, comentario) values (1, 5, 'submitted', 'under_review', NULL);
update programa_version set estado_codigo = 'approved'     where id = 1;
insert into programa_aprobacion (programa_version_id, actor_id, estado_anterior, estado_nuevo, comentario) values (1, 5, 'under_review', 'approved', 'Cumple con el formato institucional');
call sp_autorizar_version(1, 6, 'Se autoriza como versión vigente');

-- PDF oficial de la version 1 (se registra una sola vez)
insert into archivo (id, nombre_original, nombre_interno, tipo_mime, tamano_bytes, hash_sha256, ubicacion, autor_id, programa_version_id) values
(1, 'Programa_ISW-301_2026-1.pdf', 'pv1-7f3a2c.pdf', 'application/pdf', 184320,
 'a3f1c2d4e5b6978877665544332211aabbccddeeff00112233445566778899aa', 'programas/2026-1/pv1-7f3a2c.pdf', 6, 1);
update programa_version set pdf_archivo_id = 1, pdf_hash = 'a3f1c2d4e5b6978877665544332211aabbccddeeff00112233445566778899aa',
       pdf_generado_en = CURRENT_TIMESTAMP(3) where id = 1;
insert into programa_pdf (programa_version_id, archivo_id, aprobacion_id, hash_contenido, generado_por)
select 1, 1, max(id), 'a3f1c2d4e5b6978877665544332211aabbccddeeff00112233445566778899aa', 6
from programa_aprobacion where programa_version_id = 1 and estado_nuevo = 'authorized';

-- Version 2: borrador clonado de la version 1 (coexiste sin sobrescribirla)
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

/*--------------------------------------------------- Escenario minimo de tareas ---------------------------------------------------*/
-- Tarea 1: publicada a los docentes de la unidad 1 para actualizar el programa
insert into tarea (id, workflow_id, estado_codigo, creado_por, curso_id, periodo_id, programa_version_id,
                   titulo, descripcion, prioridad, alcance, unidad_destino_id, revisor_id, fecha_limite, publicada_en) values
(1, 1, 'assigned', 2, 1, 1, 2, 'Actualizar programa de Programación Web',
 'Revise y actualice la bibliografía y las evaluaciones del programa vigente.', 'high', 'unidad', 1, 5,
 '2026-12-15 23:59:59', '2026-10-01 08:00:00');

-- Tarea 2: CV con plazo ya vencido
insert into tarea (id, workflow_id, estado_codigo, creado_por, titulo, descripcion, alcance,
                   rol_destino_id, revisor_id, fecha_limite, publicada_en) values
(2, 2, 'assigned', 2, 'Actualizar CV docente 2026',
 'Suba su CV actualizado en PDF e indique la fecha de vigencia.', 'rol', 3, 5,
 '2026-09-30 23:59:59', '2026-09-01 08:00:00');

-- Tarea 3: borrador (no debe aparecer en ningun inbox)
insert into tarea (id, workflow_id, estado_codigo, creado_por, titulo, alcance, rol_destino_id) values
(3, 4, 'draft', 2, 'Confirmar asistencia a capacitación', 'rol', 3);

insert into tarea_destinatario (id, tarea_id, usuario_id, estado_codigo, asignado_en) values
(1, 1, 3, 'assigned', '2026-10-01 08:00:00'),   -- de esta asignacion salio la version 2
(2, 1, 4, 'assigned', '2026-10-01 08:00:00'),
(3, 2, 3, 'assigned', '2026-09-01 08:00:00'),
(4, 2, 4, 'assigned', '2026-09-01 08:00:00');

-- Procedimiento auxiliar SOLO para cargar el historial de ejemplo (se elimina al final)
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

-- Registro inicial de las 4 asignaciones (NULL -> assigned)
insert into tarea_transicion (tarea_destinatario_id, workflow_detalle_id, actor_id, estado_anterior, estado_nuevo, comentario)
select td.id, wd.id, 2, NULL, 'assigned', 'Publicación de la tarea'
from tarea_destinatario td join tarea t on t.id = td.tarea_id
join workflow_detalle wd on wd.workflow_id = t.workflow_id and wd.estado_origen is null and wd.estado_destino = 'assigned';

-- Docente 1 trabaja el programa, se le devuelve y lo vuelve a entregar
call sp_seed_transicion(1, 'in_progress', 3, NULL);
insert into entrega (id, tarea_destinatario_id, numero_intento, entregado_por, contenido_texto, programa_version_id) values
(1, 1, 1, 3, 'Se actualizó la bibliografía (versión 2 del programa).', 2);
call sp_seed_transicion(1, 'submitted', 3, 'Primera entrega');
call sp_seed_transicion(1, 'under_review', 5, NULL);
call sp_seed_transicion(1, 'returned', 5, 'Agregue al menos una referencia publicada en los últimos 5 años.');
insert into comentario (autor_id, tarea_destinatario_id, contenido) values
(5, 1, 'Agregue al menos una referencia publicada en los últimos 5 años.');
call sp_seed_transicion(1, 'in_progress', 3, NULL);
insert into comentario (autor_id, tarea_destinatario_id, comentario_padre_id, contenido) values
(3, 1, 1, 'Listo, agregué la referencia de 2023.');
insert into entrega (id, tarea_destinatario_id, numero_intento, entregado_por, contenido_texto, programa_version_id) values
(2, 1, 2, 3, 'Bibliografía actualizada con referencia reciente.', 2);
call sp_seed_transicion(1, 'submitted', 3, 'Segunda entrega');

-- Docente 1 entrega su CV con archivo y fecha de vigencia
call sp_seed_transicion(3, 'in_progress', 3, NULL);
insert into entrega (id, tarea_destinatario_id, numero_intento, entregado_por) values (3, 3, 1, 3);
insert into entrega_valor (entrega_id, campo_id, valor)
select 3, id, '2027-12-31' from tipo_tarea_campo where tipo_tarea_id = 2 and codigo = 'vigencia_hasta';
insert into archivo (id, nombre_original, nombre_interno, tipo_mime, tamano_bytes, hash_sha256, ubicacion, autor_id, entrega_id) values
(2, 'CV Diana Pérez.pdf', 'e3-91bd0f.pdf', 'application/pdf', 96256,
 'b4e2d3c4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2', 'entregas/2026/e3-91bd0f.pdf', 3, 3);
call sp_seed_transicion(3, 'submitted', 3, NULL);

DROP PROCEDURE sp_seed_transicion;

-- La version 2 es el trabajo de la asignacion 1 (Diana) y se entrego con la segunda entrega
update programa_version set tarea_destinatario_origen_id = 1 where id = 2;

-- Daniel guardo avance sin enviar en la tarea del programa
insert into entrega_borrador (tarea_destinatario_id, contenido_texto, guardado_por) values
(2, 'Borrador: revisar unidades 3 y 4.', 4);

-- Prorroga individual: Daniel tiene hasta el 15/10/2026 para el CV
update tarea_destinatario set fecha_limite = '2026-10-15 23:59:59' where id = 4;

-- Notificaciones (las de entregas y devoluciones vienen de los eventos que generaron los triggers)
insert into notificacion (usuario_id, tipo, titulo, mensaje, tarea_destinatario_id, evento_id)
select 3, 'assignment.returned', 'Tarea devuelta', 'Su entrega de "Actualizar programa de Programación Web" fue devuelta con observaciones.', 1, id
from evento where nombre = 'assignment.returned' and tarea_destinatario_id = 1;
insert into notificacion (usuario_id, tipo, titulo, mensaje, tarea_destinatario_id) values
(4, 'assignment.due_soon', 'Tarea vencida', 'La tarea "Actualizar CV docente 2026" venció el 30/09/2026.', 4),
(5, 'assignment.submitted', 'Nueva entrega', 'Diana Pérez entregó "Actualizar programa de Programación Web".', 1);
-- El evento de la devolucion ya se notifico
update evento set procesado_en = CURRENT_TIMESTAMP(3) where nombre = 'assignment.returned' and tarea_destinatario_id = 1;
/* =====================================================================
   04_vistas.sql | Vistas que consumen la API y las pantallas
   Ejecutar despues de 03_inserts.sql.
   ===================================================================== */
USE db_udv;
SET NAMES utf8mb4;

-- Inbox del docente: solo tareas publicadas (las draft nunca aparecen) y no eliminadas.
-- Uso: SELECT * FROM v_inbox WHERE usuario_id = ? [AND estado_codigo = ?] ORDER BY fecha_limite;
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
    COALESCE(td.fecha_limite, t.fecha_limite) AS fecha_limite,   -- incluye prorroga individual
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
WHERE t.estado_codigo <> 'draft'
  AND t.eliminado_en IS NULL;

-- Panel de cumplimiento por tarea (coordinador / autoridad / auditor)
CREATE OR REPLACE VIEW v_panel_tarea AS
SELECT
    t.id            AS tarea_id,
    t.titulo,
    tt.nombre       AS tipo_nombre,
    t.estado_codigo AS estado_tarea,
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
    -- proxima a vencer: pendiente y vence dentro de los dias del parametro 'dias_aviso_vencimiento'
    SUM(COALESCE(td.fecha_limite, t.fecha_limite) >= NOW(3)
        AND COALESCE(td.fecha_limite, t.fecha_limite) < NOW(3) + INTERVAL (SELECT CAST(valor AS UNSIGNED) FROM parametro WHERE codigo = 'dias_aviso_vencimiento') DAY
        AND td.estado_codigo IN ('assigned', 'in_progress', 'returned')) AS proximas_a_vencer,
    ROUND(100 * SUM(td.estado_codigo IN ('submitted', 'under_review', 'approved', 'closed'))
          / NULLIF(SUM(td.estado_codigo <> 'cancelled'), 0), 1)       AS porcentaje_cumplimiento
FROM tarea t
JOIN workflow w ON w.id = t.workflow_id
JOIN tipo_tarea tt ON tt.id = w.tipo_tarea_id
LEFT JOIN tarea_destinatario td ON td.tarea_id = t.id
WHERE t.eliminado_en IS NULL
GROUP BY t.id, t.titulo, tt.nombre, t.estado_codigo, t.creado_por, t.revisor_id, t.fecha_limite;

-- Historial completo de una tarea (todas sus asignaciones), en orden
-- Uso: SELECT * FROM v_historial_tarea WHERE tarea_id = ? ORDER BY creado_en, transicion_id;
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
    tr.creado_en
FROM tarea_transicion tr
JOIN tarea_destinatario td ON td.id = tr.tarea_destinatario_id
JOIN usuario d ON d.id = td.usuario_id
JOIN usuario a ON a.id = tr.actor_id;

-- Version vigente (autorizada) de cada programa por periodo
CREATE OR REPLACE VIEW v_programa_vigente AS
SELECT
    pc.id               AS programa_curso_id,
    c.codigo            AS curso_codigo,
    c.nombre            AS curso_nombre,
    s.nombre            AS sede,
    m.nombre            AS modalidad,
    a.nombre            AS area,
    pv.nivel,
    pv.programa_academico,
    pv.horas_clase_semanal,
    p.codigo            AS periodo,
    pv.id               AS programa_version_id,
    pv.numero_version,
    pv.nombre           AS version_nombre,
    pv.autorizado_en,
    CONCAT(u.nombres, ' ', u.apellidos) AS autorizado_por,
    pv.pdf_archivo_id,
    pv.pdf_hash,
    pv.pdf_generado_en
FROM programa_version pv
JOIN programa_curso pc ON pc.id = pv.programa_curso_id
JOIN curso   c ON c.id = pc.curso_id
JOIN sede    s ON s.id = pc.sede_id
JOIN modalidad m ON m.id = pc.modalidad_id
JOIN periodo p ON p.id = pv.periodo_id
LEFT JOIN area a ON a.id = pv.area_id
LEFT JOIN usuario u ON u.id = pv.autorizado_por
WHERE pv.estado_codigo = 'authorized';

-- Todas las versiones de un programa con su total de evaluaciones (consulta de versiones anteriores, RF18)
CREATE OR REPLACE VIEW v_programa_versiones AS
SELECT
    pv.programa_curso_id,
    pv.id               AS programa_version_id,
    pv.numero_version,
    pv.nombre,
    p.codigo            AS periodo,
    pv.estado_codigo,
    pv.version_origen_id,
    pv.resumen_cambios,
    pv.creado_en,
    pv.autorizado_en,
    (SELECT IFNULL(SUM(e.ponderacion), 0) FROM programa_evaluacion e
      WHERE e.programa_version_id = pv.id) AS total_evaluaciones
FROM programa_version pv
JOIN periodo p ON p.id = pv.periodo_id;

-- Historial de aprobacion de una version de programa
CREATE OR REPLACE VIEW v_historial_programa AS
SELECT
    pa.id               AS aprobacion_id,
    pa.programa_version_id,
    pv.programa_curso_id,
    pv.numero_version,
    pa.estado_anterior,
    pa.estado_nuevo,
    CONCAT(u.nombres, ' ', u.apellidos) AS actor,
    pa.comentario,
    pa.creado_en
FROM programa_aprobacion pa
JOIN programa_version pv ON pv.id = pa.programa_version_id
JOIN usuario u ON u.id = pa.actor_id;

-- Eventos pendientes de notificar (los consume el proceso del Grupo 6 en orden)
CREATE OR REPLACE VIEW v_evento_pendiente AS
SELECT id AS evento_id, nombre, tarea_id, tarea_destinatario_id, programa_version_id, actor_id, payload, creado_en
FROM evento
WHERE procesado_en IS NULL;
