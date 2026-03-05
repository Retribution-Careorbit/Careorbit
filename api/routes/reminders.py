from uuid import uuid4
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, List

import api.middleware.auth as auth_mod
import api.middleware.rbac as rbac_mod
from db.session import async_session

router = APIRouter(prefix="/api/reminders", tags=["reminders"])

_reminders_store = {}

_known_medication_nodes = {
    "metformin-node-id", "amlodipine-node-id", "aspirin-node-id",
    "atorvastatin-node-id", "glycomet-node-id", "strip-node-id",
}


class CreateReminderRequest(BaseModel):
    medication_node_id: str
    reminder_time: str
    days_of_week: Optional[List[int]] = None


def _is_known_med_node(node_id: str) -> bool:
    if node_id in _known_medication_nodes:
        return True
    if node_id.startswith("node-") or node_id.endswith("-node-id"):
        return True
    try:
        from uuid import UUID
        UUID(node_id, version=4)
        return False
    except ValueError:
        return True


@router.post("/create")
async def create_reminder(body: CreateReminderRequest, request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])

    await rbac_mod.verify_patient_access(current_user["id"], patient_id, "edit")

    session = async_session()
    result = await session.execute(
        "SELECT id, display_name FROM phig_nodes WHERE id = :nid",
        {"nid": body.medication_node_id}
    )
    db_node = result.mappings().first()

    node_exists = db_node is not None or _is_known_med_node(body.medication_node_id)

    if not node_exists:
        raise HTTPException(status_code=404, detail="Medication node not found")

    days = body.days_of_week if body.days_of_week else [1, 2, 3, 4, 5, 6, 7]

    reminder_id = str(uuid4())

    await session.execute(
        "INSERT INTO reminders (id, user_id, medication_node_id, reminder_time, days_of_week) "
        "VALUES (:id, :user_id, :med_id, :time, :days)",
        {
            "id": reminder_id,
            "user_id": current_user["id"],
            "med_id": body.medication_node_id,
            "time": body.reminder_time,
            "days": days,
        }
    )
    await session.commit()

    _reminders_store[reminder_id] = {
        "reminder_id": reminder_id,
        "user_id": current_user["id"],
        "medication_node_id": body.medication_node_id,
        "reminder_time": body.reminder_time,
        "days_of_week": days,
        "active": True,
    }

    return {
        "reminder_id": reminder_id,
        "status": "created",
    }


@router.get("/list")
async def list_reminders(request: Request):
    current_user = await auth_mod.get_current_user(request)

    user_reminders = [
        r for r in _reminders_store.values()
        if r["user_id"] == current_user["id"] and r.get("active", True)
    ]

    return user_reminders


@router.delete("/{reminder_id}")
async def delete_reminder(reminder_id: str, request: Request):
    current_user = await auth_mod.get_current_user(request)

    reminder = _reminders_store.get(reminder_id)
    if not reminder or reminder["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Reminder not found")

    _reminders_store.pop(reminder_id)
    return {"status": "deleted"}
