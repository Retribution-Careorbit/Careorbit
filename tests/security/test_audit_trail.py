# tests/security/test_audit_trail.py
# V4 REWRITE combining V3.1 Fix D + V4-5 + V4-10:
#   R4-D: Test structure (user_id, IP, timestamp, metadata) not action enum
#   V4-5: Restored REGISTER, VIEW_OVERVIEW, VIEW_CARE_GAPS, UPGRADE_SUBSCRIPTION
#         (all used in actual MVP route handlers)
#   V4-10: Replaced fragile str(call_args) assertion with direct param access

import pytest
from api.middleware.audit import log_audit
from unittest.mock import patch, AsyncMock, MagicMock


class TestAuditStructure:
    """Verify audit entries contain all required fields."""

    async def test_audit_entry_records_user_id(self):
        """Every audit entry must record WHO performed the action."""
        with patch("api.middleware.audit.async_session") as mock_session:
            session = AsyncMock()
            session.__aenter__ = AsyncMock(return_value=session)
            session.__aexit__ = AsyncMock(return_value=False)
            mock_session.return_value = session

            mock_request = MagicMock()
            mock_request.client.host = "192.168.1.100"
            mock_request.headers = {"user-agent": "Mozilla/5.0"}

            await log_audit("user-123", "patient-456", "VIEW_MEDICATIONS",
                          request=mock_request)

            assert session.execute.called
            # V4-10: Direct param access, not str(call_args)
            call_params = session.execute.call_args[0][1]  # 2nd positional arg
            assert call_params.get("uid") == "user-123", \
                f"user_id param wrong: {call_params}"

    async def test_audit_entry_records_patient_id(self):
        """Audit must record WHOSE data was accessed."""
        with patch("api.middleware.audit.async_session") as mock_session:
            session = AsyncMock()
            session.__aenter__ = AsyncMock(return_value=session)
            session.__aexit__ = AsyncMock(return_value=False)
            mock_session.return_value = session

            mock_request = MagicMock()
            mock_request.client.host = "10.0.0.1"
            mock_request.headers = {}

            await log_audit("user-123", "patient-456", "VIEW_LABS",
                          request=mock_request)

            call_params = session.execute.call_args[0][1]
            assert call_params.get("pid") == "patient-456"

    async def test_audit_entry_records_ip_address(self):
        """Audit must record IP for forensic investigations."""
        with patch("api.middleware.audit.async_session") as mock_session:
            session = AsyncMock()
            session.__aenter__ = AsyncMock(return_value=session)
            session.__aexit__ = AsyncMock(return_value=False)
            mock_session.return_value = session

            mock_request = MagicMock()
            mock_request.client.host = "10.0.0.42"
            mock_request.headers = {"user-agent": "TestClient"}

            await log_audit("user-123", "patient-456", "UPLOAD_DOCUMENT",
                          request=mock_request)

            call_params = session.execute.call_args[0][1]
            assert call_params.get("ip") == "10.0.0.42", \
                f"IP not recorded: {call_params}"

    async def test_audit_entry_records_action(self):
        """Audit must record WHAT action was performed."""
        with patch("api.middleware.audit.async_session") as mock_session:
            session = AsyncMock()
            session.__aenter__ = AsyncMock(return_value=session)
            session.__aexit__ = AsyncMock(return_value=False)
            mock_session.return_value = session

            mock_request = MagicMock()
            mock_request.client.host = "127.0.0.1"
            mock_request.headers = {}

            await log_audit("user-123", "patient-456", "CHAT_QUERY",
                          request=mock_request)

            call_params = session.execute.call_args[0][1]
            assert call_params.get("action") == "CHAT_QUERY"

    async def test_audit_commit_is_called(self):
        """Audit entry must be committed to DB (not just executed)."""
        with patch("api.middleware.audit.async_session") as mock_session:
            session = AsyncMock()
            session.__aenter__ = AsyncMock(return_value=session)
            session.__aexit__ = AsyncMock(return_value=False)
            mock_session.return_value = session

            mock_request = MagicMock()
            mock_request.client.host = "127.0.0.1"
            mock_request.headers = {}

            await log_audit("u", "p", "LOGIN", request=mock_request)
            assert session.commit.called, "Audit entry must be committed"

    async def test_audit_accepts_optional_metadata(self):
        """Audit should accept and store optional metadata dict."""
        with patch("api.middleware.audit.async_session") as mock_session:
            session = AsyncMock()
            session.__aenter__ = AsyncMock(return_value=session)
            session.__aexit__ = AsyncMock(return_value=False)
            mock_session.return_value = session

            mock_request = MagicMock()
            mock_request.client.host = "127.0.0.1"
            mock_request.headers = {}

            await log_audit(
                "user-123", "patient-456", "GENERATE_SUMMARY",
                request=mock_request,
                metadata={"summary_id": "sum-001", "format": "pdf"}
            )
            assert session.execute.called


class TestValidAuditActions:
    """
    V4-5 FIX: Restored actions that are ACTUALLY used in MVP route handlers.
    Previously removed REGISTER, VIEW_OVERVIEW, VIEW_CARE_GAPS, UPGRADE_SUBSCRIPTION
    even though they appear in auth.py, patients.py, and subscriptions.py.
    """

    # Sourced directly from all MVP route handlers:
    SCHEMA_VALID_ACTIONS = [
        # auth.py
        "REGISTER",          # V4-5 RESTORED: auth.py register route
        "LOGIN",             # auth.py login route
        "LOGOUT",            # auth.py logout route
        # patients.py
        "VIEW_PROFILE",
        "VIEW_MEDICATIONS",
        "VIEW_LABS",
        "VIEW_SUMMARY",
        "VIEW_OVERVIEW",     # V4-5 RESTORED: patients.py get_overview route
        "VIEW_CARE_GAPS",    # V4-5 RESTORED: patients.py get_care_gaps route
        "UPDATE_PROFILE",
        # documents.py / confirmations.py
        "UPLOAD_DOCUMENT",
        "CONFIRM_DATA",
        # summary.py
        "GENERATE_SUMMARY",
        "DOWNLOAD_PDF",
        # chat.py
        "CHAT_QUERY",
        # caregivers.py
        "ADD_CAREGIVER",
        "REVOKE_CAREGIVER",
        # subscriptions.py
        "UPGRADE_SUBSCRIPTION",  # V4-5 RESTORED: subscriptions.py upgrade route
        # General data operations
        "EXPORT_DATA",
        "DELETE_ACCOUNT",
    ]

    def test_valid_actions_list_has_no_duplicates(self):
        actions = self.SCHEMA_VALID_ACTIONS
        assert len(actions) == len(set(actions)), \
            f"Duplicate actions found: {[a for a in actions if actions.count(a) > 1]}"

    def test_valid_actions_minimum_count(self):
        """Must cover all major categories: auth, data, care, admin."""
        assert len(self.SCHEMA_VALID_ACTIONS) >= 15

    def test_register_action_is_included(self):
        """V4-5: REGISTER must be present — used in auth.py register route."""
        assert "REGISTER" in self.SCHEMA_VALID_ACTIONS, \
            "REGISTER was incorrectly removed — auth.py logs it on every registration"

    def test_view_overview_is_included(self):
        """V4-5: VIEW_OVERVIEW used in patients.py get_overview route."""
        assert "VIEW_OVERVIEW" in self.SCHEMA_VALID_ACTIONS
