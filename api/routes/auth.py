import re
import hashlib
import time
from collections import defaultdict
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

from api.middleware.auth import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, revoke_refresh_token, revoke_all_user_tokens,
    get_current_user
)
from api.middleware.audit import log_audit
from utils.encryption import encrypt_sql, get_encryption_params
from db.session import async_session
from config import get_settings

router = APIRouter(prefix="/api/auth", tags=["auth"])

_users_store = {}
_rate_limit_store = defaultdict(list)
_refresh_tokens_store = {}
_otp_store = {}

# DEMO SEED — remove when Azure + DB available
from db.seed_demo import DEMO_USER_ID, DEMO_EMAIL, DEMO_PASSWORD, RAMESH_PROFILE
_users_store[DEMO_USER_ID] = {
    "id": DEMO_USER_ID,
    "name": RAMESH_PROFILE["name"],
    "email": DEMO_EMAIL,
    "password_hash": hash_password(DEMO_PASSWORD),
    "phone_number": RAMESH_PROFILE["phone_number"],
    "tier": RAMESH_PROFILE["tier"],
    "date_of_birth": RAMESH_PROFILE["date_of_birth"],
    "gender": RAMESH_PROFILE["gender"],
    "city": RAMESH_PROFILE["city"],
    "state": RAMESH_PROFILE["state"],
    "preferred_language": RAMESH_PROFILE["preferred_language"],
    "medical_literacy_level": RAMESH_PROFILE["medical_literacy_level"],
    "onboarding_completed_at": RAMESH_PROFILE["onboarding_completed_at"],
}
# END DEMO SEED


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    phone_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    preferred_language: Optional[str] = "en"


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class VerifyOTPRequest(BaseModel):
    phone_number: str
    otp_code: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _check_rate_limit(ip: str) -> bool:
    settings = get_settings()
    now = time.time()
    cutoff = now - settings.RATE_LIMIT_COOLDOWN_SECONDS
    _rate_limit_store[ip] = [t for t in _rate_limit_store[ip] if t > cutoff]
    return len(_rate_limit_store[ip]) >= settings.RATE_LIMIT_MAX_FAILURES


def _record_failure(ip: str):
    _rate_limit_store[ip].append(time.time())


def _validate_password(password: str):
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if not re.search(r'[a-zA-Z]', password):
        raise HTTPException(status_code=400, detail="Password must contain letters")
    if not re.search(r'\d', password):
        raise HTTPException(status_code=400, detail="Password must contain numbers")


def _store_refresh_token(raw_token: str, user_id: str):
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    _refresh_tokens_store[token_hash] = {
        "user_id": user_id,
        "revoked": False,
    }


def _validate_refresh_token(raw_token: str) -> dict:
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    entry = _refresh_tokens_store.get(token_hash)
    if not entry or entry.get("revoked"):
        return None
    return entry


def _revoke_local_token(raw_token: str):
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    if token_hash in _refresh_tokens_store:
        _refresh_tokens_store[token_hash]["revoked"] = True


def _revoke_all_local_tokens(user_id: str):
    for entry in _refresh_tokens_store.values():
        if entry["user_id"] == user_id:
            entry["revoked"] = True


@router.post("/register")
async def register(body: RegisterRequest, request: Request):
    _validate_password(body.password)

    for user in _users_store.values():
        if user["email"] == body.email:
            raise HTTPException(status_code=409, detail="Email already registered")

    user_id = str(uuid4())
    hashed = hash_password(body.password)

    _users_store[user_id] = {
        "id": user_id,
        "name": body.name,
        "email": body.email,
        "password_hash": hashed,
        "phone_number": body.phone_number,
        "tier": "free",
        "date_of_birth": body.date_of_birth,
        "gender": body.gender,
        "city": body.city,
        "state": body.state,
        "preferred_language": body.preferred_language,
        "medical_literacy_level": None,
        "onboarding_completed_at": None,
    }

    params = get_encryption_params({
        "uid": user_id,
        "name": body.name,
        "email": body.email,
        "phone": body.phone_number,
    })

    async with async_session() as session:
        await session.execute(
            "SELECT id FROM users WHERE email = :email",
            {"email": body.email}
        )
        await session.execute(
            "INSERT INTO users (id, name, email, phone_number, password_hash) "
            "VALUES (:uid, pgp_sym_encrypt(:name, :encryption_key), :email, :phone, :pwd)",
            {**params, "pwd": hashed}
        )
        await session.commit()

    access_token = create_access_token(user_id)
    ip = _get_client_ip(request)
    refresh_token = await create_refresh_token(user_id, ip_address=ip)
    _store_refresh_token(refresh_token, user_id)

    await log_audit(user_id, user_id, "REGISTER", request)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {"id": user_id, "name": body.name, "email": body.email, "onboarding_complete": False},
    }


@router.post("/login")
async def login(body: LoginRequest, request: Request):
    ip = _get_client_ip(request)

    if _check_rate_limit(ip):
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")

    user = None
    for u in _users_store.values():
        if u["email"] == body.email:
            user = u
            break

    if not user:
        _record_failure(ip)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(body.password, user["password_hash"]):
        _record_failure(ip)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(user["id"])
    refresh_token = await create_refresh_token(user["id"], ip_address=ip)
    _store_refresh_token(refresh_token, user["id"])

    await log_audit(user["id"], user["id"], "LOGIN", request)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "name": user.get("name"),
            "email": user["email"],
            "onboarding_complete": all(user.get(f) for f in ("date_of_birth", "gender", "preferred_language", "medical_literacy_level")),
        },
    }


@router.post("/refresh")
async def refresh(body: RefreshRequest):
    entry = _validate_refresh_token(body.refresh_token)

    if not entry:
        raise HTTPException(status_code=401, detail="Invalid or revoked refresh token")

    user_id = entry["user_id"]

    _revoke_local_token(body.refresh_token)
    await revoke_refresh_token(body.refresh_token)

    new_access = create_access_token(user_id)
    new_refresh = await create_refresh_token(user_id)
    _store_refresh_token(new_refresh, user_id)

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(body: LogoutRequest, request: Request):
    _revoke_local_token(body.refresh_token)
    await revoke_refresh_token(body.refresh_token)
    return {"status": "logged_out"}


@router.post("/change-password")
async def change_password(body: ChangePasswordRequest, request: Request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    current_user = await get_current_user(request)

    _validate_password(body.new_password)

    user = _users_store.get(current_user["id"])
    if user and not verify_password(body.current_password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    new_hash = hash_password(body.new_password)
    if user:
        user["password_hash"] = new_hash

    _revoke_all_local_tokens(current_user["id"])
    await revoke_all_user_tokens(current_user["id"])

    return {"status": "password_changed"}


@router.post("/verify-otp")
async def verify_otp(body: VerifyOTPRequest):
    otp_entry = _otp_store.get(body.phone_number)

    if not otp_entry:
        raise HTTPException(status_code=400, detail="No pending OTP for this phone number")

    if otp_entry.get("expired", False) or (
        time.time() - otp_entry.get("created_at", 0) > 300
    ):
        raise HTTPException(status_code=410, detail="OTP has expired. Please request a new one.")

    if otp_entry.get("code") != body.otp_code:
        raise HTTPException(status_code=401, detail="Invalid OTP code")

    del _otp_store[body.phone_number]

    user_id = otp_entry.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="OTP session invalid")

    access_token = create_access_token(user_id)
    refresh_token = await create_refresh_token(user_id)
    _store_refresh_token(refresh_token, user_id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "verified": True,
    }
