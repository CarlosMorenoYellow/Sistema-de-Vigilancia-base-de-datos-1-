from pydantic import BaseModel, Field
from uuid import UUID

class LocationBase(BaseModel):
    name: str = Field(..., max_length=50, description="Nombre de la ubicación o edificio")
    floor_no: str = Field(default="0", max_length=10, description="Piso o nivel")
    zone_type: str = Field(..., max_length=30, description="Tipo de zona (ej. comercial, estacionamiento)")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitud entre -90 y 90")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitud entre -180 y 180")

class LocationCreate(LocationBase):
    pass

class LocationResponse(LocationBase):
    id: UUID

    class Config:
        from_attributes = True