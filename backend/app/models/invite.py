from datetime import datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field


class MCQOption(BaseModel):
    key: Literal["A", "B", "C", "D"]
    text: str


class MCQQuestion(BaseModel):
    id: int
    question: str
    options: list[MCQOption]
    correct_answer: Literal["A", "B", "C", "D"]
    topic: str


class CandidateAnswer(BaseModel):
    question_id: int
    selected: Literal["A", "B", "C", "D"]
    is_correct: bool = False


class InterviewInvite(BaseModel):
    id: str
    token: str                      # unique URL token for the candidate
    company_id: str
    company_name: str
    hr_id: str
    hr_name: str

    # Candidate details
    candidate_name: str
    candidate_email: EmailStr
    position: str
    tech_stack: str
    difficulty: Literal["junior", "mid", "senior"] = "mid"
    num_questions: int = 5

    # Interview content
    questions: list[MCQQuestion] = []
    answers: list[CandidateAnswer] = []
    score: int | None = None           # 0–100
    score_breakdown: str | None = None

    # Lifecycle
    status: Literal["generating", "invited", "opened", "in_progress", "completed", "expired", "failed"] = "generating"
    error: str | None = None  # populated if status='failed'
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    opened_at: datetime | None = None
    completed_at: datetime | None = None
    expires_at: datetime | None = None


class CreateInviteRequest(BaseModel):
    candidate_name: str
    candidate_email: EmailStr
    position: str
    tech_stack: str
    difficulty: Literal["junior", "mid", "senior"] = "mid"
    num_questions: int = Field(default=5, ge=3, le=10)


class SubmitAnswersRequest(BaseModel):
    answers: list[dict]   # [{question_id: int, selected: "A"|"B"|"C"|"D"}]
