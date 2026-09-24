"""
Auth service: password hashing + JWT handling + HR user CRUD.
"""
import uuid
from datetime import datetime, timedelta

import bcrypt
from jose import jwt, JWTError

from app.config import settings
from app.core.logging import log
from app.db.mongodb import get_db
from app.models.hr_user import HRUser, HRUserPublic


# ── Password helpers ─────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── JWT helpers ──────────────────────────────────────────────────────

def create_access_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    payload["exp"] = expire
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


# ── HR User CRUD ─────────────────────────────────────────────────────

async def get_hr_by_email(email: str) -> HRUser | None:
    db = get_db()
    doc = await db.hr_users.find_one({"email": email.lower()})
    if not doc:
        return None
    doc.pop("_id", None)
    return HRUser(**doc)


async def create_hr_user(
    company_name: str,
    name: str,
    email: str,
    password: str,
) -> HRUser:
    db = get_db()
    # Normalise company name into a slug-like ID so all HRs from same company share it
    company_id = company_name.lower().strip().replace(" ", "_")

    user = HRUser(
        id=str(uuid.uuid4()),
        company_id=company_id,
        company_name=company_name.strip(),
        name=name.strip(),
        email=email.lower().strip(),
        password_hash=hash_password(password),
        role="admin",
    )
    await db.hr_users.insert_one(user.model_dump())
    log.info(f"New HR user created: {email} @ {company_name}")
    return user


def to_public(user: HRUser) -> HRUserPublic:
    return HRUserPublic(
        id=user.id,
        company_id=user.company_id,
        company_name=user.company_name,
        name=user.name,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
    )
