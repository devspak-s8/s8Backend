from app.database import user_collection, booking_collection, template_collection
from bson import ObjectId
from app.utils.serialize import serialize_doc

async def get_dashboard_overview(user_id: str):
    user_obj_id = ObjectId(user_id)

    # ---------------------
    # User info
    # ---------------------
    user = await user_collection.find_one({"_id": user_obj_id}, {"password": 0})

    # ---------------------
    # Recent bookings
    # ---------------------
    recent_bookings_cursor = booking_collection.find(
        {"userid": str(user_obj_id)}
    ).sort("date", -1).limit(5)  # your collection stores "date" not "bookingDate"
    recent_bookings_raw = await recent_bookings_cursor.to_list(length=5)

    recent_bookings = []
    for b in recent_bookings_raw:
        recent_bookings.append({
            "_id": str(b.get("_id")),  # React key / Booking ID
            "bookingDate": b.get("date").isoformat() if hasattr(b.get("date"), "isoformat") else b.get("date"),
            "userName": b.get("name", "N/A"),
            "userid": b.get("userid"),
            "status": b.get("status", "pending"),
            "notes": b.get("notes", ""),
            "meet_link": b.get("meet_link", None)
        })

    # ---------------------
    # Recent templates
    # ---------------------
    recent_templates_cursor = template_collection.find(
        {"uploaded_by": str(user_obj_id)}
    ).sort("created_at", -1).limit(5)
    recent_templates_raw = await recent_templates_cursor.to_list(length=5)

    recent_templates = []
    for t in recent_templates_raw:
        recent_templates.append({
            "_id": str(t.get("_id")),
            "title": t.get("title", t.get("name", "Untitled")),  # depending on your schema
            "author": t.get("author", "N/A"),
            "downloads": t.get("downloads", 0),
            "rating": t.get("rating", 0)
        })

    # ---------------------
    # Analytics
    # ---------------------
    total_templates = await template_collection.count_documents({"uploaded_by": str(user_obj_id)})
    total_bookings = await booking_collection.count_documents({"userid": str(user_obj_id)})
    total_users = await user_collection.count_documents({})
    earnings = 0  # replace with real logic if needed

    dashboard_data = {
        "user": user,
        "recentBookings": recent_bookings,
        "recentTemplates": recent_templates,
        "analytics": {
            "totalTemplates": total_templates,
            "totalBookings": total_bookings,
            "totalUsers": total_users,
            "earnings": earnings,
        }
    }

    # ---------------------
    # Serialize ObjectIds for React
    # ---------------------
    return serialize_doc(dashboard_data)
