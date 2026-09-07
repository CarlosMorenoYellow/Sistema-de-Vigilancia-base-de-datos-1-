from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class EventBase(BaseModel):
    id: int
    time: datetime
    conf_level: float = Field(..., ge=0.0, le=1.0)
    box_x: Optional[int] = Field(None, ge=0)
    box_y: Optional[int] = Field(None, ge=0)
    box_w: Optional[int] = Field(None, ge=0)
    box_h: Optional[int] = Field(None, ge=0)
    cid: str = Field(..., min_length=12, max_length=12)

class EventCreate(EventBase):
    pass

class EventResponse(EventBase):
    class Config:
        from_attributes = True