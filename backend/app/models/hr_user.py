from datetime import datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field


class HRUser(BaseModel):
    id: str
    company_id: str
    company_name: str
    name: str
    email: EmailStr
    password_hash: str
    role: Literal["admin", "member"] = "member"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HRUserPublic(BaseModel):
    """Safe to return to clients — no password hash."""
    id: str
    company_id: str
    company_name: str
    name: str
    email: EmailStr
    role: str
    created_at: datetime


class RegisterRequest(BaseModel):
    company_name: str
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
