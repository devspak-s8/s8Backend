# app/routes/auth_routes.py
from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, Security
from app.middleware.rbac import get_current_user
from app.schemas.user import *
from app.models.user import User
from app.utils.hash_utils import hash_password, verify_password
from app.utils.auth_utils import create_access_token
from app.database import user_collection
from app.core.config import settings

from app.utils.hash_utils import hash_password

from fastapi import Query
from uuid import uuid4
from app.utils.email_utils import send_email
auth_router = APIRouter()

@auth_router.post("/register")
async def register(data: RegisterSchema):
    user = await user_collection.find_one({"email": data.email})
    if user:
        raise HTTPException(status_code=400, detail="User exists")
    hashed_pw = hash_password(data.password)
    role = "admin" if (data.email == settings.ADMIN_EMAIL and data.password == settings.ADMIN_PASSWORD) else "user"
    user_data = {**data.dict(), "password": hashed_pw, "is_verified": False, "role": role}
    await user_collection.insert_one(user_data)
    return {"msg": "Registered successfully"}

@auth_router.post("/login", response_model=TokenResponse)
async def login(data: LoginSchema):
    user = await user_collection.find_one({"email": data.email})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token_data = {"email": user["email"], "role": user["role"]}
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_access_token(token_data, timedelta(days=7))
    }


# Temporary in-memory store for verification tokens (for prod use DB or cache)
verification_tokens = {}

@auth_router.post("/send-verification-email")
async def send_verification_email(email: str = Query(...)):
    user = await user_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["is_verified"]:
        return {"msg": "Email already verified"}

    token = str(uuid4())
    verification_tokens[token] = email

    verify_link = f"http://yourfrontend.com/verify-email?token={token}"
    body = f"Click here to verify your email: {verify_link}"
    send_email(email, "Verify your email", body)
    return {"msg": "Verification email sent"}

@auth_router.get("/verify-email")
async def verify_email(token: str = Query(...)):
    email = verification_tokens.get(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    await user_collection.update_one({"email": email}, {"$set": {"is_verified": True}})
    del verification_tokens[token]
    return {"msg": "Email verified successfully"}
reset_tokens = {}

@auth_router.post("/forgot-password")
async def forgot_password(email: str):
    user = await user_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token = str(uuid4())
    reset_tokens[token] = email

    reset_link = f"http://yourfrontend.com/reset-password?token={token}"
    body = f"Click here to reset your password: {reset_link}"
    send_email(email, "Password Reset Request", body)
    return {"msg": "Password reset email sent"}

@auth_router.post("/reset-password")
async def reset_password(data: ResetPasswordSchema):
    email = reset_tokens.get(data.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    hashed_pw = hash_password(data.new_password)
    await user_collection.update_one({"email": email}, {"$set": {"password": hashed_pw}})
    del reset_tokens[data.token]
    return {"msg": "Password has been reset successfully"}
@auth_router.get("/me", response_model=UserOut)
async def get_current_user_info(current_user: dict = Security(get_current_user)):
    user = await user_collection.find_one({"email": current_user["email"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
