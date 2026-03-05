from fastapi import HTTPException
from db.session import async_session


async def verify_patient_access(user_id: str, patient_id: str = None, required_permission: str = "view") -> dict:
    if patient_id is None or user_id == patient_id:
        return {"access_type": "self", "permission_level": "full"}

    permission_hierarchy = {"view": 0, "edit": 1, "full": 2}

    session = async_session()
    result = await session.execute(
        "SELECT permission_level FROM caregiver_links WHERE caregiver_id = :cid AND patient_id = :pid AND revoked_at IS NULL",
        {"cid": user_id, "pid": patient_id}
    )
    row = result.mappings().first()

    if not row:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this patient's data."
        )

    granted_level = row.get("permission_level", "view") if isinstance(row, dict) else "view"
    required_rank = permission_hierarchy.get(required_permission, 0)
    granted_rank = permission_hierarchy.get(granted_level, 0)

    if granted_rank < required_rank:
        raise HTTPException(
            status_code=403,
            detail=f"Your permission level ({granted_level}) is insufficient."
        )

    return {"access_type": "caregiver", "permission_level": granted_level}
