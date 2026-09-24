import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import log
from app.config import settings
from app.db.mongodb import connect_mongo, disconnect_mongo
from app.db.redis import connect_redis, disconnect_redis
from app.api.v1 import auth, invites, candidate


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting HireIQ backend…")
    try:
        await connect_mongo()
    except Exception as e:
        log.critical(f"MongoDB connection FAILED: {e}")
        raise
    try:
        await connect_redis()
    except Exception as e:
        log.warning(f"Redis connection FAILED: {e}. Real-time updates disabled.")
    log.info("All services connected. Application ready.")
    yield
    log.info("Shutting down HireIQ backend…")
    await disconnect_mongo()
    await disconnect_redis()


app = FastAPI(
    title="HireIQ API",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    log.error(f"Unhandled exception on {request.method} {request.url.path}\n{tb}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Server error.", "error": type(exc).__name__, "message": str(exc)},
    )


app.include_router(auth.router, prefix="/api/v1")
app.include_router(invites.router, prefix="/api/v1")
app.include_router(candidate.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}
