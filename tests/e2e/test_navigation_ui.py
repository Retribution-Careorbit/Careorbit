"""
E2E UI Test Plans — Sidebar, Navigation, Theme
===============================================
These test plans are designed to be run via Playwright (runTest).
Each test case documents the steps, selectors, and expected outcomes
for the premium sidebar and navigation redesign.

Test Coverage:
- TC-NAV-001: Sidebar renders with all 7 nav items
- TC-NAV-002: Clicking nav item navigates to correct page
- TC-NAV-003: Active nav item is visually highlighted
- TC-NAV-004: Sidebar collapse/expand on mobile
- TC-NAV-005: Theme toggle switches between light/dark mode
- TC-NAV-006: Dark mode persists across page navigation
- TC-NAV-007: Sidebar user profile section shows email
- TC-NAV-008: Sign out button works
- TC-NAV-009: Sidebar has smooth hover animations
- TC-NAV-010: Active indicator slides to selected item
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from uuid import uuid4

client = TestClient(app)

RAMESH_CREDENTIALS = {
    "email": "ramesh@careorbit.dev",
    "password": "Ramesh123!"
}

NAV_ITEMS = [
    {"label": "Dashboard", "path": "/", "testid": "nav-dashboard"},
    {"label": "Medications", "path": "/medications", "testid": "nav-medications"},
    {"label": "Documents", "path": "/documents", "testid": "nav-documents"},
    {"label": "AI Chat", "path": "/chat", "testid": "nav-ai-chat"},
    {"label": "Reminders", "path": "/reminders", "testid": "nav-reminders"},
    {"label": "Lab Reports", "path": "/test-cases", "testid": "nav-test-cases"},
    {"label": "Settings", "path": "/settings", "testid": "nav-settings"},
]

NAVIGATION_TEST_PLANS = {
    "TC-NAV-001": {
        "name": "Sidebar renders with all 7 nav items",
        "steps": [
            "[New Context] Login as Ramesh",
            "[Browser] Navigate to /",
            "[Verify] Sidebar is visible",
            "[Verify] Assert 7 nav items present:",
            f"  - {', '.join(item['label'] for item in NAV_ITEMS)}",
            "[Verify] Each item has an icon and a label",
            "[Verify] CareOrbit logo/brand is visible at top",
        ],
    },
    "TC-NAV-002": {
        "name": "Clicking nav item navigates to correct page",
        "steps": [
            "[Browser] On dashboard (logged in)",
            "[Browser] Click 'Medications' nav item",
            "[Verify] URL changes to /medications",
            "[Verify] Medications page content is visible",
            "[Browser] Click 'Documents' nav item",
            "[Verify] URL changes to /documents",
            "[Browser] Click 'AI Chat' nav item",
            "[Verify] URL changes to /chat",
            "[Browser] Click 'Dashboard' nav item",
            "[Verify] URL returns to /",
        ],
    },
    "TC-NAV-003": {
        "name": "Active nav item is visually highlighted",
        "steps": [
            "[Browser] Navigate to /medications",
            "[Verify] 'Medications' nav item has active/selected visual state",
            "[Verify] Active state includes background highlight or indicator bar",
            "[Verify] Other nav items do NOT have active state",
            "[Browser] Navigate to /chat",
            "[Verify] 'AI Chat' now has active state",
            "[Verify] 'Medications' no longer has active state",
        ],
        "expected_css": {
            "active": "background-color or border-left indicator",
            "inactive": "transparent background",
        },
    },
    "TC-NAV-004": {
        "name": "Sidebar collapse/expand on mobile",
        "viewport": {"width": 400, "height": 720},
        "steps": [
            "[Browser] Set viewport to 400x720 (mobile)",
            "[Browser] Navigate to / (logged in)",
            "[Verify] Sidebar is collapsed/hidden by default",
            "[Verify] Hamburger menu trigger is visible",
            "[Browser] Click hamburger menu trigger",
            "[Verify] Sidebar slides in from left",
            "[Browser] Click a nav item (e.g., Medications)",
            "[Verify] Sidebar closes after navigation",
            "[Verify] Page content is visible (not obscured)",
        ],
    },
    "TC-NAV-005": {
        "name": "Theme toggle switches between light/dark mode",
        "steps": [
            "[Browser] On any page (logged in)",
            "[Verify] Note current theme (light by default)",
            "[Browser] Click theme toggle button [data-testid='button-theme-toggle']",
            "[Verify] Page switches to dark mode",
            "[Verify] Background becomes dark, text becomes light",
            "[Verify] Cards and sidebar adapt to dark theme",
            "[Browser] Click theme toggle again",
            "[Verify] Page returns to light mode",
        ],
        "selectors": {
            "theme_toggle": "button-theme-toggle",
        },
    },
    "TC-NAV-006": {
        "name": "Dark mode persists across page navigation",
        "steps": [
            "[Browser] Toggle to dark mode",
            "[Browser] Navigate to /medications",
            "[Verify] Page is still in dark mode",
            "[Browser] Navigate to /chat",
            "[Verify] Page is still in dark mode",
            "[Browser] Navigate to /settings",
            "[Verify] Page is still in dark mode",
            "[Verify] Theme toggle shows 'Light Mode' option (sun icon)",
        ],
    },
    "TC-NAV-007": {
        "name": "Sidebar user profile section shows email",
        "steps": [
            "[Browser] On any page (logged in as Ramesh)",
            "[Verify] Sidebar footer shows user email 'ramesh@careorbit.dev'",
            "[Verify] Email is styled as secondary/muted text",
        ],
    },
    "TC-NAV-008": {
        "name": "Sign out button works",
        "steps": [
            "[Browser] On any page (logged in)",
            "[Browser] Click [data-testid='button-sign-out-sidebar'] in sidebar",
            "[Verify] User is logged out",
            "[Verify] URL redirects to / (login page)",
            "[Verify] Login form is visible (not dashboard)",
            "[Verify] localStorage tokens are cleared",
        ],
        "selectors": {
            "sign_out": "button-sign-out-sidebar",
        },
    },
    "TC-NAV-009": {
        "name": "Sidebar has smooth hover animations",
        "steps": [
            "[Browser] On dashboard",
            "[Browser] Hover over 'Medications' nav item",
            "[Verify] Item shows hover state (background change, slight scale/lift)",
            "[Verify] Hover transition is smooth (200-300ms)",
            "[Browser] Move mouse away",
            "[Verify] Item smoothly returns to default state",
        ],
    },
    "TC-NAV-010": {
        "name": "Active indicator slides to selected item",
        "steps": [
            "[Browser] On dashboard (Dashboard nav item active)",
            "[Browser] Click 'Medications' nav item",
            "[Verify] Active indicator slides from Dashboard to Medications",
            "[Verify] Slide animation is smooth (300ms, ease-in-out)",
            "[Verify] No visual glitch during transition",
        ],
    },
}


class TestNavigationAPIBackend:
    """Backend-verifiable tests for navigation-related API endpoints."""

    def test_tc_nav_001_all_api_routes_accessible(self):
        """TC-NAV-001 backend: All main API routes return valid responses for authenticated user."""
        auth = client.post("/api/auth/login", json=RAMESH_CREDENTIALS).json()
        headers = {"Authorization": f"Bearer {auth['access_token']}"}
        routes = [
            ("/api/patients/overview", 200),
            ("/api/patients/medications", 200),
            ("/api/reminders/list", 200),
            ("/api/subscriptions/current", 200),
            ("/api/subscriptions/plans", 200),
        ]
        for route, expected_status in routes:
            resp = client.get(route, headers=headers)
            assert resp.status_code == expected_status, f"{route} returned {resp.status_code}"

    def test_tc_nav_005_login_returns_token(self):
        """TC-NAV-005 backend: Login returns access token for authenticated navigation."""
        resp = client.post("/api/auth/login", json=RAMESH_CREDENTIALS)
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert len(data["access_token"]) > 20

    def test_tc_nav_008_logout_invalidates_refresh(self):
        """TC-NAV-008 backend: POST /api/auth/logout invalidates refresh token."""
        auth = client.post("/api/auth/login", json=RAMESH_CREDENTIALS).json()
        headers = {"Authorization": f"Bearer {auth['access_token']}"}
        resp = client.post("/api/auth/logout", headers=headers,
                           json={"refresh_token": auth["refresh_token"]})
        assert resp.status_code == 200
        reuse = client.post("/api/auth/refresh",
                            json={"refresh_token": auth["refresh_token"]})
        assert reuse.status_code in (401, 403)

    def test_tc_nav_007_login_returns_email(self):
        """TC-NAV-007 backend: Login response includes user email for sidebar display."""
        auth = client.post("/api/auth/login", json=RAMESH_CREDENTIALS).json()
        assert "user" in auth
        assert auth["user"]["email"] == "ramesh@careorbit.dev"

    def test_tc_nav_unauthenticated_routes_blocked(self):
        """Unauthenticated requests to protected routes are rejected."""
        routes = [
            "/api/patients/overview",
            "/api/patients/medications",
            "/api/reminders/list",
            "/api/subscriptions/current",
        ]
        for route in routes:
            resp = client.get(route)
            assert resp.status_code in (401, 403), f"{route} should require auth"
