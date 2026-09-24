from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings
from app.core.logging import log


class MongoDB:
    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None


mongodb = MongoDB()


async def connect_mongo():
    log.info(f"Connecting to MongoDB (db={settings.mongo_db_name})…")
    mongodb.client = AsyncIOMotorClient(settings.mongo_uri)
    mongodb.db = mongodb.client[settings.mongo_db_name]
    await mongodb.client.admin.command("ping")
    log.info("MongoDB ping OK — connection is live.")
    try:
        # HR users
        await mongodb.db.hr_users.create_index("email", unique=True)
        await mongodb.db.hr_users.create_index("company_id")
        # Interview invites
        await mongodb.db.invites.create_index("token", unique=True)
        await mongodb.db.invites.create_index("company_id")
        await mongodb.db.invites.create_index([("sent_at", -1)])
        await mongodb.db.invites.create_index("status")
        log.info("MongoDB indexes ensured.")
    except Exception as e:
        log.warning(f"Index creation skipped (non-fatal): {e}")


async def disconnect_mongo():
    if mongodb.client:
        mongodb.client.close()
        log.info("MongoDB disconnected.")


def get_db() -> AsyncIOMotorDatabase:
    if mongodb.db is None:
        raise RuntimeError("MongoDB is not connected.")
    return mongodb.db
