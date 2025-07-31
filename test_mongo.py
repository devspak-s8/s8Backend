import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import certifi
import os

async def test_connection():
    MONGO_URL = os.getenv("MONGO_URL")
    client = AsyncIOMotorClient(MONGO_URL, tlsCAFile=certifi.where())
    try:
        result = await client.admin.command("ping")
        print("✅ MongoDB connected:", result)
    except Exception as e:
        print("❌ MongoDB connection failed:", e)

if __name__ == "__main__":
    asyncio.run(test_connection())
