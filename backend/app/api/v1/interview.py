import uuid
import json
import traceback
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.logging import log
from app.db.redis import get_session, save_session, delete_session
from app.db.mongodb import get_db
from app.models.interview import InterviewSession, InterviewStage
from app.core.interview_engine import InterviewEngine
from app.core import llm_service

router = APIRouter(prefix="/interview", tags=["interview"])


class CreateSessionResponse(BaseModel):
    session_id: str
    greeting: str


class SendMessageRequest(BaseModel):
    session_id: str
    message: str


@router.post("/session", response_model=CreateSessionResponse)
async def create_session():
    """Creates a new interview session."""
    try:
        session_id = str(uuid.uuid4())
        session = InterviewSession(session_id=session_id)
        await save_session(session)
        log.info(f"New interview session created: {session_id!r}")
        greeting = (
            "Welcome to TalentScout! 👋\n\n"
            "I'm your AI interviewer. I'll guide you through a short screening — "
            "first some basic details, then a few technical questions based on your skills.\n\n"
            "**What's your full name?**"
        )
        return CreateSessionResponse(session_id=session_id, greeting=greeting)
    except Exception as e:
        log.error(f"Failed to create session: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Could not create session: {e}")


@router.post("/message")
async def send_message(body: SendMessageRequest):
    """
    Sends a candidate message and streams back the AI response via SSE.

    Stream format:
      data: {"chunk": "word "}              ← text chunk
      data: {"done": true, "stage": 2}      ← final event
      data: {"error": "message"}            ← if something goes wrong mid-stream
    """
    session = await get_session(body.session_id)
    if not session:
        log.warning(f"send_message: session {body.session_id!r} not found.")
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    engine = InterviewEngine(session)

    async def generate():
        try:
            updated_session, reply = await engine.process_message(body.message)
            log.info(
                f"[{body.session_id[:8]}] stage={updated_session.stage} "
                f"reply_len={len(reply)} chars"
            )
            await save_session(updated_session)

            # Stream reply word-by-word
            words = reply.split(" ")
            for i, word in enumerate(words):
                chunk = word + ("" if i == len(words) - 1 else " ")
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"

            # Persist completed interview to MongoDB
            if updated_session.stage == InterviewStage.COMPLETED:
                try:
                    db = get_db()
                    scored_qa = await llm_service.score_technical_answers(
                        updated_session.candidate_data.tech_stack,
                        [qa.model_dump() for qa in updated_session.technical_qa]
                    )
                    doc = updated_session.model_dump()
                    doc["technical_qa"] = scored_qa
                    doc["finalized_at"] = datetime.utcnow().isoformat()
                    await db.interviews.insert_one(doc)
                    await delete_session(updated_session.session_id)
                    log.info(f"Interview {body.session_id!r} finalised and saved to MongoDB.")
                except Exception as db_err:
                    log.error(
                        f"Failed to persist interview {body.session_id!r}: {db_err}\n"
                        f"{traceback.format_exc()}"
                    )
                    # Don't break the stream — candidate already got the closing message

            yield f"data: {json.dumps({'done': True, 'stage': int(updated_session.stage)})}\n\n"

        except Exception as e:
            log.error(
                f"Stream error for session {body.session_id!r}: {e}\n"
                f"{traceback.format_exc()}"
            )
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@router.get("/session/{session_id}")
async def get_session_state(session_id: str):
    """Fetch session state — used to resume after a browser refresh."""
    session = await get_session(session_id)
    if not session:
        log.debug(f"get_session_state: {session_id!r} not found.")
        raise HTTPException(status_code=404, detail="Session not found.")
    return session
