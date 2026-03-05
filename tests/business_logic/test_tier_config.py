# tests/business_logic/test_tier_config.py
# Tests TIER_LIMITS configuration constants from utils/tier_config.py.
# These are pure config unit tests — no live endpoints required.
# V4: Subscription live endpoint tests moved to test_api_subscriptions.py.

import pytest
from utils.tier_config import TIER_LIMITS, get_tier_limits, get_limit, check_feature_allowed


class TestTierLimitsConfiguration:
    """Validate tier configuration constants match business model."""

    def test_all_three_tiers_defined(self):
        assert "free" in TIER_LIMITS
        assert "premium_individual" in TIER_LIMITS
        assert "premium_family" in TIER_LIMITS

    def test_free_tier_shows_ads(self):
        """Business model: Free tier is ad-supported."""
        assert TIER_LIMITS["free"]["shows_ads"] is True

    def test_premium_individual_no_ads(self):
        """Business model: Premium Individual — 'Zero Advertisements'."""
        assert TIER_LIMITS["premium_individual"]["shows_ads"] is False

    def test_premium_family_no_ads(self):
        assert TIER_LIMITS["premium_family"]["shows_ads"] is False

    def test_free_tier_document_limit(self):
        """Business model: 100 documents/month on free tier."""
        assert TIER_LIMITS["free"]["documents_per_month"] == 100

    def test_premium_unlimited_documents(self):
        """Business model: Unlimited uploads on premium."""
        assert TIER_LIMITS["premium_individual"]["documents_per_month"] is None

    def test_free_tier_summary_limit(self):
        """Business model: 5 summaries/month on free."""
        assert TIER_LIMITS["free"]["summaries_per_month"] == 5

    def test_premium_unlimited_summaries(self):
        assert TIER_LIMITS["premium_individual"]["summaries_per_month"] is None

    def test_free_caregiver_limit(self):
        """Business model: max 2 caregivers on free."""
        assert TIER_LIMITS["free"]["max_caregivers"] == 2

    def test_premium_individual_caregiver_limit(self):
        """Business model: 5 caregivers on premium individual."""
        assert TIER_LIMITS["premium_individual"]["max_caregivers"] == 5

    def test_premium_family_caregiver_limit(self):
        """Business model: 10 caregivers on family plan."""
        assert TIER_LIMITS["premium_family"]["max_caregivers"] == 10

    def test_free_tier_data_retention_24_months(self):
        """Business model: 2-year rolling window on free."""
        assert TIER_LIMITS["free"]["data_retention_months"] == 24

    def test_premium_lifetime_data_retention(self):
        """Business model: Lifetime retention on premium."""
        assert TIER_LIMITS["premium_individual"]["data_retention_months"] is None

    def test_family_tier_has_family_dashboard(self):
        """Business model: Unified family dashboard — family plan only."""
        assert TIER_LIMITS["premium_family"]["family_dashboard"] is True
        assert TIER_LIMITS["premium_individual"]["family_dashboard"] is False
        assert TIER_LIMITS["free"]["family_dashboard"] is False

    def test_get_tier_limits_returns_free_for_unknown_tier(self):
        """get_tier_limits should default to free for unrecognized tiers."""
        result = get_tier_limits("enterprise_xyz")
        assert result == TIER_LIMITS["free"]

    def test_check_feature_allowed(self):
        assert check_feature_allowed("free", "shows_ads") is True
        assert check_feature_allowed("premium_individual", "shows_ads") is False
        assert check_feature_allowed("premium_family", "family_dashboard") is True
        assert check_feature_allowed("free", "family_dashboard") is False

    def test_get_limit_returns_none_for_unlimited(self):
        result = get_limit("premium_individual", "documents_per_month")
        assert result is None

    def test_get_limit_returns_value_for_bounded(self):
        result = get_limit("free", "documents_per_month")
        assert result == 100


class TestFeatureGateLogic:
    """Test the feature gate middleware functions."""

    async def test_check_usage_below_limit_is_allowed(self):
        """User with 50/100 docs used → allowed."""
        with __import__("unittest.mock", fromlist=["patch"]).patch(
            "api.middleware.feature_gate.get_user_tier",
            return_value="free"
        ), __import__("unittest.mock", fromlist=["patch"]).patch(
            "api.middleware.feature_gate.async_session"
        ) as mock_session:
            session = __import__("unittest.mock", fromlist=["AsyncMock"]).AsyncMock()
            session.__aenter__ = session.__aexit__ = session
            session.execute = __import__("unittest.mock", fromlist=["AsyncMock"]).AsyncMock(
                return_value=__import__("unittest.mock", fromlist=["MagicMock"]).MagicMock(
                    first=lambda: (50,)
                )
            )
            mock_session.return_value = session

            from api.middleware.feature_gate import check_usage_limit
            result = await check_usage_limit("user-id", "documents_per_month")
            assert result["allowed"] is True
            assert result["current"] == 50
            assert result["limit"] == 100

    async def test_check_usage_at_limit_is_denied(self):
        """User with 100/100 docs → denied."""
        with __import__("unittest.mock", fromlist=["patch"]).patch(
            "api.middleware.feature_gate.get_user_tier", return_value="free"
        ), __import__("unittest.mock", fromlist=["patch"]).patch(
            "api.middleware.feature_gate.async_session"
        ) as mock_session:
            session = __import__("unittest.mock", fromlist=["AsyncMock"]).AsyncMock()
            session.__aenter__ = session.__aexit__ = session
            session.execute = __import__("unittest.mock", fromlist=["AsyncMock"]).AsyncMock(
                return_value=__import__("unittest.mock", fromlist=["MagicMock"]).MagicMock(
                    first=lambda: (100,)
                )
            )
            mock_session.return_value = session

            from api.middleware.feature_gate import check_usage_limit
            result = await check_usage_limit("user-id", "documents_per_month")
            assert result["allowed"] is False

    async def test_premium_unlimited_always_allowed(self):
        """Premium user has no limit → always allowed."""
        with __import__("unittest.mock", fromlist=["patch"]).patch(
            "api.middleware.feature_gate.get_user_tier",
            return_value="premium_individual"
        ):
            from api.middleware.feature_gate import check_usage_limit
            result = await check_usage_limit("premium-user-id", "documents_per_month")
            assert result["allowed"] is True
            assert result["limit"] is None
