from app.database import db
from bson import ObjectId
from app.utils.serialize import serialize_doc, serialize_list  # your code

booking_collection = db.bookings

async def create_booking(data):
    result = await booking_collection.insert_one(data)
    booking = await booking_collection.find_one({"_id": result.inserted_id})
    return serialize_doc(booking)

async def get_user_bookings(user_id):
    bookings = await booking_collection.find({"user_id": user_id}).to_list(100)
    return serialize_list(bookings)

async def get_all_bookings():
    bookings = await booking_collection.find({}).to_list(100)
    return serialize_list(bookings)

async def update_booking_status(booking_id, status):
    result = await booking_collection.update_one(
        {"_id": ObjectId(booking_id)},
        {"$set": {"status": status}}
    )
    if result.modified_count:
        booking = await booking_collection.find_one({"_id": ObjectId(booking_id)})
        return serialize_doc(booking)
    return None
