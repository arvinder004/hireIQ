from datetime import datetime
from enum import IntEnum
from typing import Literal
from pydantic import BaseModel, Field, EmailStr

class InterviewStage(IntEnum):
    INFO_GATHERING = 1
    TECHNICAL = 2
    COMPLETED = 3

class CandidateData(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None   
    years_experience: int | None = None
    desired_position: str | None = None
    location: str | None = None
    tech_stack: str | None = None

class TechnicalQA(BaseModel):
    question_number: int
    question: str
    answer: str | None = None
    score: int | None = None
    score_rationale: str | None = None 

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class InterviewSession(BaseModel):
    """
    Complete state of one interview. Stored in Redis while active, moved to MongoDB on completion.
    """
    session_id: str
    stage: InterviewStage.INFO_GATHERING
    candidate_data: CandidateData = Field(default_factory=CandidateData)
    current_field: str = "name"
    current_question: str | None = None
    confirmation_pending: bool = False
    question_count: int = 0
    technical_qa: list[TechnicalQA] = []
    messages: list[Message] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    