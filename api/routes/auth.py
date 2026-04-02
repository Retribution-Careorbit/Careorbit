import re
import hashlib
import time
import logging
import secrets
from urllib.parse import urlencode
from collections import defaultdict
from uuid import uuid4

import httpx
import jwt as pyjwt
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
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
logger = logging.getLogger("careorbit.auth.routes")

_users_store = {}
_rate_limit_store = defaultdict(list)
_refresh_tokens_store = {}
_otp_store = {}
_entra_state_store = {}
_entra_exchange_store = {}
_entra_openid_cache = {"fetched_at": 0.0, "data": None}

# DEMO SEED — remove when Azure + DB available
from db.seed_demo import (
    DEMO_USER_ID,
    DEMO_EMAIL,
    DEMO_PASSWORD,
    RAMESH_PROFILE,
    FATHER_USER_ID,
    FATHER_EMAIL,
    FATHER_PASSWORD,
    FATHER_PROFILE,
)


def _seed_user_record(user_id: str, profile: dict, email: str, password: str):
    _users_store[user_id] = {
        "id": user_id,
        "name": profile["name"],
        "email": email,
        "password_hash": hash_password(password),
        "phone_number": profile.get("phone_number"),
        "tier": profile.get("tier", "free"),
        "date_of_birth": profile.get("date_of_birth"),
        "gender": profile.get("gender"),
        "city": profile.get("city"),
        "state": profile.get("state"),
        "preferred_language": profile.get("preferred_language", "en"),
        "medical_literacy_level": profile.get("medical_literacy_level"),
        "onboarding_completed_at": profile.get("onboarding_completed_at"),
    }


_seed_user_record(DEMO_USER_ID, RAMESH_PROFILE, DEMO_EMAIL, DEMO_PASSWORD)
_seed_user_record(FATHER_USER_ID, FATHER_PROFILE, FATHER_EMAIL, FATHER_PASSWORD)
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


class EntraExchangeRequest(BaseModel):
    exchange_code: str


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


def _entera_settings_or_503():
    settings = get_settings()
    if not settings.ENTRA_ENABLED:
        raise HTTPException(status_code=503, detail="Entra authentication is not enabled")
    if not settings.ENTRA_CLIENT_ID or not settings.ENTRA_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Entra auth is missing client credentials")
    if not settings.ENTRA_REDIRECT_URI:
        raise HTTPException(status_code=503, detail="Entra redirect URI is not configured")
    return settings


def _purge_expired_entra_state(now: float):
    expired = [k for k, v in _entra_state_store.items() if (now - v.get("created_at", 0)) > 600]
    for key in expired:
        _entra_state_store.pop(key, None)


def _purge_expired_entra_exchange(now: float):
    expired = [k for k, v in _entra_exchange_store.items() if (now - v.get("created_at", 0)) > 180]
    for key in expired:
        _entra_exchange_store.pop(key, None)


async def _get_entra_openid_config(settings):
    now = time.time()
    cached = _entra_openid_cache.get("data")
    if cached and (now - _entra_openid_cache.get("fetched_at", 0)) < 3600:
        return cached

    if settings.ENTRA_OPENID_CONFIG_URL:
        config_url = settings.ENTRA_OPENID_CONFIG_URL
    elif settings.ENTRA_TENANT_ID:
        config_url = f"https://login.microsoftonline.com/{settings.ENTRA_TENANT_ID}/v2.0/.well-known/openid-configuration"
    else:
        raise HTTPException(status_code=503, detail="Set ENTRA_OPENID_CONFIG_URL or ENTRA_TENANT_ID")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(config_url)
            response.raise_for_status()
            data = response.json()
    except Exception as exc:
        logger.error(f"Failed to load Entra OIDC config: {exc}")
        raise HTTPException(status_code=502, detail="Unable to load Entra OpenID configuration")

    _entra_openid_cache["fetched_at"] = now
    _entra_openid_cache["data"] = data
    return data


def _validate_entra_id_token(id_token: str, jwks_uri: str, issuer: str, audience: str) -> dict:
    try:
        signing_key = pyjwt.PyJWKClient(jwks_uri).get_signing_key_from_jwt(id_token)
        claims = pyjwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=audience,
            issuer=issuer,
            options={"require": ["exp", "iat", "iss", "aud"]},
        )
        return claims
    except Exception as exc:
        logger.warning(f"Entra ID token validation failed: {exc}")
        raise HTTPException(status_code=401, detail="Invalid Entra identity token")


def _hint_for_provider(settings, provider: str) -> str:
    if provider == "google":
        return settings.ENTRA_GOOGLE_DOMAIN_HINT
    if provider == "apple":
        return settings.ENTRA_APPLE_DOMAIN_HINT
    return ""


def _normalize_provider(value: str) -> str:
    provider = (value or "microsoft").strip().lower()
    if provider not in {"microsoft", "google", "apple"}:
        raise HTTPException(status_code=400, detail="provider must be one of: microsoft, google, apple")
    return provider


def _upsert_social_user(claims: dict, provider: str) -> dict:
    email = claims.get("email") or claims.get("preferred_username")
    if not email:
        raise HTTPException(status_code=400, detail="Email claim missing from Entra token")

    existing_user = None
    for user in _users_store.values():
        if user.get("email", "").lower() == email.lower():
            existing_user = user
            break

    display_name = claims.get("name") or email.split("@")[0]
    external_sub = claims.get("oid") or claims.get("sub") or str(uuid4())

    if existing_user:
        existing_user["name"] = existing_user.get("name") or display_name
        existing_user["ent_provider"] = provider
        existing_user["ent_sub"] = external_sub
        return existing_user

    user_id = str(uuid4())
    generated_password = secrets.token_urlsafe(24)
    user = {
        "id": user_id,
        "name": display_name,
        "email": email,
        "password_hash": hash_password(generated_password),
        "phone_number": None,
        "tier": "free",
        "date_of_birth": None,
        "gender": None,
        "city": None,
        "state": None,
        "preferred_language": "en",
        "medical_literacy_level": None,
        "onboarding_completed_at": None,
        "ent_provider": provider,
        "ent_sub": external_sub,
    }
    _users_store[user_id] = user
    return user


@router.get("/entra/login")
async def entra_login(provider: str = "microsoft"):
    settings = _entera_settings_or_503()
    normalized_provider = _normalize_provider(provider)
    oidc = await _get_entra_openid_config(settings)

    state = secrets.token_urlsafe(24)
    nonce = secrets.token_urlsafe(24)
    now = time.time()
    _purge_expired_entra_state(now)
    _entra_state_store[state] = {
        "provider": normalized_provider,
        "nonce": nonce,
        "created_at": now,
    }

    params = {
        "client_id": settings.ENTRA_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.ENTRA_REDIRECT_URI,
        "response_mode": "query",
        "scope": settings.ENTRA_SCOPES,
        "state": state,
        "nonce": nonce,
    }

    provider_hint = _hint_for_provider(settings, normalized_provider)
    if provider_hint:
        params["domain_hint"] = provider_hint

    authorization_url = f"{oidc['authorization_endpoint']}?{urlencode(params)}"
    return RedirectResponse(url=authorization_url, status_code=302)


@router.get("/entra/callback")
async def entra_callback(request: Request, code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None):
    settings = _entera_settings_or_503()

    if error:
        raise HTTPException(status_code=401, detail=f"Entra authentication failed: {error}")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code/state in callback")

    state_entry = _entra_state_store.pop(state, None)
    if not state_entry:
        raise HTTPException(status_code=400, detail="Invalid or expired Entra auth state")

    if (time.time() - state_entry.get("created_at", 0)) > 600:
        raise HTTPException(status_code=400, detail="Entra auth state expired")

    oidc = await _get_entra_openid_config(settings)

    payload = {
        "grant_type": "authorization_code",
        "client_id": settings.ENTRA_CLIENT_ID,
        "client_secret": settings.ENTRA_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.ENTRA_REDIRECT_URI,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            token_response = await client.post(
                oidc["token_endpoint"],
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            token_response.raise_for_status()
            token_data = token_response.json()
    except Exception as exc:
        logger.error(f"Entra token exchange failed: {exc}")
        raise HTTPException(status_code=401, detail="Entra token exchange failed")

    id_token = token_data.get("id_token")
    if not id_token:
        raise HTTPException(status_code=401, detail="Entra response missing id_token")

    claims = _validate_entra_id_token(
        id_token=id_token,
        jwks_uri=oidc["jwks_uri"],
        issuer=oidc["issuer"],
        audience=settings.ENTRA_CLIENT_ID,
    )

    expected_nonce = state_entry.get("nonce")
    if expected_nonce and claims.get("nonce") != expected_nonce:
        raise HTTPException(status_code=401, detail="Invalid nonce in Entra token")

    user = _upsert_social_user(claims, state_entry.get("provider", "microsoft"))

    access_token = create_access_token(user["id"])
    ip = _get_client_ip(request)
    refresh_token = await create_refresh_token(user["id"], ip_address=ip)
    _store_refresh_token(refresh_token, user["id"])
    await log_audit(user["id"], user["id"], f"LOGIN_ENTRA_{state_entry.get('provider', 'microsoft').upper()}", request)

    exchange_code = secrets.token_urlsafe(32)
    _purge_expired_entra_exchange(time.time())
    _entra_exchange_store[exchange_code] = {
        "created_at": time.time(),
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user["id"],
            "name": user.get("name"),
            "email": user.get("email"),
            "onboarding_complete": all(user.get(f) for f in ("date_of_birth", "gender", "preferred_language", "medical_literacy_level")),
            "preferred_language": user.get("preferred_language", "en"),
        },
    }

    frontend_redirect = f"{settings.ENTRA_FRONTEND_CALLBACK_URL}?exchange_code={exchange_code}"
    return RedirectResponse(url=frontend_redirect, status_code=302)


@router.post("/entra/exchange")
async def entra_exchange(body: EntraExchangeRequest):
    _purge_expired_entra_exchange(time.time())
    entry = _entra_exchange_store.pop(body.exchange_code, None)
    if not entry:
        raise HTTPException(status_code=400, detail="Invalid or expired exchange code")

    return {
        "access_token": entry["access_token"],
        "refresh_token": entry["refresh_token"],
        "token_type": "bearer",
        "user": entry["user"],
    }


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

    try:
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
    except Exception as exc:
        logger.warning(f"User persistence skipped for {body.email}: {exc}")

    access_token = create_access_token(user_id)
    ip = _get_client_ip(request)
    refresh_token = await create_refresh_token(user_id, ip_address=ip)
    _store_refresh_token(refresh_token, user_id)

    await log_audit(user_id, user_id, "REGISTER", request)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "name": body.name,
            "email": body.email,
            "onboarding_complete": False,
            "preferred_language": body.preferred_language or "en",
        },
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
            "preferred_language": user.get("preferred_language", "en"),
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
