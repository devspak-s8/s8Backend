# app/models/user_model.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class User(BaseModel):
    id: Optional[str]
    email: EmailStr
    name: str
    password: str
    
    # Auth / account
    is_verified: bool = False
    role: str = "user"   # "user" | "admin"
    created_at: datetime = datetime.utcnow()
    last_login: Optional[datetime] = None

    # SaaS-related fields
    plan: str = "free"   # "free", "pro", "premium"
    credits: int = 0     # like template usage credits
    templates_created: int = 0
    bookings_count: int = 0

    # Personalization
    avatar_url: Optional[str] = None
    interests: Optional[List[str]] = []   # e.g. ["dashboards", "ecommerce", "design"]

    # Notifications
    notifications_enabled: bool = True
