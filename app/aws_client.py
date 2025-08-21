# app/aws_client.py
import boto3
import json
from app.core.config import settings

# SQS client
sqs_client = boto3.client(
    "sqs",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION
)

def push_template_task(template_id: str, s3_key: str):
    """
    Push template processing task to SQS
    """
    message_body = {
        "template_id": template_id,
        "s3_key": s3_key
    }
    response = sqs_client.send_message(
        QueueUrl=settings.SQS_QUEUE_URL,
        MessageBody=json.dumps(message_body)
    )
    return response
