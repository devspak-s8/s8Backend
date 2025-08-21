# app/worker.py
import os
import json
import shutil
import zipfile
import time
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import boto3
from app.core.config import settings
from app.template_service import update_template_status

# -----------------------------
# MongoDB setup (async)
# -----------------------------
mongo_client = AsyncIOMotorClient(settings.MONGO_URL)
db = mongo_client.get_default_database()
template_collection = db["templates"]

# -----------------------------
# SQS & S3 clients
# -----------------------------
sqs_client = boto3.client(
    "sqs",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION
)
s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION
)

# -----------------------------
# Local preview folder (temporary)
# -----------------------------
PREVIEW_FOLDER = "./previews"

# -----------------------------
# Helper functions
# -----------------------------
def download_s3_file(s3_key: str, local_path: str):
    s3_client.download_file(settings.BUCKET_NAME, s3_key, local_path)

def extract_zip(zip_path: str, extract_to: str):
    if os.path.exists(extract_to):
        shutil.rmtree(extract_to)
    os.makedirs(extract_to, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def upload_folder_to_s3(folder_path: str, s3_prefix: str):
    """Upload all files in a folder to S3 preserving folder structure."""
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            full_path = os.path.join(root, file)
            relative_path = os.path.relpath(full_path, folder_path)
            s3_key = f"{s3_prefix}/{relative_path.replace(os.sep, '/')}"
            s3_client.upload_file(full_path, settings.BUCKET_NAME, s3_key)

# -----------------------------
# Template processing
# -----------------------------
async def process_template(template_id: str, s3_key: str):
    try:
        print(f"[Worker] Processing template {template_id}")

        # Download ZIP from S3
        zip_local_path = f"/tmp/{os.path.basename(s3_key)}"
        download_s3_file(s3_key, zip_local_path)

        # Extract ZIP locally
        preview_local_path = os.path.join(PREVIEW_FOLDER, template_id)
        extract_zip(zip_local_path, preview_local_path)

        # Upload extracted files to S3 under previews/{template_id}/
        s3_preview_prefix = f"previews/{template_id}"
        upload_folder_to_s3(preview_local_path, s3_preview_prefix)

        # Generate preview URL
        preview_url = f"https://{settings.BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_preview_prefix}/index.html"

        # Update template status in DB
        await update_template_status(template_id, "ready", preview_url)

        # Cleanup
        os.remove(zip_local_path)
        shutil.rmtree(preview_local_path)
        print(f"[Worker] Template {template_id} ready at {preview_url}")

    except Exception as e:
        print(f"[Worker] Error processing template {template_id}: {e}")

# -----------------------------
# Process single SQS message
# -----------------------------
async def process_message(message):
    body = json.loads(message['Body'])
    template_id = body['template_id']
    s3_key = body['s3_key']
    await process_template(template_id, s3_key)

# -----------------------------
# Continuous SQS polling
# -----------------------------
def poll_sqs():
    print("[Worker] Starting SQS polling...")
    loop = asyncio.get_event_loop()
    while True:
        try:
            response = sqs_client.receive_message(
                QueueUrl=settings.SQS_QUEUE_URL,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20
            )
            messages = response.get("Messages", [])
            for msg in messages:
                try:
                    loop.run_until_complete(process_message(msg))
                    # delete after successful processing
                    sqs_client.delete_message(
                        QueueUrl=settings.SQS_QUEUE_URL,
                        ReceiptHandle=msg["ReceiptHandle"]
                    )
                except Exception as e:
                    print(f"[Worker] Error processing message: {e}")
        except Exception as e:
            print(f"[Worker] Error polling SQS: {e}")
            time.sleep(5)

# -----------------------------
# Process stuck templates
# -----------------------------
async def process_stuck_templates():
    stuck_templates = template_collection.find({"status": "pending"})
    async for template in stuck_templates:
        print(f"[Worker] Found stuck template {template['_id']}, processing...")
        await process_template(str(template["_id"]), template["zip_s3_key"])

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    os.makedirs(PREVIEW_FOLDER, exist_ok=True)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(process_stuck_templates())

    poll_sqs()
