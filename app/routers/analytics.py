from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from datetime import date, datetime
from uuid import UUID
from app.database import get_db_connection

router = APIRouter(prefix="/analytics", tags=["Analítica"])
public_router = APIRouter(tags=["Analítica"])

@router.get("/cameras/{camera_id}/traffic", summary="Resumen de tráfico por cámara")
def camera_traffic(
    camera_id: str,
    from_date: date = Query(..., alias="from", description="Fecha inicio (YYYY-MM-DD)"),
    to_date: date = Query(..., alias="to", description="Fecha fin (YYYY-MM-DD)"),
    conn = Depends(get_db_connection)
):
    with conn.cursor() as cur:
        cur.execute("SELECT camera_id, hour_of_day, total_detections FROM get_camera_traffic(%s, %s, %s);",
                    (camera_id, from_date, to_date))
        rows = cur.fetchall()
        return rows

@router.get("/zones/{zone_type}", summary="Resumen por zona")
def zone_summary(zone_type: str, conn = Depends(get_db_connection)):
    with conn.cursor() as cur:
        cur.execute("SELECT location_id, location_name, active_cameras, total_events, total_critical_alerts FROM get_zone_summary(%s);",
                    (zone_type,))
        rows = cur.fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="Zona no encontrada")
        return rows

@router.get("/alerts/summary", summary="Conteo de alertas por severidad y cámara")
def alerts_summary(days: int = Query(30, ge=1), conn = Depends(get_db_connection)):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT a.severity AS severity, c.id AS camera_id, COUNT(*) AS total
            FROM alert a
            JOIN event e ON a.eid = e.id
            JOIN camera c ON e.cid = c.id
            WHERE e.time >= now() - (%s || ' days')::interval
            GROUP BY a.severity, c.id
            ORDER BY a.severity, total DESC;
        """, (str(days),))
        return cur.fetchall()

@public_router.get("/objects/{object_id}/similar", summary="Objetos similares al indicado")
def objects_similar(
    object_id: UUID,
    threshold: float = Query(0.20, ge=0.0, le=1.0),
    limit: Optional[int] = Query(5, ge=1, le=100),
    conn = Depends(get_db_connection)
):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM object WHERE id = %s AND embedding IS NOT NULL;",
            (object_id,)
        )
        if cur.fetchone() is None:
            raise HTTPException(
                status_code=404,
                detail="Objeto no encontrado o no tiene embedding"
            )
        cur.execute(
            """
                 SELECT f.object_id, f.object_type, f.distance_cosine,
                     f.camera_id, f.event_time
            FROM find_similar_objects(%s, %s, %s) f
                 ;
            """,
            (object_id, threshold, limit)
        )
        return cur.fetchall()