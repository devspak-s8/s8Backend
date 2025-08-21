from datetime import datetime
import traceback
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from bson import ObjectId

from app.database import booking_collection

from app.schemas.bookings import BookingCreate, BookingOut, BookingStatusUpdate
from app.middleware.rbac import get_current_user, is_admin as get_admin_user
from app.routes.ws import broadcast_booking_update
from app.utils.meet_link_and_mail import send_meeting_email

from app.utils.serialize import serialize_doc
booking_router = APIRouter( tags=["Bookings"])


@booking_router.post("/", response_model=BookingOut)
async def create_booking(data: BookingCreate, user=Depends(get_current_user)):
    try:
        new_booking = {
            "booking_id": str(uuid4()),
            "userid": str(user["_id"]), 
            "name": user["name"],
            "email": user["email"],
            "date": data.date,
            "notes": data.notes,
            "status": "pending",
            "meet_link": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        result = await booking_collection.insert_one(new_booking)
        new_booking["id"] = str(result.inserted_id)   # 🟢 Match Pydantic schema
        print("📌 New booking created:", new_booking)

        return new_booking

    except Exception as e:
        print("❌ Booking creation failed:", e)
        traceback.print_exc() 
        raise HTTPException(status_code=500, detail="Booking creation failed")

# Get current user's bookings
@booking_router.get("/my", response_model=List[BookingOut])
async def get_my_bookings(user=Depends(get_current_user)):
    bookings = await booking_collection.find({"user_id": str(user["_id"])}).to_list(100)
    for booking in bookings:
        booking["_id"] = str(booking["_id"])
    return bookings


# Admin: get all bookings
@booking_router.get("/", response_model=List[BookingOut])
async def get_all_bookings(admin=Depends(get_admin_user)):
    bookings = await booking_collection.find({}).to_list(100)
    for booking in bookings:
        booking["_id"] = str(booking["_id"])
    return bookings


# Admin: update booking status
@booking_router.patch("/{booking_id}/status")
async def update_status(booking_id: str, status: BookingStatusUpdate, admin=Depends(get_admin_user)):
    booking = await booking_collection.find_one({"_id": ObjectId(booking_id)})

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    await booking_collection.update_one(
        {"_id": ObjectId(booking_id)},
        {"$set": {"status": status.status}}
    )

    # Send email and attach Meet link if approved
    if status.status.lower() == "approved":
        user_email = booking.get("email") or booking.get("user_email") or "default@example.com"
        meet_link = await send_meeting_email(user_email, booking_id)

        await booking_collection.update_one(
            {"_id": ObjectId(booking_id)},
            {"$set": {"meet_link": meet_link}}
        )

    # Notify connected WebSocket clients
    await broadcast_booking_update({
        "booking_id": booking_id,
        "status": status.status,
    })

    return {"message": "Booking status updated"}
# Get a booking by ID

@booking_router.get("/{booking_id}", response_model=BookingOut)
async def get_booking(booking_id: str, user=Depends(get_current_user)):
    try:
        obj_id = ObjectId(booking_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid booking ID")

    booking = await booking_collection.find_one({"_id": obj_id})

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Optional: check if user is allowed to view
    if booking.get("userid") != str(user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized to view this booking")

    # Serialize entire document and rename _id → id
    booking_serialized = serialize_doc(booking)
    booking_serialized["id"] = booking_serialized.pop("_id")

    return booking_serialized