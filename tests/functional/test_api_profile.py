import pytest
from fastapi.testclient import TestClient
from main import app
from uuid import uuid4

client = TestClient(app)


def _register_user(email=None):
    if email is None:
        email = f"profile.{uuid4().hex[:8]}@example.com"
    response = client.post("/api/auth/register", json={
        "name": "Profile Test User",
        "email": email,
        "password": "StrongPass123!",
        "phone_number": "+919876543210"
    })
    assert response.status_code in (200, 201)
    data = response.json()
    return {
        "access_token": data["access_token"],
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
        "user": data["user"],
    }


class TestRegisterOnboardingFlag:

    def test_register_returns_onboarding_complete_false(self):
        auth = _register_user()
        assert auth["user"]["onboarding_complete"] is False

    def test_register_returns_user_name(self):
        auth = _register_user()
        assert auth["user"]["name"] == "Profile Test User"

    def test_register_returns_user_email(self):
        email = f"profile.name.{uuid4().hex[:8]}@example.com"
        auth = _register_user(email=email)
        assert auth["user"]["email"] == email


class TestLoginOnboardingFlag:

    def test_ramesh_login_onboarding_complete_true(self):
        response = client.post("/api/auth/login", json={
            "email": "ramesh@careorbit.dev",
            "password": "Ramesh123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["onboarding_complete"] is True

    def test_new_user_login_onboarding_complete_false(self):
        email = f"newlogin.{uuid4().hex[:8]}@example.com"
        client.post("/api/auth/register", json={
            "name": "New User",
            "email": email,
            "password": "StrongPass123!",
            "phone_number": "+919876543210"
        })
        response = client.post("/api/auth/login", json={
            "email": email,
            "password": "StrongPass123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["onboarding_complete"] is False


class TestGetProfile:

    def test_new_user_profile_empty(self):
        auth = _register_user()
        response = client.get("/api/patients/profile", headers=auth["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["onboarding_complete"] is False
        assert data["profile"]["date_of_birth"] is None
        assert data["profile"]["gender"] is None
        assert data["profile"]["medical_literacy_level"] is None
        assert data["profile"]["age"] is None

    def test_ramesh_profile_populated(self):
        response = client.post("/api/auth/login", json={
            "email": "ramesh@careorbit.dev",
            "password": "Ramesh123!"
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/patients/profile", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["onboarding_complete"] is True
        assert data["profile"]["gender"] == "male"
        assert data["profile"]["preferred_language"] == "hi"
        assert data["profile"]["medical_literacy_level"] == "basic"
        assert data["profile"]["date_of_birth"] == "1958-03-15"
        assert data["profile"]["age"] is not None
        assert data["profile"]["age"] >= 67

    def test_profile_requires_auth(self):
        response = client.get("/api/patients/profile")
        assert response.status_code in (401, 403, 422)


class TestUpdateProfileMandatory:

    def test_update_all_mandatory_fields_completes_onboarding(self):
        auth = _register_user()
        response = client.put("/api/patients/profile", headers=auth["headers"], json={
            "date_of_birth": "1990-05-15",
            "gender": "female",
            "preferred_language": "hi",
            "medical_literacy_level": "intermediate"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["onboarding_complete"] is True
        assert data["profile"]["date_of_birth"] == "1990-05-15"
        assert data["profile"]["gender"] == "female"
        assert data["profile"]["preferred_language"] == "hi"
        assert data["profile"]["medical_literacy_level"] == "intermediate"
        assert data["profile"]["age"] == 35

    def test_partial_mandatory_fields_stays_incomplete(self):
        auth = _register_user()
        response = client.put("/api/patients/profile", headers=auth["headers"], json={
            "date_of_birth": "1990-05-15",
            "gender": "male"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["onboarding_complete"] is False

    def test_incremental_updates_complete_onboarding(self):
        auth = _register_user()
        client.put("/api/patients/profile", headers=auth["headers"], json={
            "date_of_birth": "1985-10-20",
            "gender": "male"
        })
        client.put("/api/patients/profile", headers=auth["headers"], json={
            "preferred_language": "en"
        })
        response = client.put("/api/patients/profile", headers=auth["headers"], json={
            "medical_literacy_level": "advanced"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["onboarding_complete"] is True

    def test_login_after_profile_complete_shows_true(self):
        email = f"complete.{uuid4().hex[:8]}@example.com"
        auth = _register_user(email=email)
        client.put("/api/patients/profile", headers=auth["headers"], json={
            "date_of_birth": "1990-01-01",
            "gender": "other",
            "preferred_language": "ta",
            "medical_literacy_level": "basic"
        })
        response = client.post("/api/auth/login", json={
            "email": email,
            "password": "StrongPass123!"
        })
        assert response.status_code == 200
        assert response.json()["user"]["onboarding_complete"] is True


class TestUpdateProfileValidation:

    def test_invalid_date_of_birth_rejected(self):
        auth = _register_user()
        response = client.put("/api/patients/profile", headers=auth["headers"], json={
            "date_of_birth": "not-a-date"
        })
        assert response.status_code == 400

    def test_future_date_of_birth_rejected(self):
        auth = _register_user()
        response = client.put("/api/patients/profile", headers=auth["headers"], json={
            "date_of_birth": "2099-01-01"
        })
        assert response.status_code == 400

    def test_invalid_gender_rejected(self):
        auth = _register_user()
        response = client.put("/api/patients/profile", headers=auth["headers"], json={
            "gender": "invalid"
        })
        assert response.status_code == 400

    def test_invalid_language_rejected(self):
        auth = _register_user()
        response = client.put("/api/patients/profile", headers=auth["headers"], json={
            "preferred_language": "fr"
        })
        assert response.status_code == 400

    def test_invalid_literacy_level_rejected(self):
        auth = _register_user()
        response = client.put("/api/patients/profile", headers=auth["headers"], json={
            "medical_literacy_level": "expert"
        })
        assert response.status_code == 400

    def test_invalid_blood_type_rejected(self):
        auth = _register_user()
        response = client.put("/api/patients/profile", headers=auth["headers"], json={
            "blood_type": "C+"
        })
        assert response.status_code == 400

    def test_height_out_of_range_rejected(self):
        auth = _register_user()
        response = client.put("/api/patients/profile", headers=auth["headers"], json={
            "height_cm": 10.0
        })
        assert response.status_code == 400

    def test_weight_out_of_range_rejected(self):
        auth = _register_user()
        response = client.put("/api/patients/profile", headers=auth["headers"], json={
            "weight_kg": 600.0
        })
        assert response.status_code == 400


class TestUpdateProfileOptional:

    def test_optional_fields_stored(self):
        auth = _register_user()
        response = client.put("/api/patients/profile", headers=auth["headers"], json={
            "blood_type": "O+",
            "height_cm": 170.0,
            "weight_kg": 72.5,
            "city": "Mumbai",
            "state": "Maharashtra",
            "country": "IND"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["profile"]["blood_type"] == "O+"
        assert data["profile"]["height_cm"] == 170.0
        assert data["profile"]["weight_kg"] == 72.5
        assert data["profile"]["city"] == "Mumbai"
        assert data["profile"]["state"] == "Maharashtra"
        assert data["profile"]["country"] == "IND"

    def test_optional_fields_do_not_affect_onboarding(self):
        auth = _register_user()
        response = client.put("/api/patients/profile", headers=auth["headers"], json={
            "blood_type": "A+",
            "height_cm": 175.0,
            "weight_kg": 80.0
        })
        assert response.status_code == 200
        data = response.json()
        assert data["onboarding_complete"] is False

    def test_profile_requires_auth_for_update(self):
        response = client.put("/api/patients/profile", json={
            "gender": "male"
        })
        assert response.status_code in (401, 403, 422)
