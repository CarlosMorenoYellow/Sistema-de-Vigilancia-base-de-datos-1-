from pydantic import BaseModel, Field, field_validator
from typing import List, Literal
from uuid import UUID

class VectorSearchRequest(BaseModel):
    vector: List[float] = Field(..., description="Embedding de 512 dimensiones")
    tipo: Literal["persona", "vehiculo"] | None = Field(default=None, description="Tipo de objeto")
    limit: int = Field(default=10, ge=1, le=100, description="Cantidad de resultados")

    @field_validator("vector")
    @classmethod
    def validate_vector_dimension(cls, value: List[float]) -> List[float]:
        if len(value) != 512:
            raise ValueError("El vector debe tener exactamente 512 dimensiones")
        return value

class VectorSearchResult(BaseModel):
    id: UUID
    type: str
    color: str
    distance: float