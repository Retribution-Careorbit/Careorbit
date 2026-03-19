from datetime import date
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
from datetime import datetime, timezone

import api.middleware.auth as auth_mod
import api.middleware.rbac as rbac_mod
from db.seed_demo import DEMO_USER_ID, RAMESH_VITALS, RAMESH_EMERGENCY_CONTACTS
from db.seed_demo import RAMESH_MEDICATIONS
from db.seed_demo import RAMESH_LAB_HISTORY
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
    return graph


@router.get("/medications")
async def get_medications(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)
    meds = await phig_builder.get_medication_subgraph(patient_id)
    return meds


@router.get("/vitals")
async def get_vitals(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)
    if patient_id == DEMO_USER_ID:
        return {"vitals": RAMESH_VITALS}
    return {"vitals": []}


@router.get("/lab-insights")
async def get_lab_insights(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)

    extracted_map = _latest_extracted_markers(patient_id)

    if patient_id != DEMO_USER_ID:
        areas = []
        for marker_name, extracted in extracted_map.items():
            areas.append(
                {
                    "area_key": marker_name.lower().replace(" ", "_"),
                    "area_label": marker_name,
                    "marker_name": marker_name,
                    "latest_value": extracted.get("value"),
                    "unit": extracted.get("unit"),
                    "threshold": _threshold_label(extracted.get("ref_low"), extracted.get("ref_high")),
                    "severity": "monitor",
                    "trend_direction": "stable",
                    "insight": f"{marker_name} extracted from uploaded document.",
                    "points": [{"date": extracted.get("date"), "value": extracted.get("value")}],
                }
            )
        return {"areas": areas}

    areas = []
    for entry in RAMESH_LAB_HISTORY:
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

    return {"areas": areas}


@router.get("/emergency-contacts")
async def get_emergency_contacts(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)
    if patient_id == DEMO_USER_ID:
        return {"contacts": RAMESH_EMERGENCY_CONTACTS}
    return {"contacts": []}


@router.get("/emergency-pass")
async def generate_emergency_pass(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)

    users_store = _get_users_store()
    user_data = users_store.get(patient_id, {})

    contacts = RAMESH_EMERGENCY_CONTACTS if patient_id == DEMO_USER_ID else []
    meds = RAMESH_MEDICATIONS if patient_id == DEMO_USER_ID else []
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

    return {
        "dispatch_phone": dispatch_number,
        "token": token,
        "qr_path": f"/api/patients/emergency-pass/{token}",
        "read_only_note": "Emergency view is read-only and intended for first responders.",
        "card": payload,
    }


@router.get("/emergency-pass/{token}")
async def get_emergency_pass(token: str):
    payload = _emergency_pass_store.get(token)
    if not payload:
        raise HTTPException(status_code=404, detail="Emergency pass not found")
    return {
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
