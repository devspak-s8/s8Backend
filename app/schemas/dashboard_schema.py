# app/schemas/dashboard_schema.py
from pydantic import BaseModel
from typing import List
from datetime import datetime

class BookingSummary(BaseModel):
    total_bookings: int
    pending: int
    approved: int
    rejected: int

class BookingShortInfo(BaseModel):
    id: str
    booking_id: str
    date: datetime
    status: str
    name: str
    email: str

class DashboardData(BaseModel):
    summary: BookingSummary
    recent_bookings: List[BookingShortInfo]
