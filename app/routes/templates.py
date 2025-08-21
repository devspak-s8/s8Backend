# app/routes/templates.py
import os
import aiofiles
from uuid import uuid4
from fastapi import APIRouter, UploadFile, Form, File, Depends, HTTPException, Path
from datetime import datetime
import boto3
from bson import ObjectId

from app.core.config import settings
from app.aws_client import push_template_task
from app.template_service import create_template_record
from app.models.template import Template
from app.database import template_collection
from app.utils.serialize import serialize_list
from app.middleware.rbac import get_current_user  # 🔑 Auth

template_router = APIRouter(tags=["Templates"])

# -----------------------------
# S3 client
# -----------------------------
s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION
)

# -----------------------------
# Helper to upload to S3
# -----------------------------
async def upload_file_to_s3(file: UploadFile, folder="templates"):
    file_ext = os.path.splitext(file.filename)[1]
    file_key = f"{folder}/{uuid4()}{file_ext}"

    temp_path = f"/tmp/{uuid4()}{file_ext}"
    async with aiofiles.open(temp_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    s3_client.upload_file(temp_path, settings.BUCKET_NAME, file_key)
    os.remove(temp_path)  # cleanup

    s3_url = f"https://{settings.BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{file_key}"
    return file_key, s3_url

# -----------------------------
# Upload template route
# -----------------------------
@template_router.post("/upload-template")
async def upload_template(
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    tags: str = Form(...),
    zip_file: UploadFile = File(...),
    images: list[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user)   # 👈 fetch user
):
    if not zip_file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only ZIP files allowed.")

    # Upload ZIP
    zip_key, zip_url = await upload_file_to_s3(zip_file)

    # Upload images
    image_urls = []
    for image in images:
        _, img_url = await upload_file_to_s3(image, folder="images")
        image_urls.append(img_url)

    # Build Template model (no raw dicts, private by default)
    template = Template(
        title=title,
        description=description,
        category=category,
        tags=[t.strip() for t in tags.split(",") if t.strip()],
        zip_s3_key=zip_key,
        images=image_urls,
        uploaded_by=str(current_user["_id"]),  # 👈 real user ID from auth
        status="pending",
        is_public=False  # enforce private
    )

    # Store in MongoDB
    template_id = await create_template_record(template.dict())

    # Push to SQS
    push_template_task(template_id, template.zip_s3_key)

    return {
        "message": "Template uploaded successfully.",
        "template_id": template_id,
        "zip_url": zip_url,
        "image_urls": image_urls
    }

# -----------------------------
# Get current user's templates
# -----------------------------
@template_router.get("/my-templates")
async def get_my_templates(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    templates_cursor = template_collection.find({"uploaded_by": user_id}).sort("created_at", -1)
    templates = await templates_cursor.to_list(length=100)
    return serialize_list(templates)


@template_router.get("/my-templates/{template_id}")
async def get_my_template_by_id(
    template_id: str = Path(...),
    current_user: dict = Depends(get_current_user)
):
    # Fetch template belonging to current user
    template = await template_collection.find_one({
        "_id": ObjectId(template_id),
        "uploaded_by": str(current_user["_id"])
    })

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Convert ObjectId to string for frontend
    template["_id"] = str(template["_id"])

    # Ensure preview_url is included even if not yet processed
    template["preview_url"] = template.get("preview_url")  # could be None if still processing

    return template