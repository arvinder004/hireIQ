import redis.asyncio as aioredis
from app.config import settings
from app.models.interview import InterviewSession
from app.core.logging import log

redis_client: aioredis.Redis | None = None
SESSION_TTL = 60 * 60 * 24   # 24 hours


async def connect_redis():
    global redis_client
    log.info(f"Connecting to Redis ({settings.redis_url.split('@')[-1]})…")
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)

    # Verify connection with a PING
    pong = await redis_client.ping()
    if pong:
        log.info("Redis ping OK — connection is live.")
    else:
        raise ConnectionError("Redis PING returned unexpected response.")


async def disconnect_redis():
    if redis_client:
        await redis_client.close()
        log.info("Redis disconnected.")


async def get_session(session_id: str) -> InterviewSession | None:
    if redis_client is None:
        log.error("Redis not connected — cannot retrieve session.")
        return None
    try:
        data = await redis_client.get(f"session:{session_id}")
        if not data:
            log.debug(f"Session {session_id!r} not found in Redis.")
            return None
        return InterviewSession.model_validate_json(data)
    except Exception as e:
        log.error(f"Failed to load session {session_id!r} from Redis: {e}")
        return None


async def save_session(session: InterviewSession) -> None:
    if redis_client is None:
        log.error("Redis not connected — cannot save session.")
        return
    try:
        await redis_client.setex(
            f"session:{session.session_id}",
            SESSION_TTL,
            session.model_dump_json()
        )
        log.debug(f"Session {session.session_id!r} saved (stage={session.stage}).")
    except Exception as e:
        log.error(f"Failed to save session {session.session_id!r} to Redis: {e}")


async def delete_session(session_id: str) -> None:
    if redis_client is None:
        return
    try:
        await redis_client.delete(f"session:{session_id}")
        log.info(f"Session {session_id!r} deleted from Redis.")
    except Exception as e:
        log.warning(f"Failed to delete session {session_id!r} from Redis: {e}")
