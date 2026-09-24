"""
Candidate-facing interview API (token-gated, no auth required).
GET  /api/v1/candidate/:token          — load interview
POST /api/v1/candidate/:token/submit   — submit answers
GET  /api/v1/candidate/stream/:company — SSE stream for HR dashboard updates
"""
import json
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core import mcq_service
from app.core.logging import log
from app.db.mongodb import get_db
from app.db.redis import redis_client
from app.models.invite import SubmitAnswersRequest

router = APIRouter(prefix="/candidate", tags=["candidate"])


@router.get("/{token}")
async def get_interview(token: str):
    """Candidate opens the link — return MCQs (without correct answers) and update status."""
    db = get_db()
    doc = await db.invites.find_one({"token": token}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Interview not found. The link may have expired.")

    now = datetime.utcnow()
    expires = doc.get("expires_at")
    if expires and datetime.fromisoformat(str(expires).replace("Z", "")) < now:
        raise HTTPException(status_code=410, detail="This interview link has expired.")

    if doc.get("status") in ("completed",):
        raise HTTPException(status_code=409, detail="This interview has already been completed.")

    # Update status to "opened" if first visit
    if doc.get("status") in ("invited", "generating"):
        await db.invites.update_one(
            {"token": token},
            {"$set": {"status": "opened", "opened_at": now}}
        )
        doc["status"] = "opened"
        # Notify HR dashboard via Redis pub/sub
        await _publish_status_change(doc["company_id"], doc["id"], "opened")

    # Strip correct answers before sending to candidate
    sanitized_questions = []
    for q in doc.get("questions", []):
        sanitized_questions.append({
            "id": q["id"],
            "question": q["question"],
            "topic": q.get("topic", ""),
            "options": q["options"],
        })

    return {
        "id": doc["id"],
        "candidate_name": doc["candidate_name"],
        "position": doc["position"],
        "company_name": doc["company_name"],
        "difficulty": doc["difficulty"],
        "tech_stack": doc.get("tech_stack", "General"),
        "num_questions": doc["num_questions"],
        "status": doc["status"],
        "questions": sanitized_questions,
    }


@router.post("/{token}/submit")
async def submit_answers(token: str, body: SubmitAnswersRequest):
    """Candidate submits answers — score and persist."""
    db = get_db()
    doc = await db.invites.find_one({"token": token}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Interview not found.")
    if doc.get("status") == "completed":
        raise HTTPException(status_code=409, detail="Already submitted.")

    from app.models.invite import MCQQuestion, MCQOption
    questions = [
        MCQQuestion(
            id=q["id"],
            question=q["question"],
            topic=q.get("topic", ""),
            options=[MCQOption(**o) for o in q["options"]],
            correct_answer=q["correct_answer"],
        )
        for q in doc.get("questions", [])
    ]

    score, scored_answers = mcq_service.score_answers(questions, body.answers)
    now = datetime.utcnow()

    await db.invites.update_one(
        {"token": token},
        {"$set": {
            "status": "completed",
            "score": score,
            "answers": [a.model_dump() for a in scored_answers],
            "completed_at": now,
        }}
    )
    log.info(f"Candidate {doc['candidate_email']} scored {score}/100 for {doc['position']}")
    await _publish_status_change(doc["company_id"], doc["id"], "completed", score)

    correct = sum(1 for a in scored_answers if a.is_correct)
    return {
        "score": score,
        "correct": correct,
        "total": len(questions),
        "status": "completed",
    }


@router.get("/stream/{company_id}")
async def dashboard_stream(company_id: str):
    """
    SSE stream — HR dashboard subscribes to get real-time status updates.
    Falls back to a simple keepalive if Redis is unavailable.
    """
    import asyncio

    async def event_generator():
        yield f"data: {json.dumps({'type': 'connected'})}\n\n"

        if redis_client is None:
            # Redis not available — send periodic heartbeats so the connection stays open
            # Dashboard will refresh via its own polling
            while True:
                await asyncio.sleep(30)
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
            return

        try:
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(f"hireiq:updates:{company_id}")
            async for message in pubsub.listen():
                if message["type"] == "message":
                    yield f"data: {message['data']}\n\n"
        except Exception as e:
            log.warning(f"SSE stream error for {company_id}: {e}")
            yield f"data: {json.dumps({'type': 'error'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _publish_status_change(company_id: str, invite_id: str, status: str, score: int | None = None):
    """Publish a status change to the company's Redis channel."""
    try:
        if redis_client:
            payload = json.dumps({"type": "status_update", "invite_id": invite_id, "status": status, "score": score})
            await redis_client.publish(f"hireiq:updates:{company_id}", payload)
    except Exception as e:
        log.warning(f"Redis publish failed: {e}")
