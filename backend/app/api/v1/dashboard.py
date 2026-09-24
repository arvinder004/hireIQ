from fastapi import APIRouter, Depends, Query
from app.db.mongodb import get_db
from app.api.v1.auth import verify_token

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/interviews")
async def list_interviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    position: str | None = None,
    db=Depends(get_db),
    _: dict = Depends(verify_token)
):
    query = {"stage": 3}
    if position:
        query["candidate_data.desired_position"] = {"$regex": position, "$options": "i"}

    skip = (page - 1) * page_size
    cursor = db.interviews.find(query, {"messages": 0}).sort("created_at", -1).skip(skip).limit(page_size)
    items = await cursor.to_list(length=page_size)
    for item in items:
        item["_id"] = str(item["_id"])

    total = await db.interviews.count_documents(query)
    return {"total": total, "page": page, "items": items}


@router.get("/interviews/{interview_id}")
async def get_interview(interview_id: str, db=Depends(get_db), _: dict = Depends(verify_token)):
    from bson import ObjectId
    from fastapi import HTTPException
    doc = await db.interviews.find_one({"_id": ObjectId(interview_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found.")
    doc["_id"] = str(doc["_id"])
    return doc
