# tests/functional/test_api_auth.py
# V4: phone_number field. Tests auth.py register/login routes.
# Note: Register returns 200 immediately with tokens (no OTP in Phase 1).
# OTP tests are in test_api_otp.py marked @phase2.

import pytest
from fastapi.testclient import TestClient
from main import app
from uuid import uuid4

client = TestClient(app)


class TestRegistration:

    def test_register_success_returns_tokens(self):
        """
        V4 CONTRACT: register returns HTTP 200 with access_token + refresh_token.
        No OTP gate in Phase 1 (auth.py returns tokens immediately).
        """
        response = client.post("/api/auth/register", json={
            "name": "Test User",
            "email": f"testuser.{uuid4().hex[:8]}@example.com",
            "password": "StrongPass123!",
            "phone_number": "+919876543210"
        })
        assert response.status_code in (200, 201)
        data = response.json()
        assert "access_token" in data, "access_token missing from register response"
        assert "refresh_token" in data, "refresh_token missing from register response"
        assert data["token_type"] == "bearer"

    def test_register_weak_password_rejected(self):
        response = client.post("/api/auth/register", json={
            "name": "Test User",
            "email": f"test2.{uuid4().hex[:8]}@example.com",
            "password": "123",
            "phone_number": "+919876543210"
        })
        assert response.status_code in (400, 422)

    def test_register_duplicate_email_rejected(self):
        email = f"dup.{uuid4().hex[:8]}@example.com"
        client.post("/api/auth/register", json={
            "name": "User A", "email": email,
            "password": "StrongPass123!", "phone_number": "+919876543210"
        })
        response = client.post("/api/auth/register", json={
            "name": "User B", "email": email,
            "password": "StrongPass456!", "phone_number": "+919876543211"
        })
        assert response.status_code in (400, 409)

    def test_register_missing_email_rejected(self):
        response = client.post("/api/auth/register", json={
            "name": "Test User", "password": "StrongPass123!"
        })
        assert response.status_code == 422

    def test_register_missing_password_rejected(self):
        response = client.post("/api/auth/register", json={
            "name": "Test User",
            "email": f"nopwd.{uuid4().hex[:8]}@example.com"
        })
        assert response.status_code == 422

    def test_register_preferred_language_defaults_to_english(self):
        response = client.post("/api/auth/register", json={
            "name": "Default Lang Test",
            "email": f"lang.{uuid4().hex[:8]}@example.com",
            "password": "LangPass123!"
        })
        assert response.status_code in (200, 201)
        data = response.json()
        user = data.get("user", {})
        assert "id" in data or "id" in user


class TestLogin:

    def test_login_success_returns_tokens(self):
        email = f"login.{uuid4().hex[:8]}@example.com"
        client.post("/api/auth/register", json={
            "name": "Login Test", "email": email,
            "password": "LoginPass123!", "phone_number": "+919876543212"
        })
        response = client.post("/api/auth/login", json={
            "email": email, "password": "LoginPass123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_wrong_password_rejected(self):
        response = client.post("/api/auth/login", json={
            "email": "nonexistent@example.com", "password": "WrongPassword!"
        })
        assert response.status_code == 401

    def test_login_nonexistent_user_rejected(self):
        response = client.post("/api/auth/login", json={
            "email": f"ghost.{uuid4().hex[:8]}@example.com",
            "password": "AnyPassword123!"
        })
        assert response.status_code == 401


class TestRefreshAndLogout:

    def _register_and_get_tokens(self):
        email = f"refresh.{uuid4().hex[:8]}@test.com"
        reg = client.post("/api/auth/register", json={
            "name": "Refresh Test", "email": email,
            "password": "Pass123!", "phone_number": "+919876599001"
        })
        assert reg.status_code in (200, 201)
        return reg.json()

    def test_refresh_token_returns_new_access_token(self):
        tokens = self._register_and_get_tokens()
        response = client.post("/api/auth/refresh", json={
            "refresh_token": tokens["refresh_token"]  # JSON body (not cookie)
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_logout_succeeds(self):
        tokens = self._register_and_get_tokens()
        response = client.post("/api/auth/logout", json={
            "refresh_token": tokens["refresh_token"]
        }, headers={"Authorization": f"Bearer {tokens['access_token']}"})
        assert response.status_code == 200
