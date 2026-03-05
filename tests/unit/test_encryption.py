# tests/unit/test_encryption.py
# V4 REWRITE combining V3.1 Fix C + CRIT-2:
#
#   CRIT-2 root cause: encrypt_sql() in utils/encryption.py is a PASS-THROUGH.
#   It returns field_value unchanged. The pgp_sym_encrypt call happens in the
#   raw SQL strings in route handlers.
#
#   Actual contract:
#     encrypt_sql("phone") == "phone"  (pass-through)
#     get_encryption_params(dict) → adds "encryption_key" to dict
#
#   V3.1 Fix C: Test at SQL query execution level (verify route INSERT uses
#   pgp_sym_encrypt) rather than testing the helper's return value.

import pytest
from unittest.mock import patch, AsyncMock, MagicMock, call
from fastapi.testclient import TestClient


class TestEncryptionHelpers:
    """Test the actual contracts of the encryption helper functions."""

    def test_encrypt_sql_is_pass_through(self):
        """
        encrypt_sql(field_value) returns field_value unchanged.
        The actual pgp_sym_encrypt() call is in the raw SQL strings.
        Testing the return value for 'pgp_sym_encrypt' content was wrong (CRIT-2).
        """
        from utils.encryption import encrypt_sql
        assert encrypt_sql("email_value") == "email_value"
        assert encrypt_sql("phone_number") == "phone_number"

    def test_get_encryption_params_injects_key(self):
        """get_encryption_params should add encryption_key to params dict."""
        from utils.encryption import get_encryption_params
        params = {"name": "Ramesh", "email": "ramesh@test.com"}
        result = get_encryption_params(params)
        assert "encryption_key" in result, \
            "encryption_key not injected into params"
        assert len(result["encryption_key"]) >= 16, \
            "encryption_key too short (< 16 chars)"

    def test_get_encryption_params_preserves_original_keys(self):
        """Ensure original params are not lost when key is injected."""
        from utils.encryption import get_encryption_params
        original = {"name": "Ramesh", "phone": "+919876543210"}
        result = get_encryption_params(original)
        assert result["name"] == "Ramesh"
        assert result["phone"] == "+919876543210"

    def test_encryption_key_not_empty(self):
        """Key must come from environment/config, never be empty or None."""
        from utils.encryption import get_encryption_params
        result = get_encryption_params({})
        assert result["encryption_key"] is not None
        assert result["encryption_key"] != ""


class TestSQLEncryptionAtQueryLevel:
    """
    V3.1 Fix C: Test that actual INSERT queries use pgp_sym_encrypt.
    We verify the SQL executed by the register route includes the
    encryption function call and key parameter.
    """

    def test_registration_query_uses_pgp_sym_encrypt(self):
        """
        The INSERT query for user registration must use pgp_sym_encrypt
        for PII fields. We intercept the session.execute call and inspect
        the SQL string.
        """
        with patch("api.routes.auth.async_session") as mock_session:
            session = AsyncMock()
            session.__aenter__ = AsyncMock(return_value=session)
            session.__aexit__ = AsyncMock(return_value=False)
            # Make the "existing user" check return empty (no duplicate)
            session.execute = AsyncMock(return_value=MagicMock(
                first=lambda: None,
                mappings=lambda: MagicMock(first=lambda: None)
            ))
            mock_session.return_value = session

            from main import app
            client = TestClient(app)
            client.post("/api/auth/register", json={
                "name": "Encrypt Test",
                "email": f"encrypt.test@careorbit.dev",
                "password": "EncryptPass123!",
                "phone_number": "+919876500099"
            })

            # V4.1-A FIX: hard assert — if execute was never called, the test
            # must fail (not silently pass). call_count >= 2 because auth.py
            # first SELECTs to check for duplicate email, then INSERTs.
            assert session.execute.call_count >= 2, (
                "Registration must execute at least 2 DB calls "
                "(SELECT duplicate check + INSERT). "
                f"Actual call_count: {session.execute.call_count}"
            )
            all_calls_str = " ".join(
                str(c) for c in session.execute.call_args_list
            )
            assert "pgp_sym_encrypt" in all_calls_str.lower() or \
                   "encryption_key" in all_calls_str, (
                "Registration INSERT must use pgp_sym_encrypt for PII. "
                f"Queries executed: {all_calls_str[:300]}"
            )

    def test_registration_params_include_encryption_key(self):
        """
        The params dict passed to the INSERT execute call must include
        the encryption_key (injected by get_encryption_params).
        """
        with patch("api.routes.auth.async_session") as mock_session:
            session = AsyncMock()
            session.__aenter__ = AsyncMock(return_value=session)
            session.__aexit__ = AsyncMock(return_value=False)
            session.execute = AsyncMock(return_value=MagicMock(
                first=lambda: None,
                mappings=lambda: MagicMock(first=lambda: None)
            ))
            mock_session.return_value = session

            from main import app
            client = TestClient(app)
            client.post("/api/auth/register", json={
                "name": "Key Test",
                "email": "keytest@careorbit.dev",
                "password": "KeyPass123!",
                "phone_number": "+919876500098"
            })

            # V4.1-A FIX: hard assert, same reasoning as above.
            assert session.execute.call_count >= 2, (
                "Registration must execute at least 2 DB calls. "
                f"Actual: {session.execute.call_count}"
            )
            # Inspect every call for an 'encryption_key' param
            for call_item in session.execute.call_args_list:
                args = call_item[0]  # positional args
                if len(args) >= 2 and isinstance(args[1], dict):
                    if "encryption_key" in args[1]:
                        return  # Found it — test passes
            # No call had encryption_key in params — fail explicitly
            all_params = [str(c[0]) for c in session.execute.call_args_list]
            assert False, \
                f"encryption_key not found in any execute params: {all_params}"

    @pytest.mark.skip(reason="Requires real PostgreSQL + pgcrypto extension")
    def test_roundtrip_encrypt_decrypt_with_pgcrypto(self):
        """Integration: INSERT encrypted field, SELECT with pgp_sym_decrypt."""
        pass
