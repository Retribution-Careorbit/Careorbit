from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timezone, timedelta
from typing import Optional

import api.middleware.auth as auth_mod
import api.middleware.rbac as rbac_mod
from db.seed_demo import (
    DEMO_USER_ID, RAMESH_ORBIT_HISTORY, RAMESH_NARRATIVE,
    RAMESH_APPOINTMENTS, RAMESH_CARE_GAPS, RAMESH_LABS, RAMESH_INTERACTIONS,
    RAMESH_NARRATIVE_EVENTS,
)
from api.routes.reminders import get_adherence_snapshot_for_patient
from graph.phig_builder import phig_builder

router = APIRouter(prefix="/api/orbit", tags=["orbit"])


async def compute_orbit_score(patient_id: str, user_tier: str = "free") -> dict:
    from graph.orbit_score import OrbitScoreCalculator

    graph_data = await phig_builder.get_full_patient_graph(patient_id)
    nodes = []
    for med in graph_data.get("medications", []):
        nodes.append({"type": "medication", "name": med.get("name"), "confidence": med.get("confidence", 0.7)})
    for cond in graph_data.get("conditions", []):
        nodes.append({"type": "condition", "name": cond.get("name"), "confidence": cond.get("confidence", 0.7)})
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
    score["premium_required_for_breakdown"] = False
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
            "events": RAMESH_NARRATIVE_EVENTS,
            "trigger_event": "initial_profile_complete",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    # END DEMO SEED
    return {
        "narrative": "",
        "events": [],
        "trigger_event": None,
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

    if patient_id == DEMO_USER_ID:
        for lab in RAMESH_LABS:
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

        if any(g.get("status") == "open" for g in RAMESH_CARE_GAPS):
            actions.append({
                "focus": "Care gap closure",
                "action": "Complete diabetic retinopathy screening during your next appointment.",
                "expected_impact": 5,
                "why": "Closing open care gaps raises preventive-care completeness.",
            })

        if any(ix.get("severity") == "ELEVATED" for ix in RAMESH_INTERACTIONS):
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
    return await build_improvement_plan(patient_id, current_user.get("tier", "free"))


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


_appointments_store: dict[str, list] = {DEMO_USER_ID: list(RAMESH_APPOINTMENTS)}


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
    return result
