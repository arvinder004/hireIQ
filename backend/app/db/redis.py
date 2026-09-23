import redis.asyncio as aioredis
from app.config import settings
from app.models.interview import InterviewSession

redis_client: aioredis.Redis | None = None
SESSION_TTL = 60 * 60 * 24

async def connect_redis():
    global redis_client
    
    # from_url lets you pass the single connection string 
    # instead of individual host, port, username, and password
    redis_client = aioredis.from_url(
        settings.redis_url, 
        decode_responses=True
    )
    print("Redis connected")

async def disconnect_redis():
    if redis_client:
        await redis_client.close()
        print("Redis disconnected")

async def get_session(session_id: str) -> InterviewSession | None:
    if not data:
        return None
    return InterviewSession.model_validate_json(data)

async def save_session(session: InterviewSession) -> None:
    await redis_client.setex(f"session:{session.session_id}", SESSION_TTL, session.model_dump_json())

async def delete_session(session_id: str) -> None:
    await redis_client.delete(f"session:{session_id}")


