from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from app.database import get_db_connection
from app.schemas.locations import LocationCreate, LocationResponse

router = APIRouter(prefix="/ubicaciones", tags=["Ubicaciones"])

@router.get("", response_model=List[LocationResponse], summary="Obtener todas las ubicaciones")
def get_locations(conn = Depends(get_db_connection)):
    with conn.cursor() as cur:
        cur.execute("SELECT id, name, floor_no, zone_type, latitude, longitude FROM LOCATION;")
        return cur.fetchall()

@router.get("/{id}", response_model=LocationResponse, summary="Obtener ubicación por ID")
def get_location_by_id(id: UUID, conn = Depends(get_db_connection)):
    with conn.cursor() as cur:
        cur.execute("SELECT id, name, floor_no, zone_type, latitude, longitude FROM LOCATION WHERE id = %s;", (str(id),))
        loc = cur.fetchone()
        if not loc:
            raise HTTPException(status_code=404, detail="Ubicación no encontrada")
        return loc

@router.post("", response_model=LocationResponse, status_code=status.HTTP_201_CREATED, summary="Crear ubicación")
def create_location(loc: LocationCreate, conn = Depends(get_db_connection)):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO LOCATION (name, floor_no, zone_type, latitude, longitude)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, name, floor_no, zone_type, latitude, longitude;
            """,
            (loc.name, loc.floor_no, loc.zone_type, loc.latitude, loc.longitude)
        )
        new_loc = cur.fetchone()
        conn.commit()
        return new_loc

@router.put("/{id}", response_model=LocationResponse, summary="Actualizar ubicación")
def update_location(id: UUID, loc: LocationCreate, conn = Depends(get_db_connection)):
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE LOCATION
            SET name = %s, floor_no = %s, zone_type = %s, latitude = %s, longitude = %s
            WHERE id = %s
            RETURNING id, name, floor_no, zone_type, latitude, longitude;
            """,
            (loc.name, loc.floor_no, loc.zone_type, loc.latitude, loc.longitude, str(id))
        )
        updated_loc = cur.fetchone()
        if not updated_loc:
            raise HTTPException(status_code=404, detail="Ubicación no encontrada")
        conn.commit()
        return updated_loc

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar ubicación")
def delete_location(id: UUID, conn = Depends(get_db_connection)):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM LOCATION WHERE id = %s RETURNING id;", (str(id),))
        deleted = cur.fetchone()
        if not deleted:
            raise HTTPException(status_code=404, detail="Ubicación no encontrada")
        conn.commit()
        return None