from db.session import async_session
from utils.tier_config import get_tier_limits


async def get_user_tier(user_id: str) -> str:
    session = async_session()
    result = await session.execute(
        "SELECT tier FROM users WHERE id = :uid",
        {"uid": user_id}
    )
    row = result.first()
    if row and isinstance(row, dict):
        return row.get("tier", "free")
    return "free"


async def check_usage_limit(user_id: str, resource_type: str) -> dict:
    tier = await get_user_tier(user_id)
    limits = get_tier_limits(tier)

    limit_value = limits.get(resource_type)

    if limit_value is None:
        return {"allowed": True, "current": 0, "limit": None}

    session = async_session()
    result = await session.execute(
        f"SELECT COUNT(*) FROM {resource_type}_usage WHERE user_id = :uid AND month = :month",
        {"uid": user_id, "month": "current"}
    )
    row = result.first()
    if isinstance(row, tuple):
        current = row[0] if row[0] is not None else 0
    elif isinstance(row, (int, float)):
        current = row
    else:
        current = 0

    return {
        "allowed": current < limit_value,
        "current": current,
        "limit": limit_value,
    }
