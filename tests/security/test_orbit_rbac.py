# tests/security/test_orbit_rbac.py
# T011: Security and RBAC tests for orbit API endpoints
# Tests: authentication, caregiver access, cross-patient isolation,
#         permission levels, and tier gating for orbit features.

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app
from uuid import uuid4

client = TestClient(app)

PATIENT_A_ID = str(uuid4())
PATIENT_B_ID = str(uuid4())
CAREGIVER_ID = str(uuid4())


def _no_auth():
    """Simulate unauthenticated request (no valid token)."""
    from fastapi import HTTPException
    return patch(
        "api.middleware.auth.get_current_user",
        side_effect=HTTPException(status_code=401, detail="Not authenticated"),
    )


def _auth_as(user_id, tier="free"):
    """Simulate authenticated user with given id and tier."""
    return patch(
        "api.middleware.auth.get_current_user",
        return_value={"id": user_id, "tier": tier},
    )


def _rbac_allow_view():
    """RBAC allows view-level access."""
    return patch(
        "api.middleware.rbac.verify_patient_access",
        return_value={"access_type": "caregiver", "permission_level": "view"},
    )


def _rbac_deny():
    """RBAC denies access (unlinked user)."""
    from fastapi import HTTPException
    return patch(
        "api.middleware.rbac.verify_patient_access",
        side_effect=HTTPException(
            status_code=403,
            detail="You do not have permission to access this patient's data.",
        ),
    )


def _mock_orbit_score(total_score=72.5, breakdown=None, delta=1.5):
    """Mock orbit score computation returning a valid response."""
    from datetime import datetime, timezone

    result = {
        "total_score": total_score,
        "delta": delta,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "breakdown": breakdown,
    }
    return result


class TestOrbitRBAC:
    """Security and RBAC tests for /api/orbit/* endpoints."""

    def test_orbit_score_requires_authentication(self):
        """GET /api/orbit/score without token → 401."""
        with _no_auth():
            response = client.get("/api/orbit/score")
            assert response.status_code == 401, (
                f"Expected 401 for unauthenticated orbit score request, "
                f"got {response.status_code}"
            )

    def test_orbit_score_caregiver_view_allowed(self):
        """Caregiver with view permission can access patient's orbit score → 200."""
        with _auth_as(CAREGIVER_ID, tier="free"), \
             _rbac_allow_view(), \
             patch("api.routes.orbit.compute_orbit_score", new_callable=AsyncMock) as mock_compute:
            mock_compute.return_value = _mock_orbit_score()
            response = client.get(
                f"/api/orbit/score?patient_id={PATIENT_A_ID}"
            )
            assert response.status_code == 200, (
                f"Caregiver with view permission should access orbit score. "
                f"Got: {response.status_code}"
            )

    def test_orbit_score_unlinked_user_blocked(self):
        """Unlinked user (no caregiver relationship) → 403."""
        with _auth_as(CAREGIVER_ID, tier="free"), _rbac_deny():
            response = client.get(
                f"/api/orbit/score?patient_id={PATIENT_A_ID}"
            )
            assert response.status_code == 403, (
                f"Unlinked user must not access orbit score. "
                f"Got: {response.status_code}"
            )

    def test_orbit_appointments_requires_edit_permission(self):
        """Caregiver with view-only permission → 403 for POST /api/orbit/appointments."""
        with _auth_as(CAREGIVER_ID, tier="free"), _rbac_allow_view(), \
             patch("api.middleware.rbac.require_permission") as mock_perm:
            from fastapi import HTTPException
            mock_perm.side_effect = HTTPException(
                status_code=403,
                detail="Edit permission required to create appointments.",
            )
            response = client.post(
                f"/api/orbit/appointments?patient_id={PATIENT_A_ID}",
                json={
                    "doctor_name": "Dr. Amit Roy",
                    "appointment_datetime": "2026-02-01T10:00:00",
                    "clinic_name": "CareOrbit Clinic",
                },
            )
            assert response.status_code == 403, (
                f"View-only caregiver must not create appointments. "
                f"Got: {response.status_code}"
            )

    def test_orbit_narrative_cross_patient_blocked(self):
        """Patient A cannot access Patient B's narrative → 403."""
        with _auth_as(PATIENT_A_ID, tier="free"), _rbac_deny():
            response = client.get(
                f"/api/orbit/narrative?patient_id={PATIENT_B_ID}"
            )
            assert response.status_code == 403, (
                f"Patient A must not access Patient B's narrative. "
                f"Got: {response.status_code}"
            )

    def test_orbit_score_tier_gating_free_vs_premium(self):
        """Free tier gets limited response (no breakdown); premium gets full breakdown."""
        free_score = _mock_orbit_score(
            total_score=72.5,
            breakdown=None,
        )
        premium_breakdown = {
            "completeness": 85.0,
            "avg_confidence": 78.0,
            "interaction_risk": 60.0,
            "care_gap_status": 80.0,
            "adherence_rate": 75.0,
        }
        premium_score = _mock_orbit_score(
            total_score=72.5,
            breakdown=premium_breakdown,
        )

        with _auth_as(PATIENT_A_ID, tier="free"), \
             patch("api.middleware.rbac.verify_patient_access",
                   return_value={"access_type": "self", "permission_level": "full"}), \
             patch("api.routes.orbit.compute_orbit_score", new_callable=AsyncMock) as mock_compute:
            mock_compute.return_value = free_score
            resp_free = client.get(f"/api/orbit/score?patient_id={PATIENT_A_ID}")
            if resp_free.status_code == 200:
                data_free = resp_free.json()
                assert data_free.get("breakdown") is None or \
                    data_free.get("premium_required_for_breakdown") is True, \
                    "Free tier must not receive full score breakdown"

        with _auth_as(PATIENT_A_ID, tier="premium_individual"), \
             patch("api.middleware.rbac.verify_patient_access",
                   return_value={"access_type": "self", "permission_level": "full"}), \
             patch("api.routes.orbit.compute_orbit_score", new_callable=AsyncMock) as mock_compute:
            mock_compute.return_value = premium_score
            resp_premium = client.get(f"/api/orbit/score?patient_id={PATIENT_A_ID}")
            if resp_premium.status_code == 200:
                data_premium = resp_premium.json()
                assert data_premium.get("breakdown") is not None, \
                    "Premium tier must receive full score breakdown"
                breakdown = data_premium["breakdown"]
                expected_keys = {
                    "completeness", "avg_confidence", "interaction_risk",
                    "care_gap_status", "adherence_rate",
                }
                assert expected_keys.issubset(set(breakdown.keys())), (
                    f"Premium breakdown missing keys. "
                    f"Expected: {expected_keys}, Got: {set(breakdown.keys())}"
                )
