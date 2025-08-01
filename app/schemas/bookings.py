from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class BookingCreate(BaseModel):
    service_id: str
    user_id: str
    date: datetime
    notes: Optional[str] = None

class BookingOut(BaseModel):
    id: str
    service_id: str
    user_id: str
    date: datetime
    notes: Optional[str]
    status: str

class BookingStatusUpdate(BaseModel):
    status: str
