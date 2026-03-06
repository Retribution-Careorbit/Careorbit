from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timezone, timedelta
from typing import Optional

import api.middleware.auth as auth_mod
import api.middleware.rbac as rbac_mod
from db.seed_demo import (
    DEMO_USER_ID, RAMESH_ORBIT_HISTORY, RAMESH_NARRATIVE,
    get_phig_for_orbit,
)

router = APIRouter(prefix="/api/orbit", tags=["orbit"])


async def compute_orbit_score(patient_id: str, user_tier: str = "free") -> dict:
    from graph.orbit_score import OrbitScoreCalculator
    # DEMO SEED — remove when Azure + DB available
    if patient_id == DEMO_USER_ID:
        phig = get_phig_for_orbit()
        phig["reminders"] = None
    else:
        phig = {"nodes": [], "interactions": [], "care_gaps": [], "reminders": None}
    # END DEMO SEED
    calc = OrbitScoreCalculator(phig)
    score = calc.compute()
    if user_tier == "free":
        score["breakdown"] = None
        score["premium_required_for_breakdown"] = True
    return score


async def get_score_history(patient_id: str, days: int = 30) -> list:
    # DEMO SEED — remove when Azure + DB available
    if patient_id == DEMO_USER_ID:
        return RAMESH_ORBIT_HISTORY
    # END DEMO SEED
    return []


async def create_appointment(patient_id: str, data: dict) -> dict:
    from uuid import uuid4
    appt_dt = data.get("appointment_datetime")
    brief_scheduled = False
    if appt_dt:
        try:
            dt = datetime.fromisoformat(appt_dt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if (dt - datetime.now(timezone.utc)) <= timedelta(hours=48):
                brief_scheduled = True
                await schedule_previsit_brief(str(uuid4()), patient_id)
        except (ValueError, TypeError):
            pass
    return {
        "appointment_id": str(uuid4()),
        "brief_scheduled": brief_scheduled,
    }


async def get_living_narrative(patient_id: str) -> dict:
    # DEMO SEED — remove when Azure + DB available
    if patient_id == DEMO_USER_ID:
        return {
            "narrative": RAMESH_NARRATIVE,
            "trigger_event": "initial_profile_complete",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    # END DEMO SEED
    return {
        "narrative": "",
        "trigger_event": None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


async def schedule_previsit_brief(appointment_id: str, patient_id: str) -> bool:
    return True


class AppointmentCreate(BaseModel):
    doctor_name: str = Field(...)
    appointment_datetime: str = Field(...)
    clinic_name: Optional[str] = None


@router.get("/score")
async def get_orbit_score(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)
    result = await compute_orbit_score(patient_id, current_user.get("tier", "free"))
    return result


@router.get("/score/history")
async def get_orbit_score_history(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)
    history = await get_score_history(patient_id, days=30)
    return history


@router.post("/appointments")
async def post_appointment(request: Request, body: AppointmentCreate):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)
    await rbac_mod.require_permission(current_user["id"], patient_id, "edit")
    result = await create_appointment(patient_id, body.model_dump())
    return result


@router.get("/narrative")
async def get_narrative(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)
    result = await get_living_narrative(patient_id)
    return result
