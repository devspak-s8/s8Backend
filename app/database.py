from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

# Load .env variables
load_dotenv()

# Fetch MongoDB URI
MONGO_URL = os.getenv("MONGO_URL")

# Initialize client
client = AsyncIOMotorClient(MONGO_URL)

# Automatically get the default DB (as long as it's specified in the URL)
db = client.get_default_database()

# Collections
user_collection = db["users"]

booking_collection = db["bookings"]

template_collection = db["templates"]