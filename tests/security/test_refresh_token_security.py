# tests/security/test_refresh_token_security.py
# V4 REWRITE combining V3.1 Fix B + CRIT-3:
#
#   CRIT-3 root cause: 'store_refresh_token' doesn't exist.
#     Token storage is inline inside create_refresh_token() via session.execute().
#   R4-B: JSON body for refresh/logout (not cookies).
#   V4: All assertions unconditional.

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app
from uuid import uuid4

client = TestClient(app)


class TestRefreshTokenSecurity:

    def _register_user(self) -> dict:
        """Helper: register a fresh user and return tokens."""
        email = f"refresh.{uuid4().hex[:8]}@test.com"
        reg = client.post("/api/auth/register", json={
            "name": "Refresh Security Test",
            "email": email,
            "password": "SecurePass123!",
            "phone_number": "+919876500010"
        })
        assert reg.status_code in (200, 201, 202), \
            f"Registration failed: {reg.status_code}"
        data = reg.json()
        return {
            "access_token": data.get("access_token"),
            "refresh_token": data.get("refresh_token"),
            "headers": {"Authorization": f"Bearer {data.get('access_token')}"}
        }

    def test_refresh_token_stored_as_sha256_hash(self):
        """
        CRIT-3 FIX: Patch async_session.execute, not non-existent 'store_refresh_token'.
        Verify that the second arg to execute() contains a token_hash
        that is a 64-char hex string (SHA-256 digest).
        """
        captured_params = []

        async def capture_execute(query, params=None):
            if params and "hash" in params:
                captured_params.append(params)
            return MagicMock(first=lambda: None, mappings=lambda: MagicMock(first=lambda: None))

        with patch("api.middleware.auth.async_session") as mock_session:
            session = AsyncMock()
            session.__aenter__ = AsyncMock(return_value=session)
            session.__aexit__ = AsyncMock(return_value=False)
            session.execute = AsyncMock(side_effect=capture_execute)
            mock_session.return_value = session

            from api.middleware.auth import create_refresh_token
            import asyncio
            asyncio.get_event_loop().run_until_complete(
                create_refresh_token("user-test-id", ip_address="127.0.0.1")
            )

        sha256_params = [p for p in captured_params if "hash" in p]
        assert len(sha256_params) > 0, \
            "create_refresh_token must execute an INSERT with a 'hash' parameter"
        token_hash = sha256_params[0]["hash"]
        assert len(token_hash) == 64, \
            f"SHA-256 hash must be 64 hex chars, got {len(token_hash)}: '{token_hash[:20]}...'"
        assert all(c in "0123456789abcdef" for c in token_hash), \
            "token_hash must be a valid hex string (SHA-256 output)"

    def test_revoked_refresh_token_rejected(self):
        """After logout, the old refresh token must return 401/403."""
        tokens = self._register_user()

        # Logout using JSON body (R4-B fix — not cookies)
        client.post("/api/auth/logout", json={
            "refresh_token": tokens["refresh_token"]
        }, headers=tokens["headers"])

        # Attempt to use revoked token
        response = client.post("/api/auth/refresh", json={
            "refresh_token": tokens["refresh_token"]  # JSON body (R4-B fix)
        })
        assert response.status_code in (401, 403), \
            f"Revoked refresh token was accepted: {response.status_code}"

    def test_refresh_token_rotation(self):
        """Using refresh token must issue a new one and invalidate the old."""
        tokens = self._register_user()
        old_refresh = tokens["refresh_token"]

        # Use refresh token — JSON body (R4-B fix)
        response = client.post("/api/auth/refresh", json={
            "refresh_token": old_refresh
        })
        assert response.status_code == 200, \
            f"Refresh failed: {response.status_code}"
        data = response.json()
        new_refresh = data.get("refresh_token")

        assert new_refresh is not None, "Refreshed response must include new refresh_token"
        assert new_refresh != old_refresh, \
            "Refresh token was not rotated — old and new tokens are identical"

        # Old token must now be rejected
        old_response = client.post("/api/auth/refresh", json={
            "refresh_token": old_refresh
        })
        assert old_response.status_code in (401, 403), \
            "Old refresh token still accepted after rotation"

    def test_invalid_forged_token_rejected(self):
        """Random/forged refresh token must be rejected."""
        response = client.post("/api/auth/refresh", json={
            "refresh_token": "forged.invalid.token.12345"
        })
        assert response.status_code in (401, 403)
