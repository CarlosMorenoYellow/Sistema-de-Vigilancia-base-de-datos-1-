-- Conteo de detecciones por hora para una cámara y rango de fechas.
DROP FUNCTION IF EXISTS get_camera_traffic(CHAR(12), TIMESTAMPTZ, TIMESTAMPTZ);

CREATE OR REPLACE FUNCTION get_camera_traffic(
    p_cid CHAR(12),
    p_start DATE,
    p_end DATE
)
RETURNS TABLE (
    camera_id CHAR(12),
    hour_of_day INTEGER,
    total_detections BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT p_cid,
           EXTRACT(HOUR FROM e.time)::INTEGER,
           COUNT(*)
    FROM event e
    WHERE e.cid = p_cid
      AND e.time >= p_start::TIMESTAMPTZ
      AND e.time < (p_end + 1)::TIMESTAMPTZ
    GROUP BY EXTRACT(HOUR FROM e.time)
    ORDER BY EXTRACT(HOUR FROM e.time);
END;
$$ LANGUAGE plpgsql STABLE;


-- Resumen por ubicación para un tipo de zona.
DROP FUNCTION IF EXISTS get_zone_summary(TEXT);

CREATE OR REPLACE FUNCTION get_zone_summary(
    p_zone_type TEXT
)
RETURNS TABLE (
    location_id UUID,
    location_name VARCHAR(50),
    active_cameras BIGINT,
    total_events BIGINT,
    total_critical_alerts BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        l.id,
        l.name,
        (SELECT COUNT(*) FROM camera c
         WHERE c.lid = l.id AND c.state = 'activa'),
        (SELECT COUNT(*) FROM event e
         JOIN camera c ON c.id = e.cid
         WHERE c.lid = l.id),
        (SELECT COUNT(*) FROM alert a
         JOIN event e ON e.id = a.eid
         JOIN camera c ON c.id = e.cid
         WHERE c.lid = l.id AND a.severity = 'critica')
    FROM location l
    WHERE l.zone_type = p_zone_type
    ORDER BY l.name;
END;
$$ LANGUAGE plpgsql STABLE;


-- Búsqueda coseno de objetos del mismo tipo.
DROP FUNCTION IF EXISTS find_similar_objects(UUID, DOUBLE PRECISION, INTEGER);

CREATE OR REPLACE FUNCTION find_similar_objects(
    p_oid UUID,
    p_threshold DOUBLE PRECISION DEFAULT 0.20,
    p_limit INTEGER DEFAULT 5
)
RETURNS TABLE (
    object_id UUID,
    object_type OBJECT_TYPE,
    distance_cosine DOUBLE PRECISION,
    camera_id CHAR(12),
    event_time TIMESTAMPTZ
) AS $$
DECLARE
    ref_vector VECTOR;
    ref_type OBJECT_TYPE;
BEGIN
    IF p_threshold < 0 OR p_threshold > 1 THEN
        RAISE EXCEPTION 'threshold must be between 0 and 1';
    END IF;

    SELECT o.embedding, o.type INTO ref_vector, ref_type
    FROM object o
    WHERE o.id = p_oid;

    IF ref_vector IS NULL THEN
        RAISE EXCEPTION 'Reference object not found or embedding is NULL';
    END IF;

    RETURN QUERY
    SELECT o.id,
           o.type,
           (o.embedding <=> ref_vector),
           c.id,
           e.time
    FROM object o
    JOIN identifies i ON i.oid = o.id
    JOIN event e ON e.id = i.eid
    JOIN camera c ON c.id = e.cid
    WHERE o.embedding IS NOT NULL
      AND o.id IS DISTINCT FROM p_oid
      AND o.type = ref_type
      AND (o.embedding <=> ref_vector) <= p_threshold
    ORDER BY (o.embedding <=> ref_vector), e.time
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;