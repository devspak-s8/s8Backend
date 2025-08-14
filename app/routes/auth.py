# app/routes/auth_routes.py
from datetime import timedelta
from fastapi import APIRouter, Body, Query, Security, HTTPException
from app.middleware.rbac import get_current_user
from app.schemas.user import *
from app.utils.hash_utils import hash_password, verify_password
from app.utils.auth_utils import create_access_token, decode_token, create_refresh_token
from app.database import user_collection
from app.core.config import settings
from app.core.error_messages import ErrorResponses  # Centralized error messages
from uuid import uuid4
from app.utils.email_utils import send_email
from datetime import datetime, timedelta
auth_router = APIRouter(tags=["Auth"])
from pydantic import BaseModel
from bson import ObjectId
class EmailSchema(BaseModel):
    email: str
# Temporary in-memory token storage
reset_tokens = {}
verification_tokens = {}


@auth_router.post("/register")
async def register(data: RegisterSchema):
    user = await user_collection.find_one({"email": data.email})
    if user:
        raise ErrorResponses.USER_EXISTS

    hashed_pw = hash_password(data.password)
    role = "admin" if (data.email == settings.ADMIN_EMAIL and data.password == settings.ADMIN_PASSWORD) else "user"

    user_data = {**data.dict(), "password": hashed_pw, "is_verified": False, "role": role}
    await user_collection.insert_one(user_data)
    return {"msg": "Registered successfully"}
@auth_router.post("/login", response_model=TokenResponse)
async def login(data: LoginSchema):
    user = await user_collection.find_one({"email": data.email})
    if not user or not verify_password(data.password, user["password"]):
        raise ErrorResponses.INVALID_CREDENTIALS

    # Force is_verified to boolean
    is_verified = bool(user.get("is_verified", False))

    return {
        "access_token": create_access_token({
            "email": user["email"],
            "role": user["role"]
        }),
        "refresh_token": create_refresh_token({
            "email": user["email"],
            "role": user["role"]
        }, timedelta(days=7)),
        "is_verified": is_verified,
        "is_admin": user.get("role") == "admin"
    }

@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str = Body(...)):
    try:
        payload = decode_token(refresh_token, expected_type="refresh")
        email = payload.get("email")
        role = payload.get("role")

        if not email:
            raise ErrorResponses.INVALID_TOKEN

        user = await user_collection.find_one({"email": email})
        if not user:
            raise ErrorResponses.USER_NOT_FOUND

        token_data = {"email": email, "role": role}
        access_token = create_access_token(token_data)
        refresh_token_new = create_refresh_token(token_data, expires_delta=timedelta(days=7))

        return {
            "access_token": access_token,
            "refresh_token": refresh_token_new,
        }

    except Exception:
        raise ErrorResponses.INVALID_TOKEN


@auth_router.post("/send-verification-email")
async def send_verification_email(data: EmailSchema):
    email = data.email

    # Fetch user from DB
    user = await user_collection.find_one({"email": email})
    if not user:
        raise ErrorResponses.USER_NOT_FOUND

    if user.get("is_verified"):
        return {"msg": "Email already verified"}

    # Generate token
    token = str(uuid4())

    # Save token + expiration in DB
    expires_at = datetime.utcnow() + timedelta(hours=24)
    await user_collection.update_one(
        {"email": email},
        {"$set": {"verification_token": token, "token_expires_at": expires_at}}
    )
    print("Token expires at:", user["token_expires_at"], type(user["token_expires_at"]))

    # Email content
    verify_link = f"http://localhost:5173/verify-email?token={token}"
    subject = "✅ Verify Your Email - S8Globals"
    body = f"""
As-salaamu 'alaykum 👋,

Thank you for registering at S8Builder! Please verify your email by clicking the link below:

{verify_link}

If you did not register, simply ignore this message.

-- Team S8Globals
"""

    try:
        send_email(email, subject, body)
    except Exception as e:
        print("SMTP send failed:", e)
        raise ErrorResponses.INTERNAL_SERVER_ERROR

    return {"msg": "✅ Verification email sent successfully"}
from fastapi.responses import RedirectResponse
@auth_router.get("/verify-email")
async def verify_email(token: str = Query(...)):
    # 1️⃣ Find the user by token
    user = await user_collection.find_one({"verification_token": token})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")

    # 2️⃣ Check if token expired
    if datetime.utcnow() > user["token_expires_at"]:
        raise HTTPException(status_code=400, detail="Token expired")

    # 3️⃣ Update user to verified
    await user_collection.update_one(
        {"_id": ObjectId(user["_id"])},  # ✅ Proper ObjectId casting
        {
            "$set": {"is_verified": True},
            "$unset": {"verification_token": "", "token_expires_at": ""}
        }
    )

    # 4️⃣ Redirect to frontend login page
    return RedirectResponse(url="http://localhost:5173/login?verified=true")
@auth_router.post("/forgot-password")
async def forgot_password(email: str):
    user = await user_collection.find_one({"email": email})
    if not user:
        raise ErrorResponses.USER_NOT_FOUND

    token = str(uuid4())
    reset_tokens[token] = email
# Local development (no SSL)
    reset_link = f"http://localhost:5173/reset-password?token={token}"

    subject = "🔑 Password Reset Request"
    body = f"""
    As-salaamu 'alaykum 👋,\n
    You requested to reset your password.\n
    Click this link to reset: {reset_link}\n
    If you didn’t request this, just ignore it.\n
    -- Team S8Globals
    """

    try:
        send_email(email, subject, body)
    except Exception:
        raise ErrorResponses.INTERNAL_SERVER_ERROR

    return {"msg": "✅ Password reset email sent successfully"}


@auth_router.post("/reset-password")
async def reset_password(data: ResetPasswordSchema):
    email = reset_tokens.get(data.token)
    if not email:
        raise ErrorResponses.INVALID_TOKEN

    hashed_pw = hash_password(data.new_password)
    await user_collection.update_one({"email": email}, {"$set": {"password": hashed_pw}})
    del reset_tokens[data.token]
    return {"msg": "Password has been reset successfully"}


@auth_router.get("/me", response_model=UserOut)
async def get_current_user_info(current_user: dict = Security(get_current_user)):
    user = await user_collection.find_one({"email": current_user["email"]})
    if not user:
        raise ErrorResponses.USER_NOT_FOUND
    return user
