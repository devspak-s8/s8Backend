# app/models/user_model.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    id: Optional[str]
    email: EmailStr
    name: str
    password: str
    is_verified: bool = False
    role: str = "user"  # or "admin"
