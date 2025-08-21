# app/crud/template_crud.py
from app.database import template_collection
from app.models.template import Template
from bson import ObjectId

# Create template
async def create_template(template: Template):
    template_dict = template.dict()
    result = await template_collection.insert_one(template_dict)
    return str(result.inserted_id)

# Get template by ID
async def get_template(template_id: str):
    template = await template_collection.find_one({"_id": ObjectId(template_id)})
    return template

# Update template status or preview URL
async def update_template(template_id: str, update_data: dict):
    result = await template_collection.update_one(
        {"_id": ObjectId(template_id)},
        {"$set": update_data}
    )
    return result.modified_count

# Get all templates
async def get_all_templates(limit=100):
    templates = await template_collection.find().to_list(limit)
    return templates
