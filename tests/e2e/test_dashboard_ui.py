"""
E2E UI Test Plans — Dashboard Premium UI
=========================================
These test plans are designed to be run via Playwright (runTest).
Each test case documents the steps, selectors (data-testid), and expected outcomes
for the premium dashboard redesign.

Test Coverage:
- TC-DB-001: Dashboard loads with 4 stat cards
- TC-DB-002: Stat cards display animated number values
- TC-DB-003: Stat cards have hover lift effect
- TC-DB-004: Quick actions section renders with links
- TC-DB-005: Skeleton loading states appear before data
- TC-DB-006: Page entrance animations (fade-in, stagger)
- TC-DB-007: Dark mode changes card backgrounds
- TC-DB-008: Mobile viewport shows single-column layout
- TC-DB-009: Welcome greeting shows user name
- TC-DB-010: Stat cards have gradient accent styling
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

RAMESH_CREDENTIALS = {
    "email": "ramesh@careorbit.dev",
    "password": "Ramesh123!"
}


def _login_ramesh():
    resp = client.post("/api/auth/login", json=RAMESH_CREDENTIALS)
    assert resp.status_code == 200
    return resp.json()


DASHBOARD_TEST_PLANS = {
    "TC-DB-001": {
        "name": "Dashboard loads with 4 stat cards",
        "steps": [
            "[New Context] Login as Ramesh (ramesh@careorbit.dev / Ramesh123!)",
            "[Browser] Navigate to / (dashboard)",
            "[Verify] Assert 4 stat cards are visible:",
            "  - [data-testid='text-stat-health-records'] exists",
            "  - [data-testid='text-stat-medications'] exists",
            "  - [data-testid='text-stat-reminders'] exists",
            "  - [data-testid='text-stat-subscription'] exists",
        ],
        "selectors": {
            "stat_health": "text-stat-health-records",
            "stat_meds": "text-stat-medications",
            "stat_reminders": "text-stat-reminders",
            "stat_sub": "text-stat-subscription",
        },
    },
    "TC-DB-002": {
        "name": "Stat cards display numeric values (with CountUp animation)",
        "steps": [
            "[Browser] On dashboard after data loads",
            "[Verify] Assert [data-testid='text-stat-health-records'] contains a number > 0",
            "[Verify] Assert [data-testid='text-stat-medications'] contains a number > 0",
            "[Verify] The numbers should animate from 0 to final value (CountUp)",
            "  - Take screenshot immediately on load → numbers near 0",
            "  - Take screenshot after 1s → numbers at final value",
        ],
        "selectors": {
            "stat_health": "text-stat-health-records",
            "stat_meds": "text-stat-medications",
        },
    },
    "TC-DB-003": {
        "name": "Stat cards have hover lift effect",
        "steps": [
            "[Browser] On dashboard",
            "[Browser] Hover over the first stat card",
            "[Verify] Assert card has translateY transform (negative value = lifted)",
            "[Verify] Assert card has elevated box-shadow compared to resting state",
            "[Browser] Move mouse away",
            "[Verify] Card returns to original position",
        ],
        "expected_css": {
            "hover": "transform: translateY(-4px); box-shadow: elevated",
            "rest": "transform: translateY(0); box-shadow: default",
        },
    },
    "TC-DB-004": {
        "name": "Quick actions section renders with links",
        "steps": [
            "[Browser] On dashboard",
            "[Verify] Assert [data-testid='link-quick-upload'] is visible",
            "[Verify] Assert [data-testid='link-quick-chat'] is visible",
            "[Verify] Upload link text contains 'Upload Document'",
            "[Verify] Chat link text contains 'Ask AI Assistant'",
            "[Browser] Click [data-testid='link-quick-upload']",
            "[Verify] URL changes to /documents",
        ],
        "selectors": {
            "upload_link": "link-quick-upload",
            "chat_link": "link-quick-chat",
        },
    },
    "TC-DB-005": {
        "name": "Skeleton loading states appear before data loads",
        "steps": [
            "[Browser] Navigate to dashboard with network throttling (slow 3G)",
            "[Verify] Assert Skeleton elements are visible while loading",
            "[Verify] After data loads, Skeleton elements replaced with actual content",
            "[Verify] No flash of empty state before Skeleton appears",
        ],
    },
    "TC-DB-006": {
        "name": "Page entrance animations (fade-in, stagger)",
        "steps": [
            "[Browser] Navigate to dashboard",
            "[Verify] Take screenshot at 0ms — cards should have opacity < 1 or be offset",
            "[Verify] Take screenshot at 500ms — cards should be fully visible",
            "[Verify] Cards appear in staggered sequence (1st before 4th)",
            "[Verify] Content fades in smoothly (opacity 0→1, translateY 20px→0)",
        ],
        "expected_animation": {
            "initial": {"opacity": 0, "translateY": "20px"},
            "final": {"opacity": 1, "translateY": "0px"},
            "stagger_delay": "0.1s",
        },
    },
    "TC-DB-007": {
        "name": "Dark mode changes card backgrounds and text colors",
        "steps": [
            "[Browser] On dashboard in light mode",
            "[Verify] Cards have light background color",
            "[Browser] Toggle dark mode (via Settings or sidebar toggle)",
            "[Verify] Cards have dark background color",
            "[Verify] Text color is light (white/gray) in dark mode",
            "[Verify] Primary accent color is consistent (brand pink/red)",
            "[Verify] No text becomes invisible (sufficient contrast)",
        ],
    },
    "TC-DB-008": {
        "name": "Mobile viewport shows single-column layout",
        "viewport": {"width": 400, "height": 720},
        "steps": [
            "[Browser] Set viewport to 400x720 (mobile)",
            "[Browser] Navigate to dashboard",
            "[Verify] Stat cards stack vertically (single column)",
            "[Verify] Quick actions stack vertically",
            "[Verify] Sidebar is collapsed (hamburger menu visible)",
            "[Verify] All content fits within viewport width (no horizontal scroll)",
            "[Verify] Touch targets are at least 44px height",
        ],
    },
    "TC-DB-009": {
        "name": "Welcome greeting shows user name",
        "steps": [
            "[Browser] Login as Ramesh",
            "[Browser] Navigate to /",
            "[Verify] [data-testid='text-dashboard-title'] contains 'Welcome back, Ramesh Kumar'",
        ],
        "selectors": {
            "title": "text-dashboard-title",
        },
    },
    "TC-DB-010": {
        "name": "Stat cards have gradient accent styling",
        "steps": [
            "[Browser] On dashboard",
            "[Verify] Each stat card has a subtle gradient border or accent",
            "[Verify] Icons have colored circular backgrounds",
            "[Verify] Cards have subtle glass morphism (backdrop-filter or translucent bg)",
            "[Verify] Visual hierarchy: icon → value → label → description",
        ],
        "expected_css": {
            "card": "backdrop-filter: blur() or bg-opacity",
            "icon_bg": "rounded-full with colored background",
        },
    },
}


class TestDashboardAPIBackend:
    """Backend-verifiable tests for dashboard data endpoints."""

    def test_tc_db_001_overview_returns_stats(self):
        """TC-DB-001 backend: GET /api/patients/overview returns stat data."""
        auth = _login_ramesh()
        headers = {"Authorization": f"Bearer {auth['access_token']}"}
        resp = client.get("/api/patients/overview", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "conditions" in data or "nodes" in data or "medications" in data or "total_nodes" in data

    def test_tc_db_002_medications_returns_list(self):
        """TC-DB-002 backend: GET /api/patients/medications returns medications with count > 0."""
        auth = _login_ramesh()
        headers = {"Authorization": f"Bearer {auth['access_token']}"}
        resp = client.get("/api/patients/medications", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "medications" in data
        assert len(data["medications"]) > 0

    def test_tc_db_004_reminders_endpoint_accessible(self):
        """TC-DB-004 backend: GET /api/reminders/list returns reminder data."""
        auth = _login_ramesh()
        headers = {"Authorization": f"Bearer {auth['access_token']}"}
        resp = client.get("/api/reminders/list", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_tc_db_004_subscription_endpoint_accessible(self):
        """TC-DB-004 backend: GET /api/subscriptions/current returns tier."""
        auth = _login_ramesh()
        headers = {"Authorization": f"Bearer {auth['access_token']}"}
        resp = client.get("/api/subscriptions/current", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "tier" in data

    def test_tc_db_009_login_returns_user_name(self):
        """TC-DB-009 backend: Login response includes user name for greeting."""
        auth = _login_ramesh()
        assert "user" in auth
        assert "name" in auth["user"]
        assert auth["user"]["name"] == "Ramesh Kumar"
