# app/template_service.py
from app.database import template_collection
from datetime import datetime
from bson import ObjectId

async def create_template_record(template_data: dict) -> str:
    """
    Stores template metadata in MongoDB
    """
    template_data["created_at"] = datetime.utcnow()
    template_data["status"] = "pending"
    result = await template_collection.insert_one(template_data)
    return str(result.inserted_id)

async def update_template_status(template_id: str, status: str, preview_url: str = None):
    """
    Updates template status and preview URL
    """
    update_data = {"status": status}
    if preview_url:
        update_data["preview_url"] = preview_url

    await template_collection.update_one(
        {"_id": ObjectId(template_id)},
        {"$set": update_data}
    )
