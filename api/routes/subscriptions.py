from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

import api.middleware.auth as auth_mod
from utils.tier_config import TIER_LIMITS, get_tier_limits
from db.session import async_session

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])

_user_tiers = {}


class UpgradeRequest(BaseModel):
    tier: str


@router.get("/current")
async def get_current_subscription(request: Request):
    current_user = await auth_mod.get_current_user(request)
    tier = _user_tiers.get(current_user["id"], "free")
    limits = get_tier_limits(tier)

    return {
        "tier": tier,
        "features": {
            "shows_ads": limits["shows_ads"],
            "documents_per_month": limits["documents_per_month"],
            "summaries_per_month": limits["summaries_per_month"],
            "max_caregivers": limits["max_caregivers"],
            "data_retention_months": limits["data_retention_months"],
            "family_dashboard": limits["family_dashboard"],
        },
        "usage": {
            "documents": {"limit": limits["documents_per_month"]},
            "summaries": {"limit": limits["summaries_per_month"]},
        }
    }


@router.get("/plans")
async def get_plans():
    plans = []
    for tier_name, limits in TIER_LIMITS.items():
        plans.append({
            "tier": tier_name,
            "price_monthly_cents": limits["price_monthly_cents"],
            "shows_ads": limits["shows_ads"],
            "documents_per_month": limits["documents_per_month"],
            "summaries_per_month": limits["summaries_per_month"],
            "max_caregivers": limits["max_caregivers"],
            "data_retention_months": limits["data_retention_months"],
            "family_dashboard": limits["family_dashboard"],
        })
    return {"plans": plans}


@router.post("/upgrade")
async def upgrade_subscription(body: UpgradeRequest, request: Request):
    current_user = await auth_mod.get_current_user(request)

    if body.tier not in TIER_LIMITS:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {body.tier}")

    _user_tiers[current_user["id"]] = body.tier

    return {"tier": body.tier}
