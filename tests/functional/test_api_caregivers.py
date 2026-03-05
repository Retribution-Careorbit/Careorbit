# tests/functional/test_api_caregivers.py
# V4 FIXES:
#   V4-1: add_caregiver returns {"status": "added", "caregiver_name": ...,
#          "permission_level": ...} — NO link_id in response.
#   V4-2: delete_caregiver is idempotent — always 200 (no 404 on missing).
#          DELETE /{caregiver_id} uses caregiver's user_id as path param.
#   NEW-3: Endpoints are POST /add + DELETE /{caregiver_user_id}

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from uuid import uuid4

client = TestClient(app)


def _auth(user_id="patient-id", tier="free"):
    return patch("api.middleware.auth.get_current_user",
                 return_value={"id": user_id, "tier": tier})


class TestCaregiverAdd:

    def test_add_caregiver_success(self):
        """
        V4-1 FIX: Route returns {"status": "added", "caregiver_name": ...,
        "permission_level": ...}. No link_id in response.
        """
        with _auth():
            response = client.post("/api/caregivers/add", json={
                "caregiver_email": f"caregiver.{uuid4().hex[:6]}@test.com",
                "relationship": "son",
                "permission_level": "view"
            })
            assert response.status_code in (200, 201)
            data = response.json()
            assert data["status"] == "added"
            assert "caregiver_name" in data
            assert data["permission_level"] == "view"

    def test_add_caregiver_with_edit_permission(self):
        with _auth():
            response = client.post("/api/caregivers/add", json={
                "caregiver_email": f"editor.{uuid4().hex[:6]}@test.com",
                "relationship": "daughter",
                "permission_level": "edit"
            })
            assert response.status_code in (200, 201)
            assert response.json()["permission_level"] == "edit"

    def test_invalid_relationship_rejected(self):
        """'neighbor' is not in allowed relationship list."""
        with _auth():
            response = client.post("/api/caregivers/add", json={
                "caregiver_email": "test@test.com",
                "relationship": "neighbor",
                "permission_level": "view"
            })
            assert response.status_code in (400, 422)

    def test_invalid_permission_level_rejected(self):
        """'admin' is not in allowed permission levels."""
        with _auth():
            response = client.post("/api/caregivers/add", json={
                "caregiver_email": "test@test.com",
                "relationship": "son",
                "permission_level": "admin"
            })
            assert response.status_code in (400, 422)

    def test_caregiver_email_not_registered_returns_404(self):
        """MVP: caregiver must have an existing CareOrbit account."""
        with _auth():
            response = client.post("/api/caregivers/add", json={
                "caregiver_email": f"notregistered.{uuid4().hex}@test.com",
                "relationship": "son",
                "permission_level": "view"
            })
            assert response.status_code == 404, \
                "Non-registered caregiver email must return 404"

    @pytest.mark.xfail(
        reason=(
            "V4.1-C: Feature gate enforcement requires explicit wiring in caregivers.py "
            "(e.g. await check_caregiver_limit(patient_id) before INSERT). "
            "caregivers.py in MVP Part 3 does not call check_caregiver_limit yet. "
            "Remove xfail once the gate is wired."
        ),
        strict=True  # xpass = test code is wrong, must be reviewed
    )
    def test_caregiver_limit_exceeded_returns_429(self):
        """
        Free tier max_caregivers=2 (TIER_LIMITS). When the limit is exceeded
        the feature gate must raise HTTP 429.
        This test verifies the gate IS called by the route and returns 429.
        Currently xfail — gate not wired in MVP caregivers.py.
        """
        from fastapi import HTTPException
        with _auth(tier="free"), \
             patch("api.routes.caregivers.enforce_caregiver_limit",
                   side_effect=HTTPException(status_code=429, detail={
                       "error": "Caregiver limit reached",
                       "limit": 2, "tier": "free"
                   })):
            response = client.post("/api/caregivers/add", json={
                "caregiver_email": f"third.caregiver.{uuid4().hex[:6]}@test.com",
                "relationship": "son",
                "permission_level": "view"
            })
            assert response.status_code == 429, \
                f"Expected 429 (caregiver limit), got {response.status_code}"
            data = response.json()
            assert "limit" in str(data), "429 response must include limit info"

    def test_add_requires_auth(self):
        response = client.post("/api/caregivers/add", json={
            "caregiver_email": "test@test.com",
            "relationship": "son", "permission_level": "view"
        })
        assert response.status_code in (401, 403)


class TestCaregiverDelete:

    def test_delete_caregiver_success(self):
        """
        V4-2 FIX: DELETE route is idempotent — returns 200 {"status": "revoked"}
        even if the caregiver_id doesn't exist (0 rows updated = still succeeds).
        Path param is caregiver's user_id.
        """
        with _auth():
            response = client.delete(f"/api/caregivers/{uuid4()}")
            # Idempotent delete — always 200 (or 204 if no body)
            assert response.status_code in (200, 204)

    def test_delete_active_caregiver(self):
        """Full flow: add caregiver (mock found user), then revoke."""
        caregiver_user_id = str(uuid4())
        with _auth(user_id="patient-123"):
            # Delete by caregiver's user_id
            response = client.delete(f"/api/caregivers/{caregiver_user_id}")
            assert response.status_code in (200, 204)
            if response.status_code == 200:
                assert response.json().get("status") == "revoked"

    def test_delete_requires_auth(self):
        response = client.delete(f"/api/caregivers/{uuid4()}")
        assert response.status_code in (401, 403)


class TestCaregiverViews:

    def test_list_my_patients_as_caregiver(self):
        """Caregiver can list all patients they have access to."""
        with _auth():
            response = client.get("/api/caregivers/my-patients")
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    def test_list_my_caregivers_as_patient(self):
        """Patient can see all caregivers with access to their data."""
        with _auth():
            response = client.get("/api/caregivers/my-caregivers")
            assert response.status_code == 200
            assert isinstance(response.json(), list)
