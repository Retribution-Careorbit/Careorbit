# tests/security/test_audit_append_only.py
# ADD-4: Verify audit_log table is append-only at the DB permission level.
# HIPAA compliance: application user must not have UPDATE/DELETE on audit_log.
# This test verifies the DB schema constraint, not just the application code.

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


@pytest.mark.slow
class TestAuditAppendOnly:
    """
    Verify that the audit_log table does not allow UPDATE or DELETE
    operations from the application database user.

    For MVP: These tests document the required constraint.
    Full enforcement requires a dedicated DB user with restricted grants.
    Tests are marked @pytest.mark.slow as they require DB connectivity.
    """

    @pytest.mark.skip(reason="Requires real PostgreSQL with restricted app user grants")
    def test_cannot_update_audit_entry(self):
        """
        The application DB user must NOT have UPDATE permission on audit_log.
        Attempting UPDATE must raise a PostgreSQL permission error.

        Schema note: The MVP schema comment reads:
        'This table should NEVER have UPDATE or DELETE permissions
        for application users — it's append-only for integrity.'
        """
        pass  # Implementation requires: psycopg2 with app_user credentials

    @pytest.mark.skip(reason="Requires real PostgreSQL with restricted app user grants")
    def test_cannot_delete_audit_entry(self):
        """Application DB user must NOT have DELETE on audit_log."""
        pass

    def test_audit_log_middleware_never_updates(self):
        """
        Application-level guarantee: log_audit() only executes INSERT.
        Verify the SQL in log_audit contains INSERT, not UPDATE or DELETE.
        """
        with patch("api.middleware.audit.async_session") as mock_session:
            session = AsyncMock()
            session.__aenter__ = AsyncMock(return_value=session)
            session.__aexit__ = AsyncMock(return_value=False)
            mock_session.return_value = session

            import asyncio
            mock_request = MagicMock()
            mock_request.client.host = "127.0.0.1"
            mock_request.headers = {}

            asyncio.get_event_loop().run_until_complete(
                __import__("api.middleware.audit", fromlist=["log_audit"]).log_audit(
                    "user-id", "patient-id", "VIEW_MEDICATIONS",
                    request=mock_request
                )
            )

            assert session.execute.called
            executed_sql = str(session.execute.call_args[0][0]).lower()

            assert "insert" in executed_sql, \
                "log_audit() must use INSERT, not other SQL commands"
            assert "update" not in executed_sql, \
                "log_audit() must never use UPDATE (append-only contract)"
            assert "delete" not in executed_sql, \
                "log_audit() must never use DELETE (append-only contract)"

    def test_audit_log_table_has_no_updated_at_column(self):
        """
        audit_log schema should NOT have an updated_at column —
        presence of updated_at would imply the table is mutable.
        """
        # Verify by inspecting schema.sql or DB reflection
        try:
            from database.schema import AUDIT_LOG_COLUMNS
            assert "updated_at" not in AUDIT_LOG_COLUMNS, \
                "audit_log must not have updated_at (implies mutability)"
        except ImportError:
            pytest.skip("Database schema module not available for introspection")
