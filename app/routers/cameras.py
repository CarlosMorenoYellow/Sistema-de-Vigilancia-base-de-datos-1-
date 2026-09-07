from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.database import get_db_connection
from app.schemas.cameras import CameraCreate, CameraResponse

router = APIRouter(prefix="/camaras", tags=["Cámaras"])

@router.get("", response_model=List[CameraResponse], summary="Obtener todas las cámaras")
def get_cameras(conn = Depends(get_db_connection)):
    with conn.cursor() as cur:
        cur.execute("SELECT id, model, state, has_night_vision, lid FROM CAMERA;")
        return cur.fetchall()

@router.get("/{id}", response_model=CameraResponse, summary="Obtener cámara por ID")
def get_camera_by_id(id: str, conn = Depends(get_db_connection)):
    with conn.cursor() as cur:
        cur.execute("SELECT id, model, state, has_night_vision, lid FROM CAMERA WHERE id = %s;", (id,))
        camera = cur.fetchone()
        if not camera:
            raise HTTPException(status_code=404, detail="Cámara no encontrada")
        return camera

@router.post("", response_model=CameraResponse, status_code=status.HTTP_201_CREATED, summary="Crear cámara")
def create_camera(cam: CameraCreate, conn = Depends(get_db_connection)):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO CAMERA (id, model, state, has_night_vision, lid)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, model, state, has_night_vision, lid;
            """,
            (cam.id, cam.model, cam.state.value, cam.has_night_vision, str(cam.lid))
        )
        new_cam = cur.fetchone()
        conn.commit()
        return new_cam

@router.put("/{id}", response_model=CameraResponse, summary="Actualizar cámara")
def update_camera(id: str, cam: CameraCreate, conn = Depends(get_db_connection)):
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE CAMERA
            SET model = %s, state = %s, has_night_vision = %s, lid = %s
            WHERE id = %s
            RETURNING id, model, state, has_night_vision, lid;
            """,
            (cam.model, cam.state.value, cam.has_night_vision, str(cam.lid), id)
        )
        updated_cam = cur.fetchone()
        if not updated_cam:
            raise HTTPException(status_code=404, detail="Cámara no encontrada")
        conn.commit()
        return updated_cam