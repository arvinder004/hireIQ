"""
HR Authentication API.
POST /api/v1/auth/register  — create account
POST /api/v1/auth/login     — get JWT
GET  /api/v1/auth/me        — current user
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core import auth_service
from app.core.logging import log
from app.models.hr_user import RegisterRequest, LoginRequest, HRUserPublic

router = APIRouter(prefix="/auth", tags=["auth"])
_bearer = HTTPBearer()


async def get_current_hr(creds: HTTPAuthorizationCredentials = Depends(_bearer)) -> HRUserPublic:
    payload = auth_service.decode_access_token(creds.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    user = await auth_service.get_hr_by_email(payload.get("sub", ""))
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")
    return auth_service.to_public(user)


@router.post("/register")
async def register(body: RegisterRequest):
    existing = await auth_service.get_hr_by_email(body.email)
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    user = await auth_service.create_hr_user(
        company_name=body.company_name,
        name=body.name,
        email=body.email,
        password=body.password,
    )
    token = auth_service.create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer", "user": auth_service.to_public(user)}


@router.post("/login")
async def login(body: LoginRequest):
    user = await auth_service.get_hr_by_email(body.email)
    if not user or not auth_service.verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token = auth_service.create_access_token({"sub": user.email})
    log.info(f"HR login: {body.email}")
    return {"access_token": token, "token_type": "bearer", "user": auth_service.to_public(user)}


@router.get("/me", response_model=HRUserPublic)
async def me(hr=Depends(get_current_hr)):
    return hr
