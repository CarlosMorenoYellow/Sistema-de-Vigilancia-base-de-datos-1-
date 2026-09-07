import csv
import io
from typing import Any

from fastapi import APIRouter, Depends, File, UploadFile
from uuid import UUID
from app.database import get_db_connection

router = APIRouter(prefix="/extra", tags=["Consultas Extra"])
public_router = APIRouter(tags=["Importación"])


def _csv_value(row: dict[str, str], name: str) -> str | None:
    value = row.get(name)
    return value.strip() if value and value.strip() else None


def _parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = value.lower()
    if normalized not in {"true", "false"}:
        raise ValueError("el valor booleano debe ser true o false")
    return normalized == "true"


def _object_values(row: dict[str, str]) -> tuple[str, str, str | None, str | None, str | None, str | None]:
    object_type = _csv_value(row, "objeto_tipo")
    if object_type not in {"persona", "vehiculo"}:
        raise ValueError("objeto_tipo debe ser persona o vehiculo")

    if object_type == "persona":
        color = _csv_value(row, "persona_color_ropa")
        baggage = "maletin" if _parse_bool(_csv_value(row, "persona_porta_equipaje")) else None
        vehicle_type = plate = None
    else:
        color = _csv_value(row, "vehiculo_color")
        baggage = None
        vehicle_type = _csv_value(row, "vehiculo_tipo")
        plate = _csv_value(row, "vehiculo_matricula")

    if not color:
        raise ValueError("el color del objeto es obligatorio")
    return object_type, color, baggage, vehicle_type, plate, _csv_value(row, "objeto_embedding")


def _upsert_location(cur: Any, row: dict[str, str]) -> str:
    cur.execute(
        """
        INSERT INTO location (name, floor_no, zone_type, latitude, longitude)
        VALUES (%s, COALESCE(%s, '0'), %s, %s, %s)
        ON CONFLICT (name) DO UPDATE SET
            floor_no = EXCLUDED.floor_no,
            zone_type = EXCLUDED.zone_type,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude
        RETURNING id;
        """,
        (
            _csv_value(row, "ubicacion_nombre"),
            _csv_value(row, "ubicacion_piso"),
            _csv_value(row, "ubicacion_tipo_zona"),
            _csv_value(row, "ubicacion_latitud"),
            _csv_value(row, "ubicacion_longitud"),
        ),
    )
    return str(cur.fetchone()["id"])


def _upsert_camera(cur: Any, row: dict[str, str], location_id: str) -> None:
    cur.execute(
        """
        INSERT INTO camera (id, model, state, has_night_vision, lid)
        VALUES (%s, %s, %s::CAM_STATE, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            model = EXCLUDED.model,
            state = EXCLUDED.state,
            has_night_vision = EXCLUDED.has_night_vision,
            lid = EXCLUDED.lid;
        """,
        (
            _csv_value(row, "camara_nombre"),
            _csv_value(row, "camara_modelo"),
            _csv_value(row, "camara_estado"),
            _parse_bool(_csv_value(row, "camara_vision_nocturna")),
            location_id,
        ),
    )


def _upsert_event(cur: Any, row: dict[str, str]) -> bool:
    event_id = _csv_value(row, "evento_id")
    cur.execute("SELECT 1 FROM event WHERE id = %s;", (event_id,))
    existed = cur.fetchone() is not None
    cur.execute(
        """
        INSERT INTO event (id, time, conf_level, box_x, box_y, box_w, box_h, cid)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            time = EXCLUDED.time,
            conf_level = EXCLUDED.conf_level,
            box_x = EXCLUDED.box_x,
            box_y = EXCLUDED.box_y,
            box_w = EXCLUDED.box_w,
            box_h = EXCLUDED.box_h,
            cid = EXCLUDED.cid;
        """,
        (
            event_id,
            _csv_value(row, "evento_marca_tiempo"),
            _csv_value(row, "evento_confianza"),
            _csv_value(row, "evento_bbox_x"),
            _csv_value(row, "evento_bbox_y"),
            _csv_value(row, "evento_bbox_w"),
            _csv_value(row, "evento_bbox_h"),
            _csv_value(row, "camara_nombre"),
        ),
    )
    return existed


def _upsert_object(cur: Any, row: dict[str, str]) -> str:
    object_type, color, baggage, vehicle_type, plate, embedding = _object_values(row)
    cur.execute(
        """
        SELECT id FROM object
        WHERE type = %s::OBJECT_TYPE
          AND color = %s
          AND baggage IS NOT DISTINCT FROM %s::PERSON_BAGGAGE
          AND v_type IS NOT DISTINCT FROM %s::VEHICLE_TYPE
          AND plate IS NOT DISTINCT FROM %s
          AND embedding IS NOT DISTINCT FROM %s::vector
        LIMIT 1;
        """,
        (object_type, color, baggage, vehicle_type, plate, embedding),
    )
    existing = cur.fetchone()
    if existing:
        return str(existing["id"])

    cur.execute(
        """
        INSERT INTO object (type, color, baggage, v_type, plate, embedding)
        VALUES (%s::OBJECT_TYPE, %s, %s::PERSON_BAGGAGE, %s::VEHICLE_TYPE, %s, %s::vector)
        RETURNING id;
        """,
        (object_type, color, baggage, vehicle_type, plate, embedding),
    )
    return str(cur.fetchone()["id"])


def _upsert_alert(cur: Any, row: dict[str, str]) -> None:
    severity = _csv_value(row, "alerta_severidad")
    if not severity:
        return
    event_id = _csv_value(row, "evento_id")
    state = _csv_value(row, "alerta_estado")
    description = _csv_value(row, "alerta_descripcion")
    cur.execute(
        """
        INSERT INTO alert (state, severity, description, eid)
        SELECT %s::ALERT_STATE, %s::ALERT_SEVERITY, %s, %s
        WHERE NOT EXISTS (
            SELECT 1 FROM alert
            WHERE eid = %s AND state = %s::ALERT_STATE
              AND severity = %s::ALERT_SEVERITY
              AND description IS NOT DISTINCT FROM %s
        );
        """,
        (state, severity, description, event_id, event_id, state, severity, description),
    )


@public_router.post("/csv", summary="Cargar filas de videovigilancia desde CSV")
@router.post("/csv", include_in_schema=False)
async def upload_csv(file: UploadFile = File(...), conn=Depends(get_db_connection)):
    content = await file.read()
    try:
        rows = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))
    except (UnicodeDecodeError, csv.Error) as error:
        return {"added": 0, "updated": 0, "rejected": 0, "errors": [str(error)]}

    if not rows:
        return {"added": 0, "updated": 0, "rejected": 0, "errors": ["El CSV no contiene filas"]}

    added = updated = rejected = 0
    errors: list[dict[str, Any]] = []
    required = {"ubicacion_nombre", "camara_nombre", "evento_id", "evento_marca_tiempo", "evento_confianza", "objeto_tipo"}
    with conn.transaction():
        for row_number, row in enumerate(rows, start=2):
            try:
                if not required.issubset(row):
                    raise ValueError("faltan columnas requeridas")
                with conn.transaction():
                    location_id = _upsert_location(conn.cursor(), row)
                    _upsert_camera(conn.cursor(), row, location_id)
                    existed = _upsert_event(conn.cursor(), row)
                    object_id = _upsert_object(conn.cursor(), row)
                    conn.cursor().execute(
                        "INSERT INTO identifies (eid, oid) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                        (_csv_value(row, "evento_id"), object_id),
                    )
                    _upsert_alert(conn.cursor(), row)
                updated += int(existed)
                added += int(not existed)
            except Exception as error:
                rejected += 1
                errors.append({"row": row_number, "error": str(error)})

    return {"added": added, "updated": updated, "rejected": rejected, "errors": errors}

@router.get("/cameras-by-location/{location_id}", summary="Obtener cámaras instaladas en una ubicación específica")
def get_cameras_by_location(location_id: UUID, conn = Depends(get_db_connection)):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT C.id, C.model, C.state, C.has_night_vision, L.name as location_name
            FROM CAMERA C
            JOIN LOCATION L ON C.lid = L.id
            WHERE L.id = %s;
        """, (str(location_id),))
        return cur.fetchall()

@router.get("/active-alerts", summary="Listar todas las alertas generadas recientemente")
def get_active_alerts(conn = Depends(get_db_connection)):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT A.id, A.risk_level, A.rule_triggered, E.time, C.id as camera_id
            FROM ALERT A
            JOIN EVENT E ON A.eid = E.id
            JOIN CAMERA C ON E.cid = C.id
            ORDER BY E.time DESC;
        """)
        return cur.fetchall()