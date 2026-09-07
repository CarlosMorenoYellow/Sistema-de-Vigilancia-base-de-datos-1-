from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AlertSummaryResponse(BaseModel):
    risk_level: str
    total: int

class ObjectFrequencyResponse(BaseModel):
    label_name: str
    total_detections: int

class EventFilterResponse(BaseModel):
    id: int
    time: datetime
    conf_level: float
    box_x: Optional[int]
    box_y: Optional[int]
    box_w: Optional[int]
    box_h: Optional[int]
    cid: str