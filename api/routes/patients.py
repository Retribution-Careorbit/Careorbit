from datetime import date
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
from datetime import datetime, timezone

import api.middleware.auth as auth_mod
import api.middleware.rbac as rbac_mod
from api.middleware.localization import localize_payload_for_patient
from db.seed_demo import get_seed_list_for_patient
from db.runtime_store import get_latest_lab_markers
from api.middleware.audit import log_audit
from graph.phig_builder import phig_builder
from utils.profile_validators import (
    validate_date_of_birth, validate_gender, validate_preferred_language,
    validate_medical_literacy_level, validate_blood_type,
    validate_height_cm, validate_weight_kg, derive_age,
)

router = APIRouter(prefix="/api/patients", tags=["patients"])

_emergency_pass_store: dict[str, dict] = {}


def _classify_threshold(value: float, ref_low: Optional[float], ref_high: Optional[float]) -> tuple[bool, float]:
    if ref_high is not None and value > ref_high:
        delta = value - ref_high
        ratio = delta / ref_high if ref_high else delta
        return True, max(ratio, 0.0)
    if ref_low is not None and value < ref_low:
        delta = ref_low - value
        ratio = delta / ref_low if ref_low else delta
        return True, max(ratio, 0.0)
    return False, 0.0


def _derive_trend_direction(points: list[dict]) -> str:
    if len(points) < 2:
        return "stable"
    first = float(points[0].get("value", 0))
    last = float(points[-1].get("value", 0))
    if last > first:
        return "up"
    if last < first:
        return "down"
    return "stable"


def _threshold_label(ref_low: Optional[float], ref_high: Optional[float]) -> str:
    if ref_low is not None and ref_high is not None:
        return f"{ref_low}-{ref_high}"
    if ref_high is not None:
        return f"<= {ref_high}"
    if ref_low is not None:
        return f">= {ref_low}"
    return "n/a"


def _severity_from_ratio(ratio: float) -> str:
    if ratio >= 0.25:
        return "critical"
    if ratio >= 0.12:
        return "warning"
    return "monitor"


def _insight_sentence(marker_name: str, latest: float, threshold: str, direction: str) -> str:
    direction_text = {
        "up": "trend is rising",
        "down": "trend is declining",
        "stable": "trend is stable",
    }.get(direction, "trend is stable")
    return f"{marker_name} is at {latest} ({threshold}); current {direction_text} and needs physician review."


def _latest_extracted_markers(patient_id: str) -> dict[str, dict]:
    return get_latest_lab_markers(patient_id)


class ProfileUpdateRequest(BaseModel):
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    preferred_language: Optional[str] = None
    medical_literacy_level: Optional[str] = None
    blood_type: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None


MANDATORY_ONBOARDING_FIELDS = ["date_of_birth", "gender", "preferred_language", "medical_literacy_level"]


def _get_users_store():
    from api.routes.auth import _users_store
    return _users_store


def _check_onboarding_complete(user_data: dict) -> bool:
    for field in MANDATORY_ONBOARDING_FIELDS:
        if not user_data.get(field):
            return False
    return True


def _build_profile_response(user_data: dict) -> dict:
    dob_str = user_data.get("date_of_birth")
    age = None
    if dob_str:
        try:
            if isinstance(dob_str, str):
                from datetime import datetime
                dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
            else:
                dob = dob_str
            age = derive_age(dob)
        except (ValueError, TypeError):
            pass

    return {
        "profile": {
            "date_of_birth": user_data.get("date_of_birth"),
            "age": age,
            "gender": user_data.get("gender"),
            "preferred_language": user_data.get("preferred_language", "en"),
            "medical_literacy_level": user_data.get("medical_literacy_level"),
            "blood_type": user_data.get("blood_type"),
            "height_cm": user_data.get("height_cm"),
            "weight_kg": user_data.get("weight_kg"),
            "city": user_data.get("city"),
            "state": user_data.get("state"),
            "country": user_data.get("country"),
        },
        "onboarding_complete": _check_onboarding_complete(user_data),
    }


def _pick_dispatch_number(contacts: list[dict]) -> str:
    for c in contacts:
        relation = (c.get("relation") or "").lower()
        if "emergency" in relation:
            return c.get("phone", "112")
    return "112"


@router.get("/profile")
async def get_profile(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)

    users_store = _get_users_store()
    user_data = users_store.get(patient_id, {})
    return _build_profile_response(user_data)


@router.put("/profile")
async def update_profile(body: ProfileUpdateRequest, request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)

    users_store = _get_users_store()
    user_data = users_store.get(patient_id)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    fields_updated = []

    if body.date_of_birth is not None:
        try:
            validated_dob = validate_date_of_birth(body.date_of_birth)
            user_data["date_of_birth"] = body.date_of_birth
            fields_updated.append("date_of_birth")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    if body.gender is not None:
        try:
            user_data["gender"] = validate_gender(body.gender)
            fields_updated.append("gender")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    if body.preferred_language is not None:
        try:
            user_data["preferred_language"] = validate_preferred_language(body.preferred_language)
            fields_updated.append("preferred_language")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    if body.medical_literacy_level is not None:
        try:
            user_data["medical_literacy_level"] = validate_medical_literacy_level(body.medical_literacy_level)
            fields_updated.append("medical_literacy_level")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    if body.blood_type is not None:
        try:
            user_data["blood_type"] = validate_blood_type(body.blood_type)
            fields_updated.append("blood_type")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    if body.height_cm is not None:
        try:
            user_data["height_cm"] = validate_height_cm(body.height_cm)
            fields_updated.append("height_cm")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    if body.weight_kg is not None:
        try:
            user_data["weight_kg"] = validate_weight_kg(body.weight_kg)
            fields_updated.append("weight_kg")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    if body.city is not None:
        user_data["city"] = body.city.strip()
        fields_updated.append("city")

    if body.state is not None:
        user_data["state"] = body.state.strip()
        fields_updated.append("state")

    if body.country is not None:
        user_data["country"] = body.country.strip().upper()[:3]
        fields_updated.append("country")

    was_complete = user_data.get("onboarding_completed_at") is not None
    is_now_complete = _check_onboarding_complete(user_data)

    if is_now_complete and not was_complete:
        from datetime import datetime, timezone
        user_data["onboarding_completed_at"] = datetime.now(timezone.utc).isoformat()

    await log_audit(current_user["id"], patient_id, "PROFILE_UPDATE", request, {
        "fields_updated": fields_updated,
        "onboarding_triggered": is_now_complete and not was_complete,
    })

    return _build_profile_response(user_data)


@router.get("/overview")
async def get_overview(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)
    graph = await phig_builder.get_full_patient_graph(patient_id)
    return await localize_payload_for_patient(graph, patient_id)


@router.get("/medications")
async def get_medications(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)
    meds = await phig_builder.get_medication_subgraph(patient_id)
    return await localize_payload_for_patient(meds, patient_id)


@router.get("/vitals")
async def get_vitals(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)
    return await localize_payload_for_patient({"vitals": get_seed_list_for_patient(patient_id, "vitals")}, patient_id)


@router.get("/lab-insights")
async def get_lab_insights(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)

    lab_history = get_seed_list_for_patient(patient_id, "lab_history")
    if not lab_history:
        return {"areas": []}

    extracted_map = _latest_extracted_markers(patient_id)
    areas = []
    for entry in lab_history:
        points = entry.get("points", [])
        if not points:
            continue
        marker_name = entry.get("marker_name")
        extracted = extracted_map.get(marker_name)
        latest = float(points[-1].get("value", 0))
        ref_low = entry.get("ref_low")
        ref_high = entry.get("ref_high")

        if extracted and extracted.get("value") is not None:
            latest = float(extracted.get("value", latest))
            ref_low = extracted.get("ref_low") if extracted.get("ref_low") is not None else ref_low
            ref_high = extracted.get("ref_high") if extracted.get("ref_high") is not None else ref_high
            extracted_date = extracted.get("date")
            if extracted_date and all(p.get("date") != extracted_date for p in points):
                points = [*points, {"date": extracted_date, "value": latest}]

        breached, ratio = _classify_threshold(latest, ref_low, ref_high)
        if not breached:
            continue

        trend = _derive_trend_direction(points)
        threshold = _threshold_label(ref_low, ref_high)
        areas.append(
            {
                "area_key": entry.get("area_key"),
                "area_label": entry.get("area_label"),
                "marker_name": marker_name,
                "latest_value": latest,
                "unit": extracted.get("unit") if extracted and extracted.get("unit") else entry.get("unit"),
                "threshold": threshold,
                "severity": _severity_from_ratio(ratio),
                "trend_direction": trend,
                "insight": _insight_sentence(marker_name or "Marker", latest, threshold, trend),
                "points": points,
                "severity_score": ratio,
            }
        )

    areas.sort(key=lambda item: item.get("severity_score", 0), reverse=True)
    for area in areas:
        area.pop("severity_score", None)

    return await localize_payload_for_patient({"areas": areas}, patient_id)


@router.get("/emergency-contacts")
async def get_emergency_contacts(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)
    return await localize_payload_for_patient({"contacts": get_seed_list_for_patient(patient_id, "emergency_contacts")}, patient_id)


@router.get("/emergency-pass")
async def generate_emergency_pass(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)

    users_store = _get_users_store()
    user_data = users_store.get(patient_id, {})

    contacts = get_seed_list_for_patient(patient_id, "emergency_contacts")
    meds = get_seed_list_for_patient(patient_id, "medications")
    dispatch_number = _pick_dispatch_number(contacts)

    token = uuid4().hex
    payload = {
        "token": token,
        "patient_id": patient_id,
        "patient_name": user_data.get("name") or current_user.get("name") or "Patient",
        "age": user_data.get("age"),
        "gender": user_data.get("gender"),
        "blood_type": user_data.get("blood_type"),
        "city": user_data.get("city"),
        "dispatch_phone": dispatch_number,
        "emergency_contacts": contacts,
        "medications": [
            {
                "name": m.get("name"),
                "dosage": m.get("dosage"),
                "frequency": m.get("frequency"),
            }
            for m in meds[:6]
        ],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _emergency_pass_store[token] = payload

    payload = {
        "dispatch_phone": dispatch_number,
        "token": token,
        "qr_path": f"/api/patients/emergency-pass/{token}",
        "read_only_note": "Emergency view is read-only and intended for first responders.",
        "card": payload,
    }
    return await localize_payload_for_patient(payload, patient_id)


@router.get("/emergency-pass/{token}")
async def get_emergency_pass(token: str):
    payload = _emergency_pass_store.get(token)
    if not payload:
        raise HTTPException(status_code=404, detail="Emergency pass not found")
    response_payload = {
        "read_only": True,
        "patient_name": payload.get("patient_name"),
        "age": payload.get("age"),
        "gender": payload.get("gender"),
        "blood_type": payload.get("blood_type"),
        "city": payload.get("city"),
        "dispatch_phone": payload.get("dispatch_phone"),
        "emergency_contacts": payload.get("emergency_contacts", []),
        "medications": payload.get("medications", []),
        "issued_at": payload.get("created_at"),
    }
    return await localize_payload_for_patient(response_payload, payload.get("patient_id"))
