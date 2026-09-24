"""
Interview Invite API — HR-facing.
POST /api/v1/invites          — create invite, generate MCQs, send email
GET  /api/v1/invites          — list all for this company
GET  /api/v1/invites/:id      — single invite with full details
DELETE /api/v1/invites/:id    — cancel invite
"""
import uuid
import asyncio
import json
from datetime import datetime, timedelta


from fastapi import APIRouter, HTTPException, Depends

from app.api.v1.auth import get_current_hr
from app.core import mcq_service, email_service
from app.core.logging import log
from app.db.mongodb import get_db
from app.db.redis import redis_client
from pydantic import BaseModel
from app.models.invite import InterviewInvite, CreateInviteRequest
from app.config import settings

async def _publish_status_change(company_id: str, invite_id: str, status: str):
    """Publish a status change to the company's Redis channel."""
    try:
        if redis_client:
            payload = json.dumps({"type": "status_update", "invite_id": invite_id, "status": status})
            await redis_client.publish(f"hireiq:updates:{company_id}", payload)
    except Exception as e:
        log.warning(f"Redis publish failed: {e}")


class SendEmailRequest(BaseModel):
    subject: str
    body: str
    type: str = "custom"


router = APIRouter(prefix="/invites", tags=["invites"])


@router.post("", status_code=201)
async def create_invite(body: CreateInviteRequest, hr=Depends(get_current_hr)):
    """Generate MCQs, persist invite, send email — all in one shot."""
    db = get_db()
    invite_id = str(uuid.uuid4())
    token = str(uuid.uuid4()).replace("-", "")  # clean URL token

    # Persist with "generating" status first so HR dashboard can show it immediately
    invite = InterviewInvite(
        id=invite_id,
        token=token,
        company_id=hr.company_id,
        company_name=hr.company_name,
        hr_id=hr.id,
        hr_name=hr.name,
        candidate_name=body.candidate_name,
        candidate_email=body.candidate_email,
        position=body.position,
        tech_stack=body.tech_stack,
        difficulty=body.difficulty,
        num_questions=body.num_questions,
        status="generating",
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    await db.invites.insert_one(invite.model_dump())
    log.info(f"Invite {invite_id} created for {body.candidate_email} ({body.position})")

    # Generate MCQs + send email in background so the API responds immediately
    asyncio.create_task(_finalize_invite(invite_id, token, body, hr))

    return {"id": invite_id, "token": token, "status": "generating"}


async def _finalize_invite(invite_id: str, token: str, body: CreateInviteRequest, hr):
    """Background: generate MCQs, update DB, send email."""
    db = get_db()
    try:
        questions = await mcq_service.generate_mcq_questions(
            position=body.position,
            tech_stack=body.tech_stack,
            difficulty=body.difficulty,
            num_questions=body.num_questions,
        )
        interview_url = f"{settings.frontend_url}/interview/{token}"
        email_sent = await email_service.send_interview_invite(
            candidate_name=body.candidate_name,
            candidate_email=body.candidate_email,
            position=body.position,
            company_name=hr.company_name,
            interview_url=interview_url,
            num_questions=body.num_questions,
            difficulty=body.difficulty,
        )
        await db.invites.update_one(
            {"id": invite_id},
            {"$set": {
                "questions": [q.model_dump() for q in questions],
                "status": "invited",
                "sent_at": datetime.utcnow(),
            }}
        )
        if not email_sent:
            log.warning(f"Invite {invite_id} questions generated but email failed to send.")
        else:
            log.info(f"Invite {invite_id} finalised. Email sent to {body.candidate_email}")
            
        await _publish_status_change(hr.company_id, invite_id, "invited")
    except Exception as e:
        log.error(f"Failed to finalise invite {invite_id}: {e}")
        # Mark as failed so the HR dashboard reflects reality
        await db.invites.update_one(
            {"id": invite_id},
            {"$set": {"status": "failed", "error": str(e)}}
        )
        await _publish_status_change(hr.company_id, invite_id, "failed")



@router.get("")
async def list_invites(hr=Depends(get_current_hr)):
    """Return all invites for this HR's company, newest first."""
    db = get_db()
    cursor = db.invites.find(
        {"company_id": hr.company_id},
        {"_id": 0, "questions": 0}   # exclude heavy MCQ data from list view
    ).sort("sent_at", -1)
    return await cursor.to_list(length=200)


@router.get("/{invite_id}")
async def get_invite(invite_id: str, hr=Depends(get_current_hr)):
    db = get_db()
    doc = await db.invites.find_one({"id": invite_id, "company_id": hr.company_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Invite not found.")
    return doc


@router.delete("/{invite_id}", status_code=204)
async def delete_invite(invite_id: str, hr=Depends(get_current_hr)):
    db = get_db()
    result = await db.invites.delete_one({"id": invite_id, "company_id": hr.company_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Invite not found.")

@router.post("/{invite_id}/email", status_code=200)
async def send_custom_invite_email(invite_id: str, body: SendEmailRequest, hr=Depends(get_current_hr)):
    db = get_db()
    doc = await db.invites.find_one({"id": invite_id, "company_id": hr.company_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Invite not found.")
    
    success = await email_service.send_custom_email(
        to_email=doc["candidate_email"],
        subject=body.subject,
        body=body.body,
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email. Check SMTP configuration.")
        
    if body.type == "rejection":
        await db.invites.update_one({"id": invite_id}, {"$set": {"status": "archived"}})
        
    return {"message": "Email sent successfully"}

@router.post("/{invite_id}/archive", status_code=200)
async def archive_invite(invite_id: str, hr=Depends(get_current_hr)):
    db = get_db()
    result = await db.invites.update_one(
        {"id": invite_id, "company_id": hr.company_id},
        {"$set": {"status": "archived"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Invite not found.")
    return {"message": "Candidate archived"}


