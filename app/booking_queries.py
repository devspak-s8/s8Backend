# app/database/booking_queries.py

from app.database import booking_collection
from bson import ObjectId

async def get_booking_summary(user_id: str):
    pipeline = [
        {"$match": {"userid": user_id}},  # note: you used "userid" in booking doc
        {
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }
        }
    ]
    results = await booking_collection.aggregate(pipeline).to_list(length=None)

    summary = {
        "pending": 0,
        "approved": 0,
        "rejected": 0,
        "total_bookings": 0
    }
    for r in results:
        status = r["_id"]
        count = r["count"]
        summary[status] = count
        summary["total_bookings"] += count

    return summary

async def get_recent_bookings(user_id: str, limit: int = 5):
    bookings = await booking_collection.find({"userid": user_id}).sort("created_at", -1).limit(limit).to_list(length=limit)
    for booking in bookings:
        booking["id"] = str(booking["_id"])
    return bookings
