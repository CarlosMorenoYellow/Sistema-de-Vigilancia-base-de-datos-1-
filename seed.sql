-- Tabla temporal para cargar las tuplas del archivo.csv
CREATE TABLE TEMP_TABLE (
    ubicacion_nombre VARCHAR(50),
    ubicacion_piso VARCHAR(10),
    ubicacion_latitud NUMERIC(6,4),
    ubicacion_longitud NUMERIC(7,4),
    ubicacion_tipo_zona VARCHAR(30),
    camara_nombre CHAR(12),
    camara_modelo VARCHAR(40),
    camara_estado CAM_STATE,
    camara_vision_nocturna BOOLEAN,
    evento_id BIGINT,
    evento_marca_tiempo TIMESTAMPTZ,
    evento_confianza NUMERIC(5,4),
    evento_bbox_x SMALLINT,
    evento_bbox_y SMALLINT,
    evento_bbox_w SMALLINT,
    evento_bbox_h SMALLINT,
    objeto_tipo OBJECT_TYPE,
    persona_color_ropa VARCHAR(15),
    persona_porta_equipaje BOOLEAN,
    vehiculo_tipo VEHICLE_TYPE,
    vehiculo_color VARCHAR(15),
    vehiculo_matricula CHAR(6),
    alerta_severidad ALERT_SEVERITY,
    alerta_descripcion VARCHAR(300),
    alerta_estado ALERT_STATE,
    objeto_embedding VECTOR(512)
);

\copy TEMP_TABLE FROM 'seed_100.csv' DELIMITER ',' CSV HEADER NULL AS '';

INSERT INTO LOCATION(name, floor_no, zone_type, latitude, longitude)
SELECT DISTINCT
    ubicacion_nombre,
    ubicacion_piso,
    ubicacion_tipo_zona,
    ubicacion_latitud,
    ubicacion_longitud
FROM TEMP_TABLE
WHERE ubicacion_nombre IS NOT NULL;

INSERT INTO CAMERA(id, model, state, has_night_vision, lid)
SELECT DISTINCT
    T.camara_nombre,
    T.camara_modelo,
    T.camara_estado,
    T.camara_vision_nocturna,
    L.id
FROM TEMP_TABLE T
JOIN LOCATION L ON T.ubicacion_nombre = L.name
WHERE T.camara_nombre IS NOT NULL;

INSERT INTO EVENT(id, time, conf_level, box_x, box_y, box_w, box_h, cid)
SELECT DISTINCT
    T.evento_id,
    T.evento_marca_tiempo,
    T.evento_confianza,
    T.evento_bbox_x,
    T.evento_bbox_y,
    T.evento_bbox_w,
    T.evento_bbox_h,
    C.id
FROM TEMP_TABLE T
JOIN CAMERA C ON C.id = T.camara_nombre
WHERE T.evento_id IS NOT NULL;

INSERT INTO ALERT(state, severity, description, eid)
SELECT
    T.alerta_estado,
    T.alerta_severidad,
    T.alerta_descripcion,
    E.id
FROM TEMP_TABLE T
JOIN EVENT E ON E.id = T.evento_id
WHERE T.alerta_severidad IS NOT NULL;

INSERT INTO OBJECT(type, color, baggage, v_type, plate, embedding)
SELECT DISTINCT
    T.objeto_tipo,
    CASE
        WHEN T.objeto_tipo = 'persona' THEN T.persona_color_ropa
        WHEN T.objeto_tipo = 'vehiculo' THEN T.vehiculo_color
    END,
    CASE
        WHEN T.objeto_tipo = 'persona' AND T.persona_porta_equipaje IS TRUE THEN 'maletin'
        ELSE NULL
    END::PERSON_BAGGAGE,
    T.vehiculo_tipo,
    T.vehiculo_matricula,
    T.objeto_embedding
FROM TEMP_TABLE T
WHERE T.objeto_tipo IS NOT NULL;

INSERT INTO IDENTIFIES(eid, oid)
SELECT E.id, O.id
FROM TEMP_TABLE T
JOIN EVENT E ON E.id = T.evento_id
JOIN OBJECT O ON O.type = T.objeto_tipo
    AND O.embedding IS NOT DISTINCT FROM T.objeto_embedding
    AND (
        (T.objeto_tipo = 'persona'
         AND O.color IS NOT DISTINCT FROM T.persona_color_ropa
         AND O.baggage IS NOT DISTINCT FROM (CASE WHEN T.persona_porta_equipaje IS TRUE THEN 'maletin' ELSE NULL END::PERSON_BAGGAGE))
        OR
        (T.objeto_tipo = 'vehiculo'
         AND O.color IS NOT DISTINCT FROM T.vehiculo_color
         AND O.plate IS NOT DISTINCT FROM T.vehiculo_matricula
         AND O.v_type IS NOT DISTINCT FROM T.vehiculo_tipo)
    );

-- Eliminar la tabla temporal
DROP TABLE TEMP_TABLE;