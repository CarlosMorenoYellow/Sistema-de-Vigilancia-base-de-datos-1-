-- Extensión pgVector
CREATE EXTENSION IF NOT EXISTS vector;

-- Tipos de dato ENUM
CREATE TYPE CAM_STATE AS ENUM ('activa', 'en_mantenimiento', 'inactiva');
CREATE TYPE ALERT_STATE AS ENUM ('atendida', 'pendiente', 'descartada');
CREATE TYPE ALERT_SEVERITY AS ENUM ('baja', 'media', 'alta', 'critica');
CREATE TYPE OBJECT_TYPE AS ENUM ('persona', 'vehiculo');
CREATE TYPE PERSON_BAGGAGE AS ENUM ('maletin', 'mochila', 'maleta');
CREATE TYPE VEHICLE_TYPE AS ENUM ('sedan', 'SUV', 'motocicleta', 'camion', 'autobus');

-- Tablas

CREATE TABLE LOCATION(
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    floor_no VARCHAR(10) DEFAULT '0' NOT NULL,
    zone_type VARCHAR(30) NOT NULL,
    latitude NUMERIC(6,4) NOT NULL,
    longitude NUMERIC(7,4) NOT NULL,

    CHECK (latitude BETWEEN -90.0000 AND 90.0000),
    CHECK (longitude BETWEEN -180.0000 AND 180.0000)
);

CREATE TABLE CAMERA(
    id CHAR(12) NOT NULL PRIMARY KEY,
    model VARCHAR(40) NOT NULL,
    state CAM_STATE NOT NULL,
    has_night_vision BOOLEAN DEFAULT false NOT NULL,
    lid UUID NOT NULL REFERENCES LOCATION(id)
);

CREATE TABLE EVENT(
    id BIGINT NOT NULL PRIMARY KEY,
    time TIMESTAMPTZ NOT NULL,
    conf_level NUMERIC(5,4) NOT NULL,
    box_x SMALLINT,
    box_y SMALLINT,
    box_w SMALLINT,
    box_h SMALLINT,
    cid CHAR(12) NOT NULL REFERENCES CAMERA(id),

    CHECK (conf_level BETWEEN 0.0000 AND 1.0000),
    CHECK (box_x >= 0),
    CHECK (box_y >= 0),
    CHECK (box_w >= 0),
    CHECK (box_h >= 0)
);

CREATE TABLE ALERT(
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    state ALERT_STATE NOT NULL,
    severity ALERT_SEVERITY NOT NULL,
    description VARCHAR(300),
    eid BIGINT NOT NULL REFERENCES EVENT(id)
);

CREATE TABLE OBJECT(
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    type OBJECT_TYPE NOT NULL,
    color varchar(15) NOT NULL,
    baggage PERSON_BAGGAGE,
    v_type VEHICLE_TYPE,
    plate CHAR(6),
    embedding VECTOR(512)
);

CREATE TABLE IDENTIFIES(
    eid BIGINT NOT NULL REFERENCES EVENT(id),
    oid UUID NOT NULL REFERENCES OBJECT(id),

    PRIMARY KEY (eid, oid)
);

-- índices

CREATE INDEX idx_event_cid ON EVENT(cid);
CREATE INDEX idx_event_time ON EVENT(time);
CREATE INDEX idx_location_zone_type ON LOCATION(zone_type);

-- Comentarios de tablas y columnas

COMMENT ON TABLE LOCATION IS 'Información de la ubicación de una cámara';
COMMENT ON COLUMN LOCATION.id IS 'Clave primaria de la tabla. Identificador de tipo UUID. No nulo';
COMMENT ON COLUMN LOCATION.name IS 'Nombre del lugar (Pensando principalmente para el nombre del edificio, máximo 50 caracteres). No nulo';
COMMENT ON COLUMN LOCATION.floor_no IS 'Nivel en el cual se encuentra la cámara. Dato de tipo VARCHAR(10), de manera que permite opciones como "S1", "Terraza", etc. No nulo (Si no se especifica un piso, el número por defecto es 0)';
COMMENT ON COLUMN LOCATION.zone_type IS 'Tipo de zona en el cual se encuentra una cámara (Por ejemplo zona comercial, estacionamiento, etc.) No se limitan las opciones, pero se restringe a 30 caracteres. No nulo';
COMMENT ON COLUMN LOCATION.latitude IS 'Tipo de dato NUMERIC(6,4) que corresponde a una coordenada geográfica que mide la distancia al Ecuador. Está entre -90 y 90 grados. No nulo';
COMMENT ON COLUMN LOCATION.longitude IS 'Tipo de dato NUMERIC(7,4) que corresponde a una coordenada geográfica que mide la distancia respecto al Meridiano de Greenwich. Está entre -180 y 180 grados. No nulo';

COMMENT ON TABLE CAMERA IS 'Información de una cámara';
COMMENT ON COLUMN CAMERA.id IS 'Clave primaria. String de 12 caracteres el cual en principio debería tener la estructura "CAM-_____-__", donde los primeros 5 caracteres libres corresponden a una descripción corta de la ubicación y los últimos dos un número individual para cada cámara dentro de la misma ubicación. No nulo';
COMMENT ON COLUMN CAMERA.model IS 'Modelo de la cámara. Máximo 40 caracteres. No nulo';
COMMENT ON COLUMN CAMERA.state IS 'Estado de la cámara. Puede ser "activa", "en_mantenimiento o "inactiva". No nulo';
COMMENT ON COLUMN CAMERA.has_night_vision IS 'Booleano que inidica si la cámara tiene o no visión nocturna. No nulo (false por defecto)';
COMMENT ON COLUMN CAMERA.lid IS 'Clave foránea hacia el identificador de una ubicación. No nulo';

COMMENT ON TABLE EVENT IS 'Eventos generados por movimientos captados en cámaras';
COMMENT ON COLUMN EVENT.id IS 'Clave primaria. Número entero positivo. No nulo';
COMMENT ON COLUMN EVENT.time IS 'Fecha con zona horaria en la cual ocurrió el evento. No nulo';
COMMENT ON COLUMN EVENT.conf_level IS 'Tipo de dato NUMERIC(5,4) entre 0 y 1 que indica el nivel de confianza del evento. No nulo';
COMMENT ON COLUMN EVENT.box_x IS 'Número entero. Coordenada x de la ubicación del recuadro de un video';
COMMENT ON COLUMN EVENT.box_y IS 'Número entero. Coordenada y de la ubicación del recuadro de un video';
COMMENT ON COLUMN EVENT.box_w IS 'Número entero. Anchura del recuadro de un video';
COMMENT ON COLUMN EVENT.box_h IS 'Número entero. Altura del recuadro de un video';
COMMENT ON COLUMN EVENT.cid IS 'Clave foránea hacia el identificador de una cámara. No nulo';

COMMENT ON TABLE ALERT IS 'Alertas generadas por una violación a alguna regla preestablecida';
COMMENT ON COLUMN ALERT.id IS 'Clave primaria de la tabla. Identificador de tipo UUID. No nulo';
COMMENT ON COLUMN ALERT.state IS 'Estado de atención de la alerta. Puede ser "atendida", "pendiente" o "descartada". No nulo';
COMMENT ON COLUMN ALERT.severity IS 'Nivel de seriedad de la alerta. Puede ser "baja", "media", "alta" o "critica". No nulo';
COMMENT ON COLUMN ALERT.description IS 'Descripción de una alerta. Máximo 300 caracteres';
COMMENT ON COLUMN ALERT.eid IS 'Clave foránea hacia el identificador de un evento. No nulo';

COMMENT ON TABLE OBJECT IS 'Objetos detectados en un evento';
COMMENT ON COLUMN OBJECT.id IS 'Clave primaria de la tabla. Identificador de tipo UUID. No nulo';
COMMENT ON COLUMN OBJECT.type IS 'Tipo de objeto detectado. Puede ser "persona" o "vehiculo". No nulo';
COMMENT ON COLUMN OBJECT.color IS 'String de máximo 15 caracteres que indica el color principal de la persona o vehículo detectado. No nulo';
COMMENT ON COLUMN OBJECT.baggage IS 'Si el objeto es de tipo persona, indica si tiene "maletin", "mochila" o "maleta". Si no tiene nada o el objeto es un vehículo, es NULL';
COMMENT ON COLUMN OBJECT.v_type IS 'Si el objeto es de tipo vehículo, indica el tipo de vehículo. Puede ser "sedan", "SUV", "motocicleta", "camion" o "autobus". Si el objeto es persona, es NULL';
COMMENT ON COLUMN OBJECT.plate IS 'Si el objeto es de tipo vehículo, indica la matrícula (Identificador del vehículo de 6 caracteres). Si el objeto es persona, es NULL';
COMMENT ON COLUMN OBJECT.embedding IS 'Vector de 512 dimensiones generado por pgVector que describe el objeto detectado. Este vector solo va a ser generado si el evento tuvo un 60% de confianza o más, en caso contrario, será NULL';

COMMENT ON TABLE IDENTIFIES IS 'Relación entre un objeto y un evento. La clave primaria está conformada por sus dos columnas';
COMMENT ON COLUMN IDENTIFIES.eid IS 'Clave foránea hacia el identificador de un evento. No nulo';
COMMENT ON COLUMN IDENTIFIES.oid IS 'Clave foránea hacia el identificador de un objeto. No nulo';