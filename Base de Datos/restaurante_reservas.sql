DROP DATABASE IF EXISTS restaurante_reservas;
CREATE DATABASE restaurante_reservas
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_spanish_ci;

USE restaurante_reservas;


-- 1. TABLAS CATÁLOGO Y CONTROL DE ACCESO (evitan texto libre inconsistente)

-- Roles del sistema (Módulo 1: Autenticación y usuarios)
CREATE TABLE roles (
    id_rol INT AUTO_INCREMENT PRIMARY KEY,
    nombre_rol VARCHAR(30) NOT NULL UNIQUE
);

-- Catálogo de permisos individuales del sistema
CREATE TABLE permisos (
    id_permiso INT AUTO_INCREMENT PRIMARY KEY,
    codigo_permiso VARCHAR(50) NOT NULL UNIQUE,  -- Ej: 'VER_REPORTES', 'GESTIONAR_RESERVAS'
    descripcion VARCHAR(150) NOT NULL
);

-- Tabla intermedia para asociar permisos a roles (RBAC)
CREATE TABLE permisos_rol (
    id_rol INT NOT NULL,
    id_permiso INT NOT NULL,
    PRIMARY KEY (id_rol, id_permiso),
    FOREIGN KEY (id_rol) REFERENCES roles(id_rol) ON DELETE CASCADE,
    FOREIGN KEY (id_permiso) REFERENCES permisos(id_permiso) ON DELETE CASCADE
);

-- Ubicaciones/zonas del restaurante (Módulo 3: Mesas)
CREATE TABLE ubicaciones (
    id_ubicacion INT AUTO_INCREMENT PRIMARY KEY,
    nombre_ubicacion VARCHAR(50) NOT NULL UNIQUE
);

-- Estados posibles de una mesa (Módulo 3 y 5: Mapa visual)
CREATE TABLE estados_mesa (
    id_estado_mesa INT AUTO_INCREMENT PRIMARY KEY,
    nombre_estado VARCHAR(20) NOT NULL UNIQUE
);

-- Estados posibles de una reserva (Módulo 4 y 6: Reportes)
CREATE TABLE estados_reserva (
    id_estado_reserva INT AUTO_INCREMENT PRIMARY KEY,
    nombre_estado VARCHAR(20) NOT NULL UNIQUE
);

-- 2. TABLAS PRINCIPALES

-- Módulo 1: Autenticación y usuarios
CREATE TABLE usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre_completo VARCHAR(100) NOT NULL,
    nombre_usuario VARCHAR(50) NOT NULL UNIQUE,
    contrasena_hash VARCHAR(255) NOT NULL,
    id_rol INT NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_rol) REFERENCES roles(id_rol)
);

-- Módulo 2: Clientes
-- Validaciones de negocio: telefono de al menos 8 caracteres y correo opcional
-- con formato valido (equivalente a la validacion que hace la app).
CREATE TABLE clientes (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    nombre_completo VARCHAR(100) NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    correo VARCHAR(100),
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_cliente_telefono CHECK (CHAR_LENGTH(telefono) >= 8),
    CONSTRAINT chk_cliente_correo CHECK (
        correo IS NULL
        OR correo REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'
    )
);

-- Módulo 3: Mesas
CREATE TABLE mesas (
    id_mesa INT AUTO_INCREMENT PRIMARY KEY,
    numero_mesa VARCHAR(10) NOT NULL UNIQUE,
    capacidad INT NOT NULL,
    id_ubicacion INT NOT NULL,
    id_estado_mesa INT NOT NULL,
    FOREIGN KEY (id_ubicacion) REFERENCES ubicaciones(id_ubicacion),
    FOREIGN KEY (id_estado_mesa) REFERENCES estados_mesa(id_estado_mesa)
);

-- Módulo 4: Reservas (tabla puente entre clientes y mesas)
CREATE TABLE reservas (
    id_reserva INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL,
    id_mesa INT NOT NULL,
    id_usuario INT NOT NULL,          -- quién gestionó/creó la reserva
    id_estado_reserva INT NOT NULL,
    fecha_reserva DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    numero_personas INT NOT NULL,
    observaciones VARCHAR(255),
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
    FOREIGN KEY (id_mesa) REFERENCES mesas(id_mesa),
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
    FOREIGN KEY (id_estado_reserva) REFERENCES estados_reserva(id_estado_reserva),
    CONSTRAINT chk_reserva_horas CHECK (hora_fin > hora_inicio),
    CONSTRAINT chk_reserva_personas CHECK (numero_personas >= 1)
);

-- Módulo 7: Configuración general (horario de atención)
CREATE TABLE horarios_atencion (
    id_horario INT AUTO_INCREMENT PRIMARY KEY,
    dia_semana ENUM('Lunes','Martes','Miercoles','Jueves','Viernes','Sabado','Domingo') NOT NULL UNIQUE,
    hora_apertura TIME NOT NULL,
    hora_cierre TIME NOT NULL,
    cerrado BOOLEAN NOT NULL DEFAULT FALSE
);

-- Módulo 7: Días festivos / no laborables
CREATE TABLE dias_festivos (
    id_dia_festivo INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE NOT NULL UNIQUE,
    descripcion VARCHAR(100),
    accion ENUM('Cerrado','Horario Especial') NOT NULL DEFAULT 'Cerrado'  -- ¿el restaurante abre o cierra ese día?
);

-- Módulo 7: Configuración general (parámetros clave-valor, ej. duración estándar de reserva)
CREATE TABLE configuracion_general (
    id_config INT AUTO_INCREMENT PRIMARY KEY,
    clave VARCHAR(50) NOT NULL UNIQUE,
    valor VARCHAR(100) NOT NULL,
    descripcion VARCHAR(150)
);

-- Historial/auditoría de reservas (trazabilidad de cambios)
CREATE TABLE historial_reservas (
    id_historial INT AUTO_INCREMENT PRIMARY KEY,
    id_reserva INT NOT NULL,
    id_usuario INT NOT NULL,
    accion VARCHAR(20) NOT NULL,     -- CREADA, MODIFICADA, CANCELADA
    fecha_accion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    detalle VARCHAR(255),
    FOREIGN KEY (id_reserva) REFERENCES reservas(id_reserva) ON DELETE CASCADE,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);


-- 3. DATOS INICIALES (catálogos, roles, permisos y configuración base)


INSERT INTO roles (nombre_rol) VALUES ('Administrador'), ('Recepcionista');

-- Insertar catálogo de permisos
INSERT INTO permisos (codigo_permiso, descripcion) VALUES
    ('GESTIONAR_RESERVAS', 'Permite crear, editar y cancelar reservas'),
    ('VER_MAPA_MESAS', 'Permite visualización en tiempo real del mapa de ocupación'),
    ('VER_REPORTES', 'Permite consultar y exportar métricas y reportes'),
    ('GESTIONAR_USUARIOS', 'Permite crear y modificar usuarios del sistema'),
    ('GESTIONAR_CONFIGURACION', 'Permite modificar horarios y parámetros del sistema');

-- Asignación de permisos por rol:
-- Recepcionista (id_rol = 2): Gestión de reservas y mapa de mesas
INSERT INTO permisos_rol (id_rol, id_permiso) VALUES
    (2, 1), -- GESTIONAR_RESERVAS
    (2, 2); -- VER_MAPA_MESAS

-- Administrador (id_rol = 1): Acceso total
INSERT INTO permisos_rol (id_rol, id_permiso) VALUES
    (1, 1), (1, 2), (1, 3), (1, 4), (1, 5);

INSERT INTO ubicaciones (nombre_ubicacion) VALUES ('Salon Principal'), ('Terraza'), ('Area VIP');

INSERT INTO estados_mesa (nombre_estado) VALUES ('Libre'), ('Ocupada'), ('Reservada'), ('Mantenimiento');

INSERT INTO estados_reserva (nombre_estado) VALUES
    ('Pendiente'), ('Confirmada'), ('Cancelada'), ('Completada');

INSERT INTO horarios_atencion (dia_semana, hora_apertura, hora_cierre, cerrado) VALUES
    ('Lunes', '12:00:00', '22:00:00', FALSE),
    ('Martes', '12:00:00', '22:00:00', FALSE),
    ('Miercoles', '12:00:00', '22:00:00', FALSE),
    ('Jueves', '12:00:00', '22:00:00', FALSE),
    ('Viernes', '12:00:00', '23:00:00', FALSE),
    ('Sabado', '12:00:00', '23:00:00', FALSE),
    ('Domingo', '12:00:00', '20:00:00', FALSE);

INSERT INTO dias_festivos (fecha, descripcion, accion) VALUES
    ('2026-01-01', 'Año Nuevo', 'Cerrado'),
    ('2026-04-14', 'Semana Santa', 'Cerrado'),
    ('2026-05-01', 'Dia del Trabajo', 'Cerrado'),
    ('2026-06-14', 'Dia del Padre', 'Horario Especial'),
    ('2026-09-10', 'Dia de la Independencia', 'Cerrado'),
    ('2026-12-25', 'Navidad', 'Cerrado');

INSERT INTO configuracion_general (clave, valor, descripcion) VALUES
    ('duracion_estandar_reserva_min', '90', 'Duración estándar de una reserva en minutos'),
    ('tiempo_tolerancia_min', '15', 'Minutos de tolerancia para la llegada del cliente'),
    ('max_personas_por_reserva', '20', 'Máximo de personas permitido por reserva'),
    ('notif_email_confirmacion', '1', 'Enviar confirmación de reserva por correo'),
    ('notif_recordatorio', '0', 'Enviar recordatorio 1 hora antes de la reserva');

-- Datos de ejemplo para pruebas
INSERT INTO usuarios (nombre_completo, nombre_usuario, contrasena_hash, id_rol) VALUES
    ('Admin General', 'admin', SHA2('admin123', 256), 1),
    ('Recepcionista Uno', 'recepcion1', SHA2('recepcion123', 256), 2);

-- Mesas por zona: Salon Principal (1), Terraza (2), Area VIP (3).
-- Corresponde al mapa visual de la interfaz beta (mesas.py)
INSERT INTO mesas (numero_mesa, capacidad, id_ubicacion, id_estado_mesa) VALUES
    -- Salon Principal
    ('M1', 2, 1, 1),
    ('M2', 4, 1, 1),
    ('M3', 4, 1, 1),
    ('M4', 6, 1, 1),
    ('M5', 2, 1, 1),
    ('M6', 4, 1, 1),
    ('M7', 4, 1, 1),
    ('M8', 6, 1, 1),
    -- Terraza
    ('T1', 2, 2, 1),
    ('T2', 4, 2, 1),
    ('T3', 4, 2, 1),
    ('T4', 2, 2, 1),
    -- Area VIP
    ('V1', 4, 3, 1),
    ('V2', 8, 3, 1),
    ('V3', 4, 3, 1),
    ('V4', 10, 3, 1);

INSERT INTO clientes (nombre_completo, telefono, correo) VALUES
    ('Juan Pérez', '88887777', 'juan.perez@email.com'),
    ('María López', '77778888', 'maria.lopez@email.com');


-- 4. TRIGGER: evitar doble reserva (traslape de horario en la misma mesa)


DELIMITER $$

CREATE TRIGGER trg_validar_disponibilidad_insert
BEFORE INSERT ON reservas
FOR EACH ROW
BEGIN
    DECLARE conflictos INT;

    SELECT COUNT(*) INTO conflictos
    FROM reservas
    WHERE id_mesa = NEW.id_mesa
      AND fecha_reserva = NEW.fecha_reserva
      AND id_estado_reserva IN (
            SELECT id_estado_reserva FROM estados_reserva
            WHERE nombre_estado IN ('Pendiente','Confirmada')
      )
      AND (NEW.hora_inicio < hora_fin AND NEW.hora_fin > hora_inicio);

    IF conflictos > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Conflicto: la mesa ya tiene una reserva activa que se traslapa con ese horario.';
    END IF;
END$$

CREATE TRIGGER trg_validar_disponibilidad_update
BEFORE UPDATE ON reservas
FOR EACH ROW
BEGIN
    DECLARE conflictos INT;

    SELECT COUNT(*) INTO conflictos
    FROM reservas
    WHERE id_mesa = NEW.id_mesa
      AND fecha_reserva = NEW.fecha_reserva
      AND id_reserva <> NEW.id_reserva
      AND id_estado_reserva IN (
            SELECT id_estado_reserva FROM estados_reserva
            WHERE nombre_estado IN ('Pendiente','Confirmada')
      )
      AND (NEW.hora_inicio < hora_fin AND NEW.hora_fin > hora_inicio);

    IF conflictos > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Conflicto: la mesa ya tiene una reserva activa que se traslapa con ese horario.';
    END IF;
END$$

-- Validacion de aforo, estado de la mesa y fecha (BEFORE INSERT)
-- Replica en la BD: (a) la mesa no puede estar en mantenimiento,
-- (b) el numero de personas no puede exceder la capacidad de la mesa,
-- (c) no se permiten reservas con fecha pasada.
CREATE TRIGGER trg_validar_mesa_reserva_insert
BEFORE INSERT ON reservas
FOR EACH ROW
BEGIN
    DECLARE v_capacidad INT DEFAULT 0;
    DECLARE v_estado VARCHAR(20) DEFAULT '';

    SELECT m.capacidad, em.nombre_estado
    INTO v_capacidad, v_estado
    FROM mesas m
    JOIN estados_mesa em ON m.id_estado_mesa = em.id_estado_mesa
    WHERE m.id_mesa = NEW.id_mesa;

    IF v_estado = 'Mantenimiento' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'La mesa esta en mantenimiento y no puede asignarse a una reserva.';
    END IF;

    IF NEW.numero_personas > v_capacidad THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'El numero de personas excede la capacidad de la mesa asignada.';
    END IF;

    IF NEW.fecha_reserva < CURDATE() THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'No se permite registrar una reserva con fecha pasada.';
    END IF;
END$$

CREATE TRIGGER trg_validar_mesa_reserva_update
BEFORE UPDATE ON reservas
FOR EACH ROW
BEGIN
    DECLARE v_capacidad INT DEFAULT 0;
    DECLARE v_estado VARCHAR(20) DEFAULT '';

    SELECT m.capacidad, em.nombre_estado
    INTO v_capacidad, v_estado
    FROM mesas m
    JOIN estados_mesa em ON m.id_estado_mesa = em.id_estado_mesa
    WHERE m.id_mesa = NEW.id_mesa;

    IF v_estado = 'Mantenimiento' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'La mesa esta en mantenimiento y no puede asignarse a una reserva.';
    END IF;

    IF NEW.numero_personas > v_capacidad THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'El numero de personas excede la capacidad de la mesa asignada.';
    END IF;

    IF NEW.fecha_reserva < CURDATE() THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'No se permite registrar una reserva con fecha pasada.';
    END IF;
END$$


-- 5. TRIGGERS: registrar automáticamente en el historial de auditoría

CREATE TRIGGER trg_historial_insert
AFTER INSERT ON reservas
FOR EACH ROW
BEGIN
    INSERT INTO historial_reservas (id_reserva, id_usuario, accion, detalle)
    VALUES (NEW.id_reserva, NEW.id_usuario, 'CREADA',
            CONCAT('Reserva creada para mesa ', NEW.id_mesa, ' el ', NEW.fecha_reserva));
END$$

CREATE TRIGGER trg_historial_update
AFTER UPDATE ON reservas
FOR EACH ROW
BEGIN
    INSERT INTO historial_reservas (id_reserva, id_usuario, accion, detalle)
    VALUES (NEW.id_reserva, NEW.id_usuario, 'MODIFICADA',
            CONCAT('Reserva actualizada. Estado actual: ', NEW.id_estado_reserva));
END$$

DELIMITER ;


-- 6. VISTAS ÚTILES PARA LA APLICACIÓN (PySide6) Y REPORTES

-- Vista útil para PySide6: Permite consultar rápidamente qué permisos tiene un usuario tras hacer Login
CREATE VIEW vista_permisos_usuario AS
SELECT 
    u.id_usuario,
    u.nombre_usuario,
    r.nombre_rol,
    p.codigo_permiso,
    p.descripcion AS descripcion_permiso
FROM usuarios u
JOIN roles r ON u.id_rol = r.id_rol
JOIN permisos_rol pr ON r.id_rol = pr.id_rol
JOIN permisos p ON pr.id_permiso = p.id_permiso;

-- Vista: estado actual de ocupación por mesa (para el mapa visual - Módulo 5)
CREATE VIEW vista_mapa_ocupacion AS
SELECT
    m.id_mesa,
    m.numero_mesa,
    m.capacidad,
    u.nombre_ubicacion,
    em.nombre_estado AS estado_mesa
FROM mesas m
JOIN ubicaciones u ON m.id_ubicacion = u.id_ubicacion
JOIN estados_mesa em ON m.id_estado_mesa = em.id_estado_mesa;

-- Vista: reservas del día con datos de cliente y mesa (uso diario de recepción)
CREATE VIEW vista_reservas_detalle AS
SELECT
    r.id_reserva,
    c.nombre_completo AS cliente,
    c.telefono,
    m.numero_mesa,
    r.fecha_reserva,
    r.hora_inicio,
    r.hora_fin,
    r.numero_personas,
    er.nombre_estado AS estado_reserva,
    us.nombre_completo AS gestionada_por
FROM reservas r
JOIN clientes c ON r.id_cliente = c.id_cliente
JOIN mesas m ON r.id_mesa = m.id_mesa
JOIN estados_reserva er ON r.id_estado_reserva = er.id_estado_reserva
JOIN usuarios us ON r.id_usuario = us.id_usuario;

-- Vista: reporte de mesas más solicitadas (Módulo 6: Reportes)
CREATE VIEW vista_mesas_mas_solicitadas AS
SELECT
    m.numero_mesa,
    COUNT(r.id_reserva) AS total_reservas
FROM mesas m
LEFT JOIN reservas r ON m.id_mesa = r.id_mesa
GROUP BY m.numero_mesa
ORDER BY total_reservas DESC;

-- Vista: tasa de cancelación general (Módulo 6: Reportes)
CREATE VIEW vista_tasa_cancelacion AS
SELECT
    COUNT(*) AS total_reservas,
    SUM(CASE WHEN er.nombre_estado = 'Cancelada' THEN 1 ELSE 0 END) AS canceladas,
    ROUND(
        SUM(CASE WHEN er.nombre_estado = 'Cancelada' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
    ) AS porcentaje_cancelacion
FROM reservas r
JOIN estados_reserva er ON r.id_estado_reserva = er.id_estado_reserva;

-- Vista: reservas por dia de la semana (Módulo 6: Reportes - tabla "Reservas por Dia")
CREATE VIEW vista_reservas_por_dia AS
SELECT
    CASE DAYOFWEEK(fecha_reserva)
        WHEN 1 THEN 'Domingo'
        WHEN 2 THEN 'Lunes'
        WHEN 3 THEN 'Martes'
        WHEN 4 THEN 'Miercoles'
        WHEN 5 THEN 'Jueves'
        WHEN 6 THEN 'Viernes'
        WHEN 7 THEN 'Sabado'
    END AS dia_semana,
    COUNT(*) AS total_reservas
FROM reservas
GROUP BY dia_semana
ORDER BY MIN(DAYOFWEEK(fecha_reserva));

-- Vista: horario con mayor cantidad de reservas (Módulo 6: Reportes - KPI "Horario Pico")
CREATE VIEW vista_horario_pico AS
SELECT
    hora_inicio AS horario_pico,
    COUNT(*) AS total_reservas
FROM reservas
GROUP BY hora_inicio
ORDER BY total_reservas DESC
LIMIT 1;

-- Vista: porcentaje de ocupacion actual de las mesas (Módulo 6: Reportes - KPI "Ocupacion Promedio")
CREATE VIEW vista_ocupacion_promedio AS
SELECT
    COUNT(*) AS total_mesas,
    SUM(CASE WHEN em.nombre_estado = 'Ocupada' THEN 1 ELSE 0 END) AS mesas_ocupadas,
    ROUND(
        SUM(CASE WHEN em.nombre_estado = 'Ocupada' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
    ) AS porcentaje_ocupacion
FROM mesas m
JOIN estados_mesa em ON m.id_estado_mesa = em.id_estado_mesa;

-- Vista: clientes con mas reservas (Módulo 6: Reportes - KPI "Clientes Frecuentes")
CREATE VIEW vista_clientes_frecuentes AS
SELECT
    c.id_cliente,
    c.nombre_completo AS cliente,
    c.telefono,
    COUNT(r.id_reserva) AS total_reservas
FROM clientes c
LEFT JOIN reservas r ON c.id_cliente = r.id_cliente
GROUP BY c.id_cliente, c.nombre_completo, c.telefono
ORDER BY total_reservas DESC;


-- 7. PROCEDIMIENTOS ALMACENADOS


DELIMITER $$

-- Verifica si una mesa está disponible en un rango de fecha/hora dado
-- Uso desde PySide6: CALL sp_verificar_disponibilidad(3, '2026-09-01', '19:00:00', '20:30:00');
CREATE PROCEDURE sp_verificar_disponibilidad(
    IN p_id_mesa INT,
    IN p_fecha DATE,
    IN p_hora_inicio TIME,
    IN p_hora_fin TIME
)
BEGIN
    SELECT COUNT(*) AS conflictos
    FROM reservas
    WHERE id_mesa = p_id_mesa
      AND fecha_reserva = p_fecha
      AND id_estado_reserva IN (
            SELECT id_estado_reserva FROM estados_reserva
            WHERE nombre_estado IN ('Pendiente','Confirmada')
      )
      AND (p_hora_inicio < hora_fin AND p_hora_fin > hora_inicio);
END$$

-- Mesas disponibles (aforo) para una fecha/horario dado y numero de personas.
-- Replica en la BD la logica 'mesas_disponibles'/'local_lleno' de la app:
-- devuelve las mesas libres, con capacidad suficiente y que NO esten en
-- mantenimiento. Si no devuelve filas, el local esta lleno.
-- Uso desde PySide6: CALL sp_mesas_disponibles('2026-09-01', '19:00:00', '20:30:00', 4);
CREATE PROCEDURE sp_mesas_disponibles(
    IN p_fecha DATE,
    IN p_hora_inicio TIME,
    IN p_hora_fin TIME,
    IN p_personas INT
)
BEGIN
    SELECT DISTINCT
        m.id_mesa,
        m.numero_mesa,
        m.capacidad,
        u.nombre_ubicacion
    FROM mesas m
    JOIN ubicaciones u ON m.id_ubicacion = u.id_ubicacion
    JOIN estados_mesa em ON m.id_estado_mesa = em.id_estado_mesa
    WHERE em.nombre_estado <> 'Mantenimiento'
      AND m.capacidad >= p_personas
      AND NOT EXISTS (
          SELECT 1
          FROM reservas r
          WHERE r.id_mesa = m.id_mesa
            AND r.fecha_reserva = p_fecha
            AND r.id_estado_reserva IN (
                SELECT id_estado_reserva FROM estados_reserva
                WHERE nombre_estado IN ('Pendiente','Confirmada')
            )
            AND (p_hora_inicio < r.hora_fin AND p_hora_fin > r.hora_inicio)
      )
    ORDER BY m.id_mesa;
END$$

-- Reporte de reservas por rango de fechas (para el módulo de reportes)
-- Uso: CALL sp_reservas_por_periodo('2026-09-01', '2026-09-07');
CREATE PROCEDURE sp_reservas_por_periodo(
    IN p_fecha_inicio DATE,
    IN p_fecha_fin DATE
)
BEGIN
    SELECT
        fecha_reserva,
        COUNT(*) AS total_reservas
    FROM reservas
    WHERE fecha_reserva BETWEEN p_fecha_inicio AND p_fecha_fin
    GROUP BY fecha_reserva
    ORDER BY fecha_reserva;
END$$

DELIMITER ;
