from fastapi import APIRouter, Request
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
import io
from datetime import datetime

import api.middleware.auth as auth_mod
from api.middleware.rbac import verify_patient_access
from graph.phig_builder import phig_builder
from utils.pdf_generator import generate_health_summary_pdf, generate_previsit_doctor_brief_pdf
from services.azure_blob import AzureBlobService
from api.routes.orbit import _appointments_store
from db.seed_demo import (
    get_seed_list_for_patient,
    get_seed_value_for_patient,
)

blob_service = AzureBlobService()

router = APIRouter(prefix="/api/summary", tags=["summary"])


def _build_previsit_brief_payload(appointment: dict, patient_id: str) -> dict:
    profile = get_seed_value_for_patient(patient_id, "profile", {})
    seed_labs = get_seed_list_for_patient(patient_id, "labs")
    seed_meds = get_seed_list_for_patient(patient_id, "medications")
    seed_interactions = get_seed_list_for_patient(patient_id, "interactions")
    seed_gaps = get_seed_list_for_patient(patient_id, "care_gaps")
    abnormalities = [lab for lab in seed_labs if lab.get("abnormal")]

    priorities = []
    if any(lab.get("name") == "HbA1c" for lab in abnormalities):
        priorities.append("Review glycemic control trend and adherence barriers.")
    if any(lab.get("name") in {"eGFR", "Creatinine"} for lab in abnormalities):
        priorities.append("Evaluate kidney safety and avoid nephrotoxic medication exposure.")
    if any(lab.get("name") == "TSH" for lab in abnormalities):
        priorities.append("Assess thyroid dysfunction impact on fatigue/metabolic status.")
    if any(lab.get("name") == "ALT" for lab in abnormalities):
        priorities.append("Review hepatic enzyme elevation and statin safety considerations.")
    if not priorities:
        priorities.append("Continue routine chronic disease follow-up and medication review.")

    return {
        "patient": {
            "id": patient_id,
            "name": profile.get("name") or patient_id,
            "age": profile.get("age"),
            "gender": profile.get("gender"),
            "city": profile.get("city"),
        },
        "appointment": {
            "doctor_name": appointment.get("doctor_name", "Unknown"),
            "specialization": appointment.get("specialization", "General"),
            "appointment_datetime": appointment.get("appointment_datetime", ""),
            "clinic_name": appointment.get("clinic_name", ""),
            "generated_at": f"{datetime.utcnow().isoformat()}Z",
        },
        "medications": seed_meds,
        "labs": seed_labs,
        "interaction_risks": seed_interactions,
        "care_gaps": seed_gaps,
        "clinical_priorities": priorities,
    }


@router.get("/generate")
async def generate_summary(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])

    await verify_patient_access(current_user["id"], patient_id)

    graph_data = await phig_builder.get_full_patient_graph(patient_id)

    total_nodes = 0
    if graph_data and "summary" in graph_data:
        total_nodes = graph_data["summary"].get("total_nodes", 0)

    if total_nodes == 0:
        return {"error": "No health data available to generate summary"}

    pdf_bytes = generate_health_summary_pdf(graph_data)

    try:
        await blob_service.upload_health_summary_pdf(pdf_bytes, f"CareOrbit_Summary_{patient_id}.pdf")
    except (NotImplementedError, Exception):
        pass

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="CareOrbit_Summary_{patient_id}.pdf"'
        }
    )


@router.get("/previsit-brief/{appointment_id}")
async def generate_previsit_brief(appointment_id: str, request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await verify_patient_access(current_user["id"], patient_id)

    appointments = _appointments_store.get(patient_id, [])
    appointment = next((a for a in appointments if a.get("appointment_id") == appointment_id), None)

    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")

    brief_payload = _build_previsit_brief_payload(appointment, patient_id)
    pdf_bytes = generate_previsit_doctor_brief_pdf(brief_payload)
    filename = f"CareOrbit_PreVisit_{appointment_id}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
