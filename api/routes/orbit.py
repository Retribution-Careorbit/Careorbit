from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timezone, timedelta
from typing import Optional

import api.middleware.auth as auth_mod
import api.middleware.rbac as rbac_mod
from api.middleware.localization import localize_payload_for_patient
from db.seed_demo import (
    FAMILY_MEMBER_IDS,
    get_seed_list_for_patient,
    get_seed_value_for_patient,
)
from api.routes.reminders import get_adherence_snapshot_for_patient
from graph.phig_builder import phig_builder
from db.runtime_store import get_orbit_score_history as get_runtime_orbit_score_history

router = APIRouter(prefix="/api/orbit", tags=["orbit"])


async def compute_orbit_score(patient_id: str, user_tier: str = "free") -> dict:
    from graph.orbit_score import OrbitScoreCalculator

    graph_data = await phig_builder.get_full_patient_graph(patient_id)
    nodes = []
    for med in graph_data.get("medications", []):
        nodes.append({"type": "medication", "name": med.get("name"), "confidence": med.get("confidence", 0.7)})
    for cond in graph_data.get("conditions", []):
        nodes.append({
            "type": "condition",
            "name": cond.get("name"),
            "code": cond.get("code") or cond.get("icd10") or cond.get("icd10_code"),
            "icd10": cond.get("code") or cond.get("icd10") or cond.get("icd10_code"),
            "confidence": cond.get("confidence", 0.7),
        })
    for lab in graph_data.get("labs", []):
        nodes.append({"type": "lab_value", "name": lab.get("name"), "value": lab.get("value"), "confidence": 0.9})

    phig = {
        "nodes": nodes,
        "interactions": graph_data.get("interactions", []),
        "care_gaps": graph_data.get("care_gaps", []),
        "reminders": None,
    }

    calc = OrbitScoreCalculator(phig)
    score = calc.compute()
    if user_tier == "free":
        score["breakdown"] = None
        score["premium_required_for_breakdown"] = True
    return score


async def get_score_history(patient_id: str, days: int = 30) -> list:
    history = get_runtime_orbit_score_history(patient_id)
    if history:
        return history
    return get_seed_list_for_patient(patient_id, "orbit_history")


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
    narrative = get_seed_value_for_patient(patient_id, "narrative", "")
    events = get_seed_list_for_patient(patient_id, "narrative_events")
    return {
        "narrative": narrative,
        "events": events,
        "trigger_event": "initial_profile_complete" if narrative else None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


async def build_improvement_plan(patient_id: str, user_tier: str = "free") -> dict:
    score_payload = await compute_orbit_score(patient_id, user_tier)
    current_score = float(score_payload.get("total_score", 0) or 0)
    adherence = get_adherence_snapshot_for_patient(patient_id)

    actions: list[dict] = []

    if adherence.get("adherence_rate", 1.0) < 0.9:
        actions.append({
            "focus": "Medication adherence",
            "action": "Mark reminders on time and avoid missing evening doses for 7 consecutive days.",
            "expected_impact": 8,
            "why": "Adherence consistency directly improves confidence and Orbit score stability.",
        })

    seed_labs = get_seed_list_for_patient(patient_id, "labs")
    seed_gaps = get_seed_list_for_patient(patient_id, "care_gaps")
    seed_interactions = get_seed_list_for_patient(patient_id, "interactions")

    if seed_labs:
        for lab in seed_labs:
            if lab.get("abnormal"):
                if lab.get("name") == "HbA1c":
                    actions.append({
                        "focus": "Glycemic control",
                        "action": "Target fasting glucose under 130 mg/dL and review Metformin timing with your doctor.",
                        "expected_impact": 7,
                        "why": "Lower HbA1c trends significantly improve overall risk-adjusted scoring.",
                    })
                if lab.get("name") == "eGFR":
                    actions.append({
                        "focus": "Renal protection",
                        "action": "Avoid NSAIDs unless prescribed and repeat renal panel in 2-4 weeks.",
                        "expected_impact": 6,
                        "why": "Improving renal risk factors reduces medication interaction penalties.",
                    })

        if any(g.get("status") == "open" for g in seed_gaps):
            actions.append({
                "focus": "Care gap closure",
                "action": "Complete diabetic retinopathy screening during your next appointment.",
                "expected_impact": 5,
                "why": "Closing open care gaps raises preventive-care completeness.",
            })

        if any(ix.get("severity") == "ELEVATED" for ix in seed_interactions):
            actions.append({
                "focus": "Interaction risk",
                "action": "Discuss replacing Ibuprofen with a kidney-safe analgesic option.",
                "expected_impact": 4,
                "why": "Resolving high-risk interactions lowers Orbit interaction penalties.",
            })

    if not actions:
        actions.append({
            "focus": "Maintenance",
            "action": "Continue current medication, monitoring, and appointment cadence.",
            "expected_impact": 3,
            "why": "Consistency protects current score and prevents regressions.",
        })

    actions.sort(key=lambda item: item.get("expected_impact", 0), reverse=True)
    projected = min(100.0, round(current_score + sum(a["expected_impact"] for a in actions[:3]) * 0.4, 1))

    return {
        "current_score": current_score,
        "projected_score_30d": projected,
        "adherence": adherence,
        "actions": actions,
    }


async def schedule_previsit_brief(appointment_id: str, patient_id: str) -> bool:
    return True


class AppointmentCreate(BaseModel):
    doctor_name: str = Field(...)
    appointment_datetime: str = Field(...)
    specialization: Optional[str] = None
    clinic_name: Optional[str] = None


@router.get("/score")
async def get_orbit_score(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)
    result = await compute_orbit_score(patient_id, current_user.get("tier", "free"))
    result["adherence"] = get_adherence_snapshot_for_patient(patient_id)
    return result


@router.get("/score/history")
async def get_orbit_score_history(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)
    history = await get_score_history(patient_id, days=30)
    return history


@router.get("/improvement-plan")
async def get_orbit_improvement_plan(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)
    payload = await build_improvement_plan(patient_id, current_user.get("tier", "free"))
    return await localize_payload_for_patient(payload, patient_id)


@router.post("/appointments")
async def post_appointment(request: Request, body: AppointmentCreate):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)
    await rbac_mod.require_permission(current_user["id"], patient_id, "edit")
    result = await create_appointment(patient_id, body.model_dump())
    appt_entry = {
        "appointment_id": result["appointment_id"],
        "doctor_name": body.doctor_name,
        "specialization": body.specialization or "",
        "appointment_datetime": body.appointment_datetime,
        "clinic_name": body.clinic_name or "",
        "status": "upcoming",
        "brief_scheduled": result["brief_scheduled"],
    }
    if patient_id not in _appointments_store:
        _appointments_store[patient_id] = []
    _appointments_store[patient_id].append(appt_entry)
    return result


_appointments_store: dict[str, list] = {
    patient_id: list(get_seed_list_for_patient(patient_id, "appointments"))
    for patient_id in FAMILY_MEMBER_IDS
}


@router.get("/appointments")
async def list_appointments(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)
    return _appointments_store.get(patient_id, [])


@router.get("/narrative")
async def get_narrative(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)
    result = await get_living_narrative(patient_id)
    return await localize_payload_for_patient(result, patient_id)
