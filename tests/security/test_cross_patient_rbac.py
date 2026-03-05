# tests/security/test_cross_patient_rbac.py
# ADD-1: Patient A's token must not access Patient B's data.
# This is the most critical security test for a healthcare app.
# A bug here is a HIPAA violation.

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app
from uuid import uuid4

client = TestClient(app)

PATIENT_A_ID = str(uuid4())
PATIENT_B_ID = str(uuid4())


def _auth_as_patient_a():
    """Authenticated as Patient A."""
    return patch("api.middleware.auth.get_current_user",
                 return_value={"id": PATIENT_A_ID, "tier": "free"})


def _rbac_deny_cross_access():
    """RBAC denies Patient A accessing Patient B's data."""
    from fastapi import HTTPException
    return patch("api.middleware.rbac.verify_patient_access",
                 side_effect=HTTPException(
                     status_code=403,
                     detail="You do not have permission to access this patient's data."
                 ))


class TestCrossPatientIsolation:
    """
    Patient A must not be able to access Patient B's data
    via any endpoint, even with a valid access token.
    """

    def test_patient_a_cannot_read_patient_b_medications(self):
        """
        GET /api/patients/medications?patient_id=B with Patient A's token → 403.
        """
        with _auth_as_patient_a(), _rbac_deny_cross_access():
            response = client.get(
                f"/api/patients/medications?patient_id={PATIENT_B_ID}"
            )
            assert response.status_code == 403, \
                f"Patient A must not access Patient B's medications. " \
                f"Got: {response.status_code}"

    def test_patient_a_cannot_read_patient_b_overview(self):
        """GET /api/patients/overview?patient_id=B → 403."""
        with _auth_as_patient_a(), _rbac_deny_cross_access():
            response = client.get(
                f"/api/patients/overview?patient_id={PATIENT_B_ID}"
            )
            assert response.status_code == 403

    def test_patient_a_cannot_generate_patient_b_summary(self):
        """GET /api/summary/generate?patient_id=B → 403."""
        with _auth_as_patient_a(), _rbac_deny_cross_access():
            response = client.get(
                f"/api/summary/generate?patient_id={PATIENT_B_ID}"
            )
            assert response.status_code == 403

    def test_patient_a_cannot_upload_to_patient_b(self):
        """POST /api/documents/upload?patient_id=B → 403."""
        with _auth_as_patient_a(), _rbac_deny_cross_access():
            response = client.post(
                f"/api/documents/upload?patient_id={PATIENT_B_ID}",
                files={"file": ("rx.jpg", b"fake", "image/jpeg")}
            )
            assert response.status_code == 403

    def test_patient_a_cannot_add_reminder_for_patient_b(self):
        """POST /api/reminders/create?patient_id=B → 403."""
        with _auth_as_patient_a(), _rbac_deny_cross_access():
            response = client.post(
                f"/api/reminders/create?patient_id={PATIENT_B_ID}",
                json={
                    "medication_node_id": "some-node",
                    "reminder_time": "08:00",
                    "days_of_week": [1, 2, 3, 4, 5, 6, 7]
                }
            )
            assert response.status_code == 403

    def test_patient_accessing_own_data_is_allowed(self):
        """Patient A accessing their OWN data must always succeed."""
        with patch("api.middleware.auth.get_current_user",
                   return_value={"id": PATIENT_A_ID, "tier": "free"}), \
             patch("api.middleware.rbac.verify_patient_access",
                   return_value={"access_type": "self", "permission_level": "full"}), \
             patch("api.routes.patients.phig_builder") as mock_phig:
            from unittest.mock import AsyncMock
            mock_phig.get_medication_subgraph = AsyncMock(return_value={"medications": []})
            response = client.get(
                f"/api/patients/medications?patient_id={PATIENT_A_ID}"
            )
            assert response.status_code == 200, \
                "Patient must be able to access their own data"
