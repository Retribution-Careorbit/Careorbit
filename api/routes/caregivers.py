from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

import api.middleware.auth as auth_mod
import api.middleware.rbac as rbac_mod
from db.session import async_session

router = APIRouter(prefix="/api/caregivers", tags=["caregivers"])

_caregiver_links = []

VALID_RELATIONSHIPS = ["spouse", "son", "daughter", "parent", "sibling", "other"]
VALID_PERMISSIONS = ["view", "edit", "full"]


class AddCaregiverRequest(BaseModel):
    caregiver_email: str
    relationship: str
    permission_level: str = "view"


async def enforce_caregiver_limit(user_id: str, tier: str):
    from utils.tier_config import get_tier_limits
    limits = get_tier_limits(tier)
    max_caregivers = limits.get("max_caregivers", 2)
    current = sum(1 for link in _caregiver_links if link["patient_id"] == user_id and not link.get("revoked"))
    if current >= max_caregivers:
        raise HTTPException(status_code=403, detail="Caregiver limit reached for your tier")


@router.post("/add")
async def add_caregiver(body: AddCaregiverRequest, request: Request):
    current_user = await auth_mod.get_current_user(request)

    if body.relationship not in VALID_RELATIONSHIPS:
        raise HTTPException(status_code=400, detail=f"Invalid relationship. Must be one of: {VALID_RELATIONSHIPS}")

    if body.permission_level not in VALID_PERMISSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid permission level. Must be one of: {VALID_PERMISSIONS}")

    from api.routes.auth import _users_store
    caregiver_user = None
    for u in _users_store.values():
        if u["email"] == body.caregiver_email:
            caregiver_user = u
            break

    caregiver_name = caregiver_user["name"] if caregiver_user else body.caregiver_email.split("@")[0]
    caregiver_id = caregiver_user["id"] if caregiver_user else body.caregiver_email

    _caregiver_links.append({
        "patient_id": current_user["id"],
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
    patients = [
        link for link in _caregiver_links
        if link["caregiver_id"] == current_user["id"] and not link.get("revoked")
    ]
    return patients


@router.get("/my-caregivers")
async def my_caregivers(request: Request):
    current_user = await auth_mod.get_current_user(request)
    caregivers = [
        link for link in _caregiver_links
        if link["patient_id"] == current_user["id"] and not link.get("revoked")
    ]
    return caregivers
