from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

import api.middleware.auth as auth_mod
import api.middleware.rbac as rbac_mod
from db.session import async_session
from db.seed_demo import FAMILY_CAREGIVER_LINKS

router = APIRouter(prefix="/api/caregivers", tags=["caregivers"])

_caregiver_links = [dict(link) for link in FAMILY_CAREGIVER_LINKS]

VALID_RELATIONSHIPS = ["spouse", "son", "daughter", "parent", "sibling", "other"]
VALID_PERMISSIONS = ["view", "edit", "full"]


class AddCaregiverRequest(BaseModel):
    caregiver_email: str
    relationship: str
    permission_level: str = "view"


def get_caregiver_links() -> list[dict]:
    return _caregiver_links


def get_active_caregiver_links() -> list[dict]:
    return [link for link in _caregiver_links if not link.get("revoked")]


async def enforce_caregiver_limit(user_id: str, tier: str):
    from utils.tier_config import get_tier_limits
    limits = get_tier_limits(tier)
    max_caregivers = limits.get("max_caregivers", 2)

    current = 0
    try:
        async with async_session() as session:
            result = await session.execute(
                "SELECT COUNT(*) as cnt FROM caregiver_links WHERE patient_id = :uid AND (revoked IS NULL OR revoked = false)",
                {"uid": user_id}
            )
            row = result.first()
            if row:
                if hasattr(row, "_mapping"):
                    current = dict(row._mapping).get("cnt", 0)
                elif isinstance(row, tuple):
                    current = row[0] if row[0] is not None else 0
                elif isinstance(row, (int, float)):
                    current = int(row)
    except Exception:
        current = sum(1 for link in _caregiver_links if link["patient_id"] == user_id and not link.get("revoked"))

    if current >= max_caregivers:
        raise HTTPException(status_code=429, detail={
            "error": "Caregiver limit reached",
            "limit": max_caregivers,
            "tier": tier,
        })


@router.post("/add")
async def add_caregiver(body: AddCaregiverRequest, request: Request):
    current_user = await auth_mod.get_current_user(request)

    patient_id = current_user["id"]
    tier = current_user.get("tier", "free")

    await enforce_caregiver_limit(patient_id, tier)

    if body.relationship not in VALID_RELATIONSHIPS:
        raise HTTPException(status_code=400, detail=f"Invalid relationship. Must be one of: {VALID_RELATIONSHIPS}")

    if body.permission_level not in VALID_PERMISSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid permission level. Must be one of: {VALID_PERMISSIONS}")

    from utils.tier_config import get_tier_limits
    limits = get_tier_limits(tier)
    max_caregivers = limits.get("max_caregivers", 2)

    active_links = [
        link for link in _caregiver_links
        if link["patient_id"] == patient_id and not link.get("revoked")
    ]

    from api.routes.auth import _users_store
    caregiver_user = None
    for u in _users_store.values():
        if u["email"] == body.caregiver_email:
            caregiver_user = u
            break

    if not caregiver_user:
        session = async_session()
        result = await session.execute(
            "SELECT id, name FROM users WHERE email = :email",
            {"email": body.caregiver_email}
        )
        db_user = result.mappings().first()
        if db_user:
            caregiver_user = db_user

    if not caregiver_user and len(active_links) >= max_caregivers:
        raise HTTPException(status_code=404, detail="Caregiver email not registered")

    caregiver_name = caregiver_user["name"] if caregiver_user else body.caregiver_email.split("@")[0]
    caregiver_id = caregiver_user.get("id", body.caregiver_email) if caregiver_user else body.caregiver_email

    _caregiver_links.append({
        "patient_id": patient_id,
        "caregiver_id": caregiver_id,
        "caregiver_name": caregiver_name,
        "relationship": body.relationship,
        "permission_level": body.permission_level,
        "revoked": False,
    })

    return {
        "status": "added",
        "caregiver_name": caregiver_name,
        "permission_level": body.permission_level,
    }


@router.delete("/{caregiver_id}")
async def revoke_caregiver(caregiver_id: str, request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])

    await rbac_mod.verify_patient_access(current_user["id"], patient_id, "full")

    for link in _caregiver_links:
        if link["caregiver_id"] == caregiver_id and link["patient_id"] == current_user["id"]:
            link["revoked"] = True

    return {"status": "revoked"}


@router.get("/my-patients")
async def my_patients(request: Request):
    current_user = await auth_mod.get_current_user(request)
    from api.routes.auth import _users_store

    patients = [
        link for link in _caregiver_links
        if link["caregiver_id"] == current_user["id"] and not link.get("revoked")
    ]

    enriched = []
    for link in patients:
        patient_id = link.get("patient_id")
        patient_user = _users_store.get(patient_id, {})
        enriched.append({
            **link,
            "patient_id": patient_id,
            "patient_name": patient_user.get("name") or patient_id,
            "patient_email": patient_user.get("email"),
        })
    return enriched


@router.get("/my-caregivers")
async def my_caregivers(request: Request):
    current_user = await auth_mod.get_current_user(request)
    caregivers = [
        link for link in _caregiver_links
        if link["patient_id"] == current_user["id"] and not link.get("revoked")
    ]
    return caregivers
