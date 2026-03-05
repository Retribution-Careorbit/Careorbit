# tests/security/test_password_change_revocation.py
# ADD-2: Password change must invalidate all existing refresh tokens.
# If a user's password is changed (after theft/compromise),
# all attacker sessions must be terminated.

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app
from uuid import uuid4

client = TestClient(app)


class TestPasswordChangeRevocation:

    def test_revoke_all_user_tokens_on_password_change(self):
        """
        When revoke_all_user_tokens() is called, all refresh tokens
        for that user must have revoked_at set to NOW().
        Verifies the UPDATE query targets the correct user.
        """
        captured_params = []

        async def capture_execute(query, params=None):
            if params:
                captured_params.append((str(query).lower(), params))
            return MagicMock(first=lambda: None)

        with patch("api.middleware.auth.async_session") as mock_session:
            session = AsyncMock()
            session.__aenter__ = AsyncMock(return_value=session)
            session.__aexit__ = AsyncMock(return_value=False)
            session.execute = AsyncMock(side_effect=capture_execute)
            mock_session.return_value = session

            from api.middleware.auth import revoke_all_user_tokens
            import asyncio
            asyncio.get_event_loop().run_until_complete(
                revoke_all_user_tokens("target-user-id")
            )

        revoke_calls = [
            (q, p) for q, p in captured_params
            if "update" in q and "refresh_tokens" in q
        ]
        assert len(revoke_calls) > 0, \
            "revoke_all_user_tokens must execute an UPDATE on refresh_tokens"

        # Verify correct user targeted
        for _, params in revoke_calls:
            assert params.get("uid") == "target-user-id", \
                f"Wrong user targeted in token revocation: {params}"

    def test_revoke_single_token_on_logout(self):
        """
        Logout must revoke ONLY the specific refresh token,
        not all tokens (device-specific logout).
        """
        captured_params = []

        async def capture_execute(query, params=None):
            if params:
                captured_params.append((str(query).lower(), params))
            return MagicMock(first=lambda: None)

        with patch("api.middleware.auth.async_session") as mock_session:
            session = AsyncMock()
            session.__aenter__ = AsyncMock(return_value=session)
            session.__aexit__ = AsyncMock(return_value=False)
            session.execute = AsyncMock(side_effect=capture_execute)
            mock_session.return_value = session

            from api.middleware.auth import revoke_refresh_token
            import asyncio
            asyncio.get_event_loop().run_until_complete(
                revoke_refresh_token("raw-test-token-value")
            )

        revoke_calls = [
            (q, p) for q, p in captured_params
            if "update" in q and "revoked_at" in q
        ]
        assert len(revoke_calls) > 0, \
            "revoke_refresh_token must execute an UPDATE setting revoked_at"

        # Must filter by hash (not user_id) — single-token revocation
        for _, params in revoke_calls:
            assert "uid" not in params, \
                "Single-token revocation must target by hash, not user_id"
            assert "hash" in params, \
                "Single-token revocation must target by token_hash"

    @pytest.mark.skip(reason="Requires live auth routes with password-change endpoint")
    def test_old_token_invalid_after_password_change_e2e(self):
        """
        E2E: Register → login → change password → try old token → 401.
        Deferred until password-change endpoint is implemented.
        """
        pass
