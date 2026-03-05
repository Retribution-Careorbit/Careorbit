TIER_LIMITS = {
    "free": {
        "price_monthly_cents": 0,
        "shows_ads": True,
        "documents_per_month": 100,
        "summaries_per_month": 5,
        "max_caregivers": 2,
        "data_retention_months": 24,
        "family_dashboard": False,
    },
    "premium_individual": {
        "price_monthly_cents": 799,
        "shows_ads": False,
        "documents_per_month": None,
        "summaries_per_month": None,
        "max_caregivers": 5,
        "data_retention_months": None,
        "family_dashboard": False,
    },
    "premium_family": {
        "price_monthly_cents": 1999,
        "shows_ads": False,
        "documents_per_month": None,
        "summaries_per_month": None,
        "max_caregivers": 10,
        "data_retention_months": None,
        "family_dashboard": True,
    },
}


def get_tier_limits(tier: str) -> dict:
    return TIER_LIMITS.get(tier, TIER_LIMITS["free"])


def get_limit(tier: str, feature: str):
    limits = get_tier_limits(tier)
    return limits.get(feature)


def check_feature_allowed(tier: str, feature: str) -> bool:
    limits = get_tier_limits(tier)
    value = limits.get(feature)
    if value is None:
        return True
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value > 0
    return bool(value)
