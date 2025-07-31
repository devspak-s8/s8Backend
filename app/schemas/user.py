# app/schemas/user_schema.py
from pydantic import BaseModel, EmailStr

class RegisterSchema(BaseModel):
    email: EmailStr
    name: str
    password: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordSchema(BaseModel):
    email: EmailStr

class ResetPasswordSchema(BaseModel):
    token: str
    new_password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str

class UserOut(BaseModel):
    email: EmailStr
    name: str
    role: str
    is_verified: bool
