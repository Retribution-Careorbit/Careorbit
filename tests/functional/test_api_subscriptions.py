# tests/functional/test_api_subscriptions.py
# V4.1-B FIX: Subscriptions router IS registered in MVP v0.3.0 main.py.
# Page 123-124 of the PDF shows:
#   app.include_router(subscriptions.router, prefix="/api/subscriptions", ...)
# Removed @pytest.mark.demo_only for /current and /plans — these are real P0 CI gates.
# Removed the inline include_router fixture hack (caused duplicate route risk).
# EXCEPTION: TestTierUpgradeJourney remains @pytest.mark.demo_only because
# the payment system is explicitly Phase 3 ("OUT: Don't Build Yet") in the
# business model. The upgrade route in MVP creates the subscription record
# directly (demo mode) — not via Stripe/Razorpay.

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app  # v0.3.0 already includes subscriptions.router
from uuid import uuid4

client = TestClient(app)


class TestSubscriptionCurrent:
    """Tests for GET /api/subscriptions/current — real P0 CI gate."""

    def test_free_user_current_tier_is_free(self):
        with patch("api.middleware.auth.get_current_user",
                   return_value={"id": "free-user-id", "tier": "free"}), \
             patch("api.middleware.feature_gate.get_user_tier", return_value="free"), \
             patch("api.routes.subscriptions.async_session") as mock_session:
            session = AsyncMock()
            session.__aenter__ = AsyncMock(return_value=session)
            session.__aexit__ = AsyncMock(return_value=False)
            # No active subscription row -> defaults to free
            session.execute = AsyncMock(return_value=MagicMock(
                mappings=lambda: MagicMock(first=lambda: None)
            ))
            mock_session.return_value = session

            response = client.get("/api/subscriptions/current")
            assert response.status_code == 200
            data = response.json()
            assert data["tier"] == "free"

    def test_free_user_shows_ads(self):
        """Business model critical: free tier must surface shows_ads=True."""
        with patch("api.middleware.auth.get_current_user",
                   return_value={"id": "free-user-id", "tier": "free"}), \
             patch("api.middleware.feature_gate.get_user_tier", return_value="free"), \
             patch("api.routes.subscriptions.async_session") as mock_session:
            session = AsyncMock()
            session.__aenter__ = AsyncMock(return_value=session)
            session.__aexit__ = AsyncMock(return_value=False)
            session.execute = AsyncMock(return_value=MagicMock(
                mappings=lambda: MagicMock(first=lambda: None)
            ))
            mock_session.return_value = session

            response = client.get("/api/subscriptions/current")
            assert response.status_code == 200
            assert response.json()["features"]["shows_ads"] is True, \
                "Free tier must show ads — critical revenue requirement"

    def test_subscription_requires_auth(self):
        response = client.get("/api/subscriptions/current")
        assert response.status_code in (401, 403)


class TestSubscriptionPlans:
    """Tests for GET /api/subscriptions/plans — unauthenticated, real P0 gate."""

    def test_get_plans_returns_all_three_tiers(self):
        response = client.get("/api/subscriptions/plans")
        assert response.status_code == 200
        plans = response.json()["plans"]
        tiers = [p["tier"] for p in plans]
        assert "free" in tiers
        assert "premium_individual" in tiers
        assert "premium_family" in tiers

    def test_free_plan_price_is_zero(self):
        response = client.get("/api/subscriptions/plans")
        free_plan = next(p for p in response.json()["plans"] if p["tier"] == "free")
        assert free_plan["price_monthly_cents"] == 0

    def test_premium_individual_price_is_799_cents(self):
        """Business model: $7.99/month."""
        response = client.get("/api/subscriptions/plans")
        premium = next(
            p for p in response.json()["plans"]
            if p["tier"] == "premium_individual"
        )
        assert premium["price_monthly_cents"] == 799

    def test_family_plan_price_is_1999_cents(self):
        """Business model: $19.99/month for family."""
        response = client.get("/api/subscriptions/plans")
        family = next(
            p for p in response.json()["plans"]
            if p["tier"] == "premium_family"
        )
        assert family["price_monthly_cents"] == 1999


@pytest.mark.demo_only
class TestTierUpgradeJourney:
    """
    Upgrade flow stays @demo_only — payment system is Phase 3 (not built yet).
    The MVP upgrade route creates subscriptions directly in DB (demo mode only),
    not via Stripe/Razorpay. Keep excluded from default CI via pytest.ini marker.

    V4.1-B: Removed inline include_router hack. Standard client used.
    """

    @pytest.fixture(scope="class")
    def upgraded_user(self):
        """Register AND upgrade in fixture (V3 FIX H1)."""
        reg = client.post("/api/auth/register", json={
            "name": "Upgrade Journey Test",
            "email": f"upgrade.e2e.{uuid4().hex[:8]}@careorbit.dev",
            "password": "UpgradePass123!",
            "phone_number": "+919876543299"
        })
        assert reg.status_code in (200, 201, 202)
        tokens = reg.json()
        headers = {"Authorization": f"Bearer {tokens.get('access_token')}"}

        upgrade = client.post("/api/subscriptions/upgrade", json={
            "tier": "premium_individual", "billing_cycle": "monthly"
        }, headers=headers)
        assert upgrade.status_code == 200
        assert upgrade.json()["tier"] == "premium_individual"

        return {"headers": headers}

    def test_after_upgrade_ads_disabled(self, upgraded_user):
        with patch("api.middleware.feature_gate.get_user_tier",
                   return_value="premium_individual"):
            response = client.get(
                "/api/subscriptions/current",
                headers=upgraded_user["headers"]
            )
            assert response.status_code == 200
            assert response.json()["features"]["shows_ads"] is False

    def test_after_upgrade_document_limit_is_none(self, upgraded_user):
        with patch("api.middleware.feature_gate.get_user_tier",
                   return_value="premium_individual"), \
             patch("api.middleware.feature_gate.check_usage_limit",
                   return_value={"allowed": True, "current": 5, "limit": None}):
            response = client.get(
                "/api/subscriptions/current",
                headers=upgraded_user["headers"]
            )
            assert response.status_code == 200
            assert response.json()["usage"]["documents"]["limit"] is None
