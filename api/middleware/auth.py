import hashlib
import secrets
import logging
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import HTTPException, Request, status
from jose import jwt, JWTError

from config import get_settings
from db.session import async_session


logger = logging.getLogger("careorbit.auth")


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: str) -> str:
    settings = get_settings()
    payload = {
        "sub": user_id,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRY_MINUTES),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


async def create_refresh_token(user_id: str, ip_address: str = None) -> str:
    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)

    try:
        async with async_session() as session:
            await session.execute(
                "INSERT INTO refresh_tokens (user_id, token_hash, ip_address, expires_at) VALUES (:uid, :hash, :ip, :exp)",
                {
                    "uid": user_id,
                    "hash": token_hash,
                    "ip": ip_address or "unknown",
                    "exp": expires_at,
                }
            )
            await session.commit()
    except Exception as exc:
        logger.warning(f"Refresh token persistence failed: {exc}")

    return raw_token


async def get_current_user(request_or_credentials=None) -> dict:
    settings = get_settings()

    token = None
    if request_or_credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    if hasattr(request_or_credentials, "credentials"):
        token = request_or_credentials.credentials
    elif hasattr(request_or_credentials, "headers"):
        auth_header = request_or_credentials.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    elif isinstance(request_or_credentials, str):
        token = request_or_credentials

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return {"id": user_id, "tier": "free"}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def revoke_all_user_tokens(user_id: str):
    try:
        async with async_session() as session:
            await session.execute(
                "UPDATE refresh_tokens SET revoked_at = NOW() WHERE user_id = :uid AND revoked_at IS NULL",
                {"uid": user_id}
            )
            await session.commit()
    except Exception as exc:
        logger.warning(f"Revoke all refresh tokens failed: {exc}")


async def revoke_refresh_token(raw_token: str):
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    try:
        async with async_session() as session:
            await session.execute(
                "UPDATE refresh_tokens SET revoked_at = NOW() WHERE token_hash = :hash",
                {"hash": token_hash}
            )
            await session.commit()
    except Exception as exc:
        logger.warning(f"Revoke refresh token failed: {exc}")
