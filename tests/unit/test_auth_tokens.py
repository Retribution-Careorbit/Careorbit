# tests/unit/test_auth_tokens.py
# Tests JWT creation/verification logic without hitting real DB or HTTP.

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from contextlib import asynccontextmanager


class TestJWTTokens:

    def test_access_token_contains_user_id(self):
        from api.middleware.auth import create_access_token
        from jose import jwt
        from config import get_settings
        settings = get_settings()
        token = create_access_token("user-abc-123")
        payload = jwt.decode(token, settings.JWT_SECRET,
                             algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == "user-abc-123"

    def test_access_token_type_is_access(self):
        from api.middleware.auth import create_access_token
        from jose import jwt
        from config import get_settings
        settings = get_settings()
        token = create_access_token("user-abc-123")
        payload = jwt.decode(token, settings.JWT_SECRET,
                             algorithms=[settings.JWT_ALGORITHM])
        assert payload["type"] == "access"

    def test_access_token_expires_in_15_minutes(self):
        from api.middleware.auth import create_access_token
        from jose import jwt
        from config import get_settings
        import time
        settings = get_settings()
        before = int(time.time())
        token = create_access_token("user-abc-123")
        payload = jwt.decode(token, settings.JWT_SECRET,
                             algorithms=[settings.JWT_ALGORITHM])
        exp = payload["exp"]
        # Should expire between 14 and 16 minutes from now
        assert (before + 840) <= exp <= (before + 960)

    def test_password_hash_is_bcrypt(self):
        """Bcrypt hashes start with '$2b$' — contract for storage format."""
        from api.middleware.auth import hash_password
        hashed = hash_password("testpassword")
        assert hashed.startswith("$2b$"), \
            f"Expected bcrypt hash, got: {hashed[:10]}..."

    def test_password_verify_correct(self):
        from api.middleware.auth import hash_password, verify_password
        hashed = hash_password("MySecretPass123!")
        assert verify_password("MySecretPass123!", hashed) is True

    def test_password_verify_wrong(self):
        from api.middleware.auth import hash_password, verify_password
        hashed = hash_password("MySecretPass123!")
        assert verify_password("WrongPassword!", hashed) is False

    def test_different_users_get_different_tokens(self):
        from api.middleware.auth import create_access_token
        t1 = create_access_token("user-001")
        t2 = create_access_token("user-002")
        assert t1 != t2

    def test_tampered_token_is_rejected(self):
        from api.middleware.auth import create_access_token, get_current_user
        from fastapi import HTTPException
        from fastapi.security import HTTPAuthorizationCredentials
        import asyncio
        token = create_access_token("user-abc-123")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises((HTTPException, Exception)):
            asyncio.get_event_loop().run_until_complete(
                get_current_user(HTTPAuthorizationCredentials(
                    scheme="Bearer", credentials=tampered
                ))
            )

    @pytest.mark.anyio
    async def test_refresh_token_persists_datetime_expiry(self):
        from api.middleware.auth import create_refresh_token

        captured = {}

        class DummySession:
            async def execute(self, _query, params=None):
                captured.update(params or {})

            async def commit(self):
                return None

        @asynccontextmanager
        async def fake_session():
            yield DummySession()

        with patch("api.middleware.auth.async_session", fake_session):
            token = await create_refresh_token("user-abc-123", ip_address="127.0.0.1")

        assert isinstance(token, str)
        assert isinstance(captured.get("exp"), datetime)
        assert captured.get("exp").tzinfo is not None
