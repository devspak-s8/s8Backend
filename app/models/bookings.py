from app.database import db
from bson import ObjectId
from datetime import datetime

booking_collection = db.bookings

async def create_booking(data):
    result = await booking_collection.insert_one(data)
    return str(result.inserted_id)

async def get_user_bookings(user_id):
    bookings = await booking_collection.find({"user_id": user_id}).to_list(100)
    return bookings

async def get_all_bookings():
    bookings = await booking_collection.find({}).to_list(100)
    return bookings

async def update_booking_status(booking_id, status):
    result = await booking_collection.update_one(
        {"_id": ObjectId(booking_id)},
        {"$set": {"status": status}}
    )
    return result.modified_count
