from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class BookingCreate(BaseModel):
    date: datetime
    notes: Optional[str] = None

class BookingOut(BaseModel):
    id: str
    booking_id: str
    name: str
    email: str
    date: datetime
    notes: Optional[str]
    status: str
    meet_link: Optional[str]

    class Config:
        orm_mode = True
        json_encoders = {
            ObjectId: str
        }

class BookingStatusUpdate(BaseModel):
    status: str
