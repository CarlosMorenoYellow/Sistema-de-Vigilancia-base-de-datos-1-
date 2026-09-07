from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.database import get_db_connection
from app.schemas.events import EventCreate, EventResponse

router = APIRouter(prefix="/eventos", tags=["Eventos"])

@router.get("", response_model=List[EventResponse], summary="Obtener todos los eventos")
def get_events(conn = Depends(get_db_connection)):
    with conn.cursor() as cur:
        cur.execute("SELECT id, time, conf_level, box_x, box_y, box_w, box_h, cid FROM EVENT;")
        return cur.fetchall()

@router.get("/{id}", response_model=EventResponse, summary="Obtener evento por ID")
def get_event_by_id(id: int, conn = Depends(get_db_connection)):
    with conn.cursor() as cur:
        cur.execute("SELECT id, time, conf_level, box_x, box_y, box_w, box_h, cid FROM EVENT WHERE id = %s;", (id,))
        event = cur.fetchone()
        if not event:
            raise HTTPException(status_code=404, detail="Evento no encontrado")
        return event

@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED, summary="Crear evento")
def create_event(event: EventCreate, conn = Depends(get_db_connection)):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO EVENT (id, time, conf_level, box_x, box_y, box_w, box_h, cid)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, time, conf_level, box_x, box_y, box_w, box_h, cid;
            """,
            (event.id, event.time, event.conf_level, event.box_x, event.box_y, event.box_w, event.box_h, event.cid)
        )
        new_event = cur.fetchone()
        conn.commit()
        return new_event