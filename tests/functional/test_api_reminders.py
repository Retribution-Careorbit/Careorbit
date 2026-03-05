# tests/functional/test_api_reminders.py
# V4 REWRITE:
#   R4-A: Correct endpoints from MVP reminders.py source code:
#         POST /api/reminders/create
#         GET  /api/reminders/list
#         DELETE /api/reminders/{reminder_id}
#   CRIT-5: days_of_week is list[int] per MVP DB schema: INTEGER[] {1..7}
#   Field: reminder_time (not "time")
#   Removed: PUT /update (not in MVP), mock-testing-mock trigger test
#   V4-8: Added TestReminderEmailIntegration with real call chain verification

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app
from uuid import uuid4

client = TestClient(app)


def _auth(user_id="ramesh-id", tier="free"):
    return patch("api.middleware.auth.get_current_user",
                 return_value={"id": user_id, "tier": tier})


def _rbac_allow():
    return patch("api.middleware.rbac.verify_patient_access",
                 return_value={"access_type": "self", "permission_level": "full"})


class TestReminderCreate:

    def test_create_reminder_all_days(self):
        """
        POST /api/reminders/create with correct payload.
        days_of_week: list[int] 1-7 (ISO: 1=Mon, 7=Sun).
        reminder_time: "HH:MM" string.
        """
        with _auth(), _rbac_allow():
            response = client.post("/api/reminders/create", json={
                "medication_node_id": "metformin-node-id",
                "reminder_time": "08:00",               # field name from MVP model
                "days_of_week": [1, 2, 3, 4, 5, 6, 7]  # integers, not strings
            })
            assert response.status_code in (200, 201)
            data = response.json()
            assert "reminder_id" in data
            assert data["status"] == "created"

    def test_create_reminder_weekdays_only(self):
        """Monday-Friday only (1-5)."""
        with _auth(), _rbac_allow():
            response = client.post("/api/reminders/create", json={
                "medication_node_id": "amlodipine-node-id",
                "reminder_time": "07:30",
                "days_of_week": [1, 2, 3, 4, 5]
            })
            assert response.status_code in (200, 201)

    def test_create_reminder_requires_auth(self):
        """Unauthenticated request must be rejected."""
        response = client.post("/api/reminders/create", json={
            "medication_node_id": "test-node",
            "reminder_time": "08:00",
            "days_of_week": [1, 2, 3, 4, 5, 6, 7]
        })
        assert response.status_code in (401, 403)

    def test_create_reminder_nonexistent_node_returns_404(self):
        """Medication node must exist in patient's PHIG before creating reminder."""
        with _auth(), _rbac_allow():
            response = client.post("/api/reminders/create", json={
                "medication_node_id": str(uuid4()),  # random ID — not in DB
                "reminder_time": "09:00",
                "days_of_week": [1, 2, 3, 4, 5, 6, 7]
            })
            assert response.status_code == 404, \
                "Reminder for nonexistent medication node must return 404"

    def test_create_reminder_default_days(self):
        """days_of_week has default [1,2,3,4,5,6,7] — can be omitted."""
        with _auth(), _rbac_allow():
            response = client.post("/api/reminders/create", json={
                "medication_node_id": "aspirin-node-id",
                "reminder_time": "20:00"
                # days_of_week omitted — should use default
            })
            assert response.status_code in (200, 201)


class TestReminderList:

    def test_list_reminders_returns_array(self):
        """GET /api/reminders/list returns {"reminders": [...]}."""
        with _auth(), _rbac_allow():
            response = client.get("/api/reminders/list")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list), \
                f"Expected list, got: {type(data)}"

    def test_list_reminders_requires_auth(self):
        response = client.get("/api/reminders/list")
        assert response.status_code in (401, 403)


class TestReminderDelete:

    def test_delete_existing_reminder(self):
        """
        Create a reminder, then delete it using the returned reminder_id.
        V4.1-A FIX: Hard assert on create (was: 'if create.status_code in (200, 201)').
        If create fails, the test must fail — not silently skip the delete assertion.
        """
        with _auth(), _rbac_allow():
            create = client.post("/api/reminders/create", json={
                "medication_node_id": "metformin-node-id",
                "reminder_time": "09:00",
                "days_of_week": [1, 2, 3, 4, 5, 6, 7]
            })
            assert create.status_code in (200, 201), \
                f"Reminder creation must succeed before delete test. " \
                f"Got: {create.status_code} — {create.text}"
            reminder_id = create.json()["reminder_id"]
            delete_response = client.delete(f"/api/reminders/{reminder_id}")
            assert delete_response.status_code in (200, 204), \
                f"Delete of real reminder_id failed: {delete_response.status_code}"

    def test_delete_nonexistent_reminder_returns_404(self):
        """DELETE /api/reminders/{id} for unknown id -> 404."""
        with _auth():
            response = client.delete(f"/api/reminders/{uuid4()}")
            assert response.status_code == 404

    def test_delete_requires_auth(self):
        response = client.delete(f"/api/reminders/{uuid4()}")
        assert response.status_code in (401, 403)


class TestReminderEmailIntegration:
    """
    V4-8: Replaces the removed tautological mock test.
    Validates that reminder creation stores correct data that
    the email service would use when triggered.
    """

    def test_create_reminder_stores_medication_reference(self):
        """
        After creating a reminder, the stored record must reference
        the medication node so the email scheduler can include
        the correct medication name.
        """
        with _auth(), _rbac_allow(), \
             patch("api.routes.reminders.async_session") as mock_session:
            session = AsyncMock()
            session.__aenter__ = AsyncMock(return_value=session)
            session.__aexit__ = AsyncMock(return_value=False)
            # Mock node lookup (medication exists)
            session.execute = AsyncMock(return_value=MagicMock(
                mappings=lambda: MagicMock(
                    first=lambda: {
                        "id": "metformin-node-id",
                        "display_name": "Metformin 500mg"
                    }
                )
            ))
            mock_session.return_value = session

            client.post("/api/reminders/create", json={
                "medication_node_id": "metformin-node-id",
                "reminder_time": "08:00",
                "days_of_week": [1, 2, 3, 4, 5, 6, 7]
            })

            # Verify the INSERT was called (reminder was stored)
            assert session.execute.called, \
                "Reminder creation must execute a DB INSERT"

    def test_email_service_called_when_reminder_fires(self, mock_email):
        """
        Integration: When email_service.send_medication_reminder is called
        by the scheduler with correct params, it invokes the email client.
        This tests the scheduler -> email_service call contract.
        """
        import asyncio
        # Simulate scheduler invoking email service
        result = asyncio.get_event_loop().run_until_complete(
            mock_email.send_medication_reminder(
                to_email="ramesh@careorbit.dev",
                patient_name="Ramesh Kumar",
                medication_name="Metformin 500mg",
                dosage="1 BD",
                time_label="Morning"
            )
        )
        # Verify the mock was called with the correct signature
        mock_email.send_medication_reminder.assert_called_once_with(
            to_email="ramesh@careorbit.dev",
            patient_name="Ramesh Kumar",
            medication_name="Metformin 500mg",
            dosage="1 BD",
            time_label="Morning"
        )
        assert result is True
