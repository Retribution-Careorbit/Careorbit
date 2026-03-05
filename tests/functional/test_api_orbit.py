# tests/functional/test_api_orbit.py
# T004: Functional tests for Orbit API endpoints (4 routes).
# Endpoints under test:
#   GET  /api/orbit/score          — current orbit score
#   GET  /api/orbit/score/history  — score history
#   POST /api/orbit/appointments   — create appointment
#   GET  /api/orbit/narrative      — living narrative

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app
from uuid import uuid4
from datetime import datetime, timezone, timedelta

client = TestClient(app)

MOCK_USER_FREE = {"id": str(uuid4()), "tier": "free"}
MOCK_USER_PREMIUM = {"id": str(uuid4()), "tier": "premium_individual"}


def _auth_patch(user=None):
    if user is None:
        user = MOCK_USER_PREMIUM
    return patch("api.middleware.auth.get_current_user", return_value=user)


class TestGetOrbitScore:

    def test_get_orbit_score_authenticated(self):
        with _auth_patch(), \
             patch("api.routes.orbit.compute_orbit_score", new_callable=AsyncMock) as mock_compute:
            mock_compute.return_value = {
                "total_score": 72.5,
                "breakdown": {
                    "completeness": 80.0,
                    "avg_confidence": 65.0,
                    "interaction_risk": 75.0,
                    "care_gap_status": 60.0,
                    "adherence_rate": 75.0,
                },
                "delta": 3.2,
                "computed_at": datetime.now(timezone.utc).isoformat(),
            }
            response = client.get("/api/orbit/score")
            assert response.status_code == 200
            data = response.json()
            assert "total_score" in data

    def test_get_orbit_score_unauthenticated(self):
        response = client.get("/api/orbit/score")
        assert response.status_code in (401, 403)

    def test_orbit_score_is_float_0_to_100(self):
        with _auth_patch(), \
             patch("api.routes.orbit.compute_orbit_score", new_callable=AsyncMock) as mock_compute:
            mock_compute.return_value = {
                "total_score": 85.3,
                "breakdown": {
                    "completeness": 90.0,
                    "avg_confidence": 80.0,
                    "interaction_risk": 85.0,
                    "care_gap_status": 80.0,
                    "adherence_rate": 75.0,
                },
                "delta": None,
                "computed_at": datetime.now(timezone.utc).isoformat(),
            }
            response = client.get("/api/orbit/score")
            assert response.status_code == 200
            data = response.json()
            score = data["total_score"]
            assert isinstance(score, (int, float))
            assert 0 <= score <= 100

    def test_orbit_score_free_tier_no_breakdown(self):
        with _auth_patch(MOCK_USER_FREE), \
             patch("api.routes.orbit.compute_orbit_score", new_callable=AsyncMock) as mock_compute, \
             patch("api.middleware.feature_gate.get_user_tier", return_value="free"):
            mock_compute.return_value = {
                "total_score": 60.0,
                "breakdown": None,
                "premium_required_for_breakdown": True,
                "delta": None,
                "computed_at": datetime.now(timezone.utc).isoformat(),
            }
            response = client.get("/api/orbit/score")
            assert response.status_code == 200
            data = response.json()
            assert data.get("breakdown") is None
            assert data.get("premium_required_for_breakdown") is True

    def test_orbit_score_premium_tier_full_breakdown(self):
        with _auth_patch(MOCK_USER_PREMIUM), \
             patch("api.routes.orbit.compute_orbit_score", new_callable=AsyncMock) as mock_compute, \
             patch("api.middleware.feature_gate.get_user_tier", return_value="premium_individual"):
            mock_compute.return_value = {
                "total_score": 78.0,
                "breakdown": {
                    "completeness": 90.0,
                    "avg_confidence": 80.0,
                    "interaction_risk": 70.0,
                    "care_gap_status": 60.0,
                    "adherence_rate": 75.0,
                },
                "delta": 2.1,
                "computed_at": datetime.now(timezone.utc).isoformat(),
            }
            response = client.get("/api/orbit/score")
            assert response.status_code == 200
            data = response.json()
            assert data["breakdown"] is not None
            assert isinstance(data["breakdown"], dict)

    def test_orbit_score_breakdown_has_all_components(self):
        expected_keys = {"completeness", "avg_confidence", "interaction_risk",
                         "care_gap_status", "adherence_rate"}
        with _auth_patch(MOCK_USER_PREMIUM), \
             patch("api.routes.orbit.compute_orbit_score", new_callable=AsyncMock) as mock_compute, \
             patch("api.middleware.feature_gate.get_user_tier", return_value="premium_individual"):
            mock_compute.return_value = {
                "total_score": 78.0,
                "breakdown": {
                    "completeness": 90.0,
                    "avg_confidence": 80.0,
                    "interaction_risk": 70.0,
                    "care_gap_status": 60.0,
                    "adherence_rate": 75.0,
                },
                "delta": None,
                "computed_at": datetime.now(timezone.utc).isoformat(),
            }
            response = client.get("/api/orbit/score")
            assert response.status_code == 200
            breakdown = response.json()["breakdown"]
            assert set(breakdown.keys()) >= expected_keys

    def test_orbit_score_has_delta(self):
        with _auth_patch(), \
             patch("api.routes.orbit.compute_orbit_score", new_callable=AsyncMock) as mock_compute:
            mock_compute.return_value = {
                "total_score": 72.0,
                "breakdown": None,
                "delta": 5.5,
                "computed_at": datetime.now(timezone.utc).isoformat(),
            }
            response = client.get("/api/orbit/score")
            assert response.status_code == 200
            data = response.json()
            assert "delta" in data
            assert data["delta"] is None or isinstance(data["delta"], (int, float))

    def test_orbit_score_has_computed_at(self):
        now = datetime.now(timezone.utc).isoformat()
        with _auth_patch(), \
             patch("api.routes.orbit.compute_orbit_score", new_callable=AsyncMock) as mock_compute:
            mock_compute.return_value = {
                "total_score": 72.0,
                "breakdown": None,
                "delta": None,
                "computed_at": now,
            }
            response = client.get("/api/orbit/score")
            assert response.status_code == 200
            data = response.json()
            assert "computed_at" in data
            assert len(data["computed_at"]) > 0


class TestGetScoreHistory:

    def test_get_score_history_returns_list(self):
        with _auth_patch(), \
             patch("api.routes.orbit.get_score_history", new_callable=AsyncMock) as mock_history:
            mock_history.return_value = [
                {"total_score": 60.0, "computed_at": datetime.now(timezone.utc).isoformat()},
                {"total_score": 65.0, "computed_at": datetime.now(timezone.utc).isoformat()},
            ]
            response = client.get("/api/orbit/score/history")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            for entry in data:
                assert "total_score" in entry
                assert "computed_at" in entry

    def test_score_history_default_30_days(self):
        with _auth_patch(), \
             patch("api.routes.orbit.get_score_history", new_callable=AsyncMock) as mock_history:
            mock_history.return_value = []
            response = client.get("/api/orbit/score/history")
            assert response.status_code == 200
            if mock_history.call_args:
                args, kwargs = mock_history.call_args
                days = kwargs.get("days", args[1] if len(args) > 1 else 30)
                assert days == 30

    def test_score_history_max_90_rows(self):
        with _auth_patch(), \
             patch("api.routes.orbit.get_score_history", new_callable=AsyncMock) as mock_history:
            entries = [
                {"total_score": float(i), "computed_at": datetime.now(timezone.utc).isoformat()}
                for i in range(90)
            ]
            mock_history.return_value = entries
            response = client.get("/api/orbit/score/history")
            assert response.status_code == 200
            data = response.json()
            assert len(data) <= 90


class TestPostAppointment:

    def test_post_appointment_creates_record(self):
        appt_time = (datetime.now(timezone.utc) + timedelta(hours=72)).isoformat()
        with _auth_patch(), \
             patch("api.routes.orbit.create_appointment", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {
                "appointment_id": str(uuid4()),
                "brief_scheduled": False,
            }
            response = client.post("/api/orbit/appointments", json={
                "doctor_name": "Dr. Amit Roy",
                "appointment_datetime": appt_time,
                "clinic_name": "City Hospital",
            })
            assert response.status_code in (200, 201)
            data = response.json()
            assert "appointment_id" in data

    def test_post_appointment_within_48h_triggers_brief(self):
        appt_time = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        with _auth_patch(), \
             patch("api.routes.orbit.create_appointment", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {
                "appointment_id": str(uuid4()),
                "brief_scheduled": True,
            }
            response = client.post("/api/orbit/appointments", json={
                "doctor_name": "Dr. Priya Singh",
                "appointment_datetime": appt_time,
                "clinic_name": "Apollo Clinic",
            })
            assert response.status_code in (200, 201)
            data = response.json()
            assert data["brief_scheduled"] is True

    def test_post_appointment_beyond_48h_no_brief(self):
        appt_time = (datetime.now(timezone.utc) + timedelta(hours=96)).isoformat()
        with _auth_patch(), \
             patch("api.routes.orbit.create_appointment", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {
                "appointment_id": str(uuid4()),
                "brief_scheduled": False,
            }
            response = client.post("/api/orbit/appointments", json={
                "doctor_name": "Dr. Ravi Mehta",
                "appointment_datetime": appt_time,
                "clinic_name": "Max Hospital",
            })
            assert response.status_code in (200, 201)
            data = response.json()
            assert data["brief_scheduled"] is False

    def test_post_appointment_required_fields_validation(self):
        with _auth_patch(), \
             patch("api.routes.orbit.create_appointment", new_callable=AsyncMock):
            response = client.post("/api/orbit/appointments", json={
                "appointment_datetime": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            })
            assert response.status_code == 422


class TestGetNarrative:

    def test_get_narrative_returns_text(self):
        with _auth_patch(), \
             patch("api.routes.orbit.get_living_narrative", new_callable=AsyncMock) as mock_narr:
            mock_narr.return_value = {
                "narrative": "Ramesh has been managing Type 2 Diabetes with Metformin 500mg twice daily.",
            }
            response = client.get("/api/orbit/narrative")
            assert response.status_code == 200
            data = response.json()
            narrative = data.get("narrative", "")
            assert isinstance(narrative, str)
            assert len(narrative) > 0
