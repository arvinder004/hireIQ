from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings

class MongoDB: 
    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None

mongodb = MongoDB()

async def connect_mongo():
    mongodb.client = AsyncIOMotorClient(settings.mongo_uri)
    mongodb.db = mongodb.client[settings.mongo_db_name]
    
    # Create indexes once at startup
    await mongodb.db.interviews.create_index("candidate_data.email")
    await mongodb.db.interviews.create_index([("created_at", -1)])
    await mongodb.db.interviews.create_index("status")
    
    # TTL: auto-delete records after 90 days
    await mongodb.db.interviews.create_index("created_at", expire_after_seconds=7776000)
    
    print("MongoDB Connected")

async def disconnect_mongo():
    if mongodb.client:
        mongodb.client.close()
        print("MongoDB disconnected")

def get_db() -> AsyncIOMotorDatabase:
    return mongodb.db
