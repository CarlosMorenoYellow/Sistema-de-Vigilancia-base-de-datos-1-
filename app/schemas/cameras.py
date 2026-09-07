from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum

class CamState(str, Enum):
    activa = 'activa'
    en_mantenimiento = 'en_mantenimiento'
    inactiva = 'inactiva'

class CameraBase(BaseModel):
    id: str = Field(..., min_length=12, max_length=12, description="Formato CAM-_____-__")
    model: str = Field(..., max_length=40)
    state: CamState
    has_night_vision: bool = False
    lid: UUID

class CameraCreate(CameraBase):
    pass

class CameraResponse(CameraBase):
    class Config:
        from_attributes = True