"""
E2E UI Test Plans — Onboarding & Auth Flow
==========================================
These test plans are designed to be run via Playwright (runTest).
Each test case documents the steps, selectors (data-testid), and expected outcomes.

Test Coverage:
- TC-OB-001: New user registration redirects to /onboarding
- TC-OB-002: Onboarding form shows 4 mandatory fields
- TC-OB-003: Filling all mandatory fields + submit redirects to dashboard
- TC-OB-004: Skip button goes to dashboard with banner visible
- TC-OB-005: Ramesh login skips onboarding, goes to dashboard
- TC-OB-006: Dashboard shows onboarding banner for incomplete profile
- TC-OB-007: Optional fields section expands/collapses
- TC-OB-008: Validation errors shown for empty mandatory fields
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from uuid import uuid4

client = TestClient(app)


ONBOARDING_TEST_PLANS = {
    "TC-OB-001": {
        "name": "New user registration redirects to onboarding",
        "steps": [
            "[New Context] Create a new browser context",
            "[Browser] Navigate to /register",
            "[Verify] Assert button with data-testid='button-register' is visible",
            "[Browser] Fill [data-testid='input-name'] with 'Test User'",
            "[Browser] Fill [data-testid='input-email'] with random email",
            "[Browser] Fill [data-testid='input-password'] with 'TestPass123!'",
            "[Browser] Click [data-testid='button-register']",
            "[Verify] Wait for URL to contain '/onboarding' (up to 5s)",
        ],
        "selectors": {
            "register_button": "button-register",
            "name_input": "input-name",
            "email_input": "input-email",
            "password_input": "input-password",
        },
    },
    "TC-OB-002": {
        "name": "Onboarding form shows 4 mandatory fields",
        "steps": [
            "[Browser] After registration, on /onboarding page",
            "[Verify] Assert [data-testid='text-onboarding-title'] contains 'Complete Your Profile'",
            "[Verify] Assert [data-testid='input-date-of-birth'] is visible",
            "[Verify] Assert [data-testid='select-gender'] is visible",
            "[Verify] Assert [data-testid='select-language'] is visible",
            "[Verify] Assert [data-testid='select-literacy'] is visible",
            "[Verify] Assert [data-testid='button-submit-profile'] is visible",
            "[Verify] Assert [data-testid='button-skip-onboarding'] is visible",
        ],
        "selectors": {
            "title": "text-onboarding-title",
            "dob": "input-date-of-birth",
            "gender": "select-gender",
            "language": "select-language",
            "literacy": "select-literacy",
            "submit": "button-submit-profile",
            "skip": "button-skip-onboarding",
        },
    },
    "TC-OB-003": {
        "name": "Filling mandatory fields + submit redirects to dashboard",
        "steps": [
            "[Browser] On /onboarding page",
            "[Browser] Enter '1990-05-15' in [data-testid='input-date-of-birth']",
            "[Browser] Click [data-testid='select-gender'], select 'Male'",
            "[Browser] Click [data-testid='select-language'], select 'Hindi'",
            "[Browser] Click [data-testid='select-literacy'], select option containing 'Basic'",
            "[Browser] Click [data-testid='button-submit-profile']",
            "[Verify] Wait for URL to be '/' (dashboard)",
            "[Verify] Assert [data-testid='text-dashboard-title'] is visible",
            "[Verify] Assert [data-testid='text-onboarding-banner'] does NOT exist",
        ],
        "selectors": {
            "dob": "input-date-of-birth",
            "gender": "select-gender",
            "language": "select-language",
            "literacy": "select-literacy",
            "submit": "button-submit-profile",
            "dashboard_title": "text-dashboard-title",
            "banner": "text-onboarding-banner",
        },
    },
    "TC-OB-004": {
        "name": "Skip button goes to dashboard with banner",
        "steps": [
            "[New Context] Register new user, navigate to /onboarding",
            "[Browser] Click [data-testid='button-skip-onboarding']",
            "[Verify] URL is '/' (dashboard)",
            "[Verify] Assert [data-testid='text-dashboard-title'] is visible",
            "[Verify] Assert [data-testid='text-onboarding-banner'] IS visible",
            "[Verify] Assert [data-testid='link-complete-profile'] is visible",
        ],
        "selectors": {
            "skip": "button-skip-onboarding",
            "dashboard_title": "text-dashboard-title",
            "banner": "text-onboarding-banner",
            "complete_link": "link-complete-profile",
        },
    },
    "TC-OB-005": {
        "name": "Ramesh login skips onboarding",
        "steps": [
            "[New Context] Create a new browser context",
            "[Browser] Navigate to /",
            "[Verify] Login form visible with [data-testid='button-login']",
            "[Browser] Fill [data-testid='input-email'] with 'ramesh@careorbit.dev'",
            "[Browser] Fill [data-testid='input-password'] with 'Ramesh123!'",
            "[Browser] Click [data-testid='button-login']",
            "[Verify] URL is '/' (NOT /onboarding)",
            "[Verify] [data-testid='text-dashboard-title'] contains 'Welcome back, Ramesh Kumar'",
            "[Verify] [data-testid='text-onboarding-banner'] does NOT exist",
        ],
        "selectors": {
            "login_button": "button-login",
            "email_input": "input-email",
            "password_input": "input-password",
            "dashboard_title": "text-dashboard-title",
            "banner": "text-onboarding-banner",
        },
    },
    "TC-OB-006": {
        "name": "Dashboard shows onboarding banner for incomplete profile",
        "steps": [
            "[New Context] Register new user",
            "[Browser] Navigate to / (skip onboarding)",
            "[Verify] Assert [data-testid='text-onboarding-banner'] text contains 'Complete your profile'",
            "[Verify] Assert [data-testid='link-complete-profile'] links to /onboarding",
        ],
        "selectors": {
            "banner": "text-onboarding-banner",
            "complete_link": "link-complete-profile",
        },
    },
    "TC-OB-007": {
        "name": "Optional fields section expands/collapses",
        "steps": [
            "[Browser] On /onboarding page",
            "[Verify] Assert [data-testid='input-height'] is NOT visible (collapsed)",
            "[Browser] Click [data-testid='button-toggle-optional']",
            "[Verify] Assert [data-testid='input-height'] IS visible (expanded)",
            "[Verify] Assert [data-testid='input-weight'] IS visible",
            "[Verify] Assert [data-testid='select-blood-type'] IS visible",
            "[Verify] Assert [data-testid='input-city'] IS visible",
            "[Browser] Click [data-testid='button-toggle-optional'] again",
            "[Verify] Assert [data-testid='input-height'] is NOT visible (collapsed again)",
        ],
        "selectors": {
            "toggle": "button-toggle-optional",
            "height": "input-height",
            "weight": "input-weight",
            "blood_type": "select-blood-type",
            "city": "input-city",
        },
    },
    "TC-OB-008": {
        "name": "Validation errors shown for empty mandatory fields",
        "steps": [
            "[Browser] On /onboarding page with no fields filled",
            "[Browser] Click [data-testid='button-submit-profile']",
            "[Verify] Assert [data-testid='error-date-of-birth'] is visible",
            "[Verify] Assert [data-testid='error-gender'] is visible",
            "[Verify] Assert [data-testid='error-language'] is visible",
            "[Verify] Assert [data-testid='error-literacy'] is visible",
            "[Verify] URL remains /onboarding (no redirect)",
        ],
        "selectors": {
            "submit": "button-submit-profile",
            "error_dob": "error-date-of-birth",
            "error_gender": "error-gender",
            "error_language": "error-language",
            "error_literacy": "error-literacy",
        },
    },
}


class TestOnboardingAPIBackend:
    """Backend-verifiable tests for the onboarding flow."""

    def test_tc_ob_001_register_returns_onboarding_false(self):
        """TC-OB-001 backend: Register response includes onboarding_complete=false."""
        response = client.post("/api/auth/register", json={
            "name": "Onboard Test",
            "email": f"ob001.{uuid4().hex[:8]}@example.com",
            "password": "StrongPass123!",
            "phone_number": "+919876543210"
        })
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["user"]["onboarding_complete"] is False

    def test_tc_ob_003_submit_profile_completes_onboarding(self):
        """TC-OB-003 backend: PUT profile with all mandatory fields → onboarding_complete=true."""
        auth = client.post("/api/auth/register", json={
            "name": "Onboard Submit",
            "email": f"ob003.{uuid4().hex[:8]}@example.com",
            "password": "StrongPass123!",
            "phone_number": "+919876543210"
        }).json()
        headers = {"Authorization": f"Bearer {auth['access_token']}"}
        response = client.put("/api/patients/profile", headers=headers, json={
            "date_of_birth": "1990-05-15",
            "gender": "male",
            "preferred_language": "hi",
            "medical_literacy_level": "basic"
        })
        assert response.status_code == 200
        assert response.json()["onboarding_complete"] is True

    def test_tc_ob_005_ramesh_login_onboarding_true(self):
        """TC-OB-005 backend: Ramesh login returns onboarding_complete=true."""
        response = client.post("/api/auth/login", json={
            "email": "ramesh@careorbit.dev",
            "password": "Ramesh123!"
        })
        assert response.status_code == 200
        assert response.json()["user"]["onboarding_complete"] is True

    def test_tc_ob_006_skip_leaves_profile_incomplete(self):
        """TC-OB-006 backend: Skipping onboarding leaves profile incomplete."""
        auth = client.post("/api/auth/register", json={
            "name": "Skip Test",
            "email": f"ob006.{uuid4().hex[:8]}@example.com",
            "password": "StrongPass123!",
            "phone_number": "+919876543210"
        }).json()
        headers = {"Authorization": f"Bearer {auth['access_token']}"}
        response = client.get("/api/patients/profile", headers=headers)
        assert response.status_code == 200
        assert response.json()["onboarding_complete"] is False
