# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.auth import auth_router
from app.routes.bookings import booking_router
from app.routes.ws import ws_router
from app.database import user_collection  # <-- make sure this is the correct path to user_collection
import logging

app = FastAPI(title="S8Builder Auth API")

# Enable CORS for testing (adjust origins in production)
origins = [
    "http://localhost:5173",  # <-- React dev server origin
    # Add other allowed origins if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,    # Don't just use ["*"] in prod, be specific
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Include auth routes with /api/auth prefix
app.include_router(auth_router, prefix="/api/auth")
app.include_router(booking_router, prefix="/api/bookings")
app.include_router(ws_router, prefix="/api/ws")
@app.get("/")
async def root():
    return {"message": "Welcome to S8Builder Auth API"}

# ✅ DB connectivity check
@app.on_event("startup")
async def startup_db_check():
    try:
        await user_collection.find_one({})
        logging.info("✅ MongoDB connected successfully.")
    except Exception as e:
        logging.error("❌ MongoDB connection failed: %s", e)
