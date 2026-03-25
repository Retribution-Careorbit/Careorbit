from fastapi import APIRouter, Request
from pydantic import BaseModel
import logging
import os

import api.middleware.auth as auth_mod
import api.middleware.rbac as rbac_mod
from graph.phig_builder import phig_builder
from api.routes.orbit import _appointments_store
from api.routes.reminders import _reminders_store
from db.runtime_store import get_patient_documents, get_notifications, mark_notifications_read
from config import get_settings

router = APIRouter(prefix="/api/system", tags=["system"])
logger = logging.getLogger("careorbit.routes.system")


class MarkReadRequest(BaseModel):
    ids: list[str] | None = None


@router.get("/architecture/compliance")
async def architecture_compliance(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)

    settings = get_settings()

    environment = (settings.ENVIRONMENT or "development").strip().lower()
    # In production we enforce fully managed Azure services; in local/dev we allow controlled backup mode.
    strict_managed_mode = environment in {"production", "prod"}

    services = [
        {
            "name": "Azure Blob Storage",
            "configured": bool(settings.AZURE_BLOB_CONNECTION_STRING),
            "required": True,
            "backup_available": True,
            "backup_label": "Local runtime document flow",
        },
        {
            "name": "Azure Document Intelligence",
            "configured": bool(settings.AZURE_DI_ENDPOINT and settings.AZURE_DI_KEY),
            "required": True,
            "backup_available": True,
            "backup_label": "Filename/type heuristics + manual review",
        },
        {
            "name": "Azure Language NER (Healthcare)",
            "configured": bool(settings.AZURE_LANGUAGE_ENDPOINT and settings.AZURE_LANGUAGE_KEY),
            "required": True,
            "backup_available": True,
            "backup_label": "Regex/entity-lite extraction",
        },
        {
            "name": "Azure OpenAI GPT-4o",
            "configured": bool(settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_KEY),
            "required": True,
            "backup_available": True,
            "backup_label": "PHIG-grounded local logic",
        },
        {
            "name": "Azure AI Search (RAG)",
            "configured": bool(settings.AZURE_SEARCH_ENDPOINT and settings.AZURE_SEARCH_KEY),
            "required": True,
            "backup_available": True,
            "backup_label": "Local PHIG graph traversal",
        },
        {
            "name": "Azure AI Translator",
            "configured": bool(settings.AZURE_TRANSLATOR_ENDPOINT and settings.AZURE_TRANSLATOR_KEY),
            "required": True,
            "backup_available": True,
            "backup_label": "English-only local response mode",
        },
        {
            "name": "Azure Key Vault",
            "configured": bool(os.environ.get("AZURE_KEYVAULT_URI")),
            "required": False,
            "backup_available": True,
            "backup_label": "Environment variables",
        },
        {
            "name": "Azure Communication Services",
            "configured": bool(settings.AZURE_COMM_CONNECTION_STRING),
            "required": False,
            "backup_available": True,
            "backup_label": "In-app notifications only",
        },
        {
            "name": "Azure PostgreSQL Flexible Server",
            "configured": "postgres" in (settings.DATABASE_URL or "").lower(),
            "required": True,
            "backup_available": True,
            "backup_label": "SQLite local persistence",
        },
    ]

    service_warnings: list[str] = []
    service_gaps: list[str] = []
    for svc in services:
        configured = bool(svc.get("configured"))
        required = bool(svc.get("required"))
        backup_available = bool(svc.get("backup_available"))
        in_degraded_mode = (not configured) and (not strict_managed_mode) and backup_available

        svc["degraded_mode"] = in_degraded_mode
        svc["status"] = "configured" if configured else ("degraded_backup" if in_degraded_mode else "missing")

        if required and not configured:
            if in_degraded_mode:
                service_warnings.append(
                    f"{svc['name']}: degraded_mode=true using backup ({svc.get('backup_label', 'local fallback')})."
                )
            else:
                service_gaps.append(svc["name"])

    has_blob = bool(settings.AZURE_BLOB_CONNECTION_STRING)
    has_di = bool(settings.AZURE_DI_ENDPOINT and settings.AZURE_DI_KEY)
    has_language = bool(settings.AZURE_LANGUAGE_ENDPOINT and settings.AZURE_LANGUAGE_KEY)
    has_openai = bool(settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_KEY)
    has_search = bool(settings.AZURE_SEARCH_ENDPOINT and settings.AZURE_SEARCH_KEY)
    has_translator = bool(settings.AZURE_TRANSLATOR_ENDPOINT and settings.AZURE_TRANSLATOR_KEY)

    def _step_state(implemented: bool, degraded_msg: str, gap_msg: str):
        if implemented:
            return True, False, None
        if strict_managed_mode:
            return False, False, gap_msg
        return True, True, degraded_msg

    s1_ok, s1_degraded, s1_note = _step_state(
        has_blob,
        "Blob upload running in local backup mode.",
        "Azure Blob connection string is not configured.",
    )
    s2_ok, s2_degraded, s2_note = _step_state(
        has_di,
        "OCR running in fallback/manual review mode.",
        "Azure Document Intelligence credentials are not configured.",
    )
    s3_ok, s3_degraded, s3_note = _step_state(
        has_language,
        "Clinical entity coding running in fallback mode.",
        "Azure Language credentials are not configured.",
    )
    s4_ok, s4_degraded, s4_note = _step_state(
        has_openai,
        "Structured extraction running in PHIG-grounded local mode.",
        "Azure OpenAI credentials are not configured.",
    )
    s6_ok, s6_degraded, s6_note = _step_state(
        has_search,
        "RAG check running via local PHIG traversal fallback.",
        "Azure AI Search credentials are not configured.",
    )
    s8_ok, s8_degraded, s8_note = _step_state(
        has_openai and has_translator,
        "Orchestration/translation running in degraded (local-language) mode.",
        "Azure OpenAI and Translator must both be configured.",
    )

    steps = [
        {"step": 1, "name": "Upload to Blob", "implemented": s1_ok, "degraded_mode": s1_degraded, "gap": None if s1_ok else s1_note},
        {"step": 2, "name": "Doc Intelligence OCR", "implemented": s2_ok, "degraded_mode": s2_degraded, "gap": None if s2_ok else s2_note},
        {"step": 3, "name": "Language NER coding", "implemented": s3_ok, "degraded_mode": s3_degraded, "gap": None if s3_ok else s3_note},
        {"step": 4, "name": "GPT extraction", "implemented": s4_ok, "degraded_mode": s4_degraded, "gap": None if s4_ok else s4_note},
        {"step": 5, "name": "Write to PHIG after confirmation", "implemented": True, "degraded_mode": False},
        {"step": 6, "name": "RAG check via AI Search", "implemented": s6_ok, "degraded_mode": s6_degraded, "gap": None if s6_ok else s6_note},
        {"step": 7, "name": "Parallel agent traversal", "implemented": True, "degraded_mode": False},
        {"step": 8, "name": "GPT orchestration + translation", "implemented": s8_ok, "degraded_mode": s8_degraded, "gap": None if s8_ok else s8_note},
        {"step": 9, "name": "Fanout to 6 features/tabs", "implemented": True, "degraded_mode": False},
    ]

    step_warnings = [
        f"Step {s['step']}: {s.get('gap') or 'Running in degraded backup mode.'}"
        for s in steps
        if s.get("degraded_mode")
    ]
    step_gaps = [f"Step {s['step']}: {s.get('gap') or 'Not fully implemented'}" for s in steps if not s["implemented"]]

    return {
        "services": services,
        "steps": steps,
        "strict_managed_mode": strict_managed_mode,
        "degraded_mode": len(service_warnings) > 0 or len(step_warnings) > 0,
        "architecture_followed": len(service_gaps) == 0 and len(step_gaps) == 0,
        "warnings": service_warnings + step_warnings,
        "gaps": service_gaps + step_gaps,
    }


@router.get("/search")
async def global_search(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)

    query = (request.query_params.get("q") or "").strip().lower()
    if len(query) < 2:
        return {"query": query, "results": []}

    results: list[dict] = []

    graph = await phig_builder.get_full_patient_graph(patient_id)
    for med in graph.get("medications", []):
        name = str(med.get("name") or "")
        if query in name.lower():
            results.append({
                "id": f"med-{name.lower().replace(' ', '-')}",
                "type": "medication",
                "title": name,
                "subtitle": f"{med.get('dosage', '')} {med.get('frequency', '')}".strip(),
                "path": "/medications",
            })

    for lab in graph.get("labs", []):
        name = str(lab.get("name") or "")
        if query in name.lower():
            results.append({
                "id": f"lab-{name.lower().replace(' ', '-')}",
                "type": "lab",
                "title": name,
                "subtitle": f"{lab.get('value')} {lab.get('unit', '')}".strip(),
                "path": "/health-insights",
            })

    for doc in get_patient_documents(patient_id):
        name = str(doc.get("file_name") or "")
        if query in name.lower() or query in str(doc.get("summary") or "").lower():
            results.append({
                "id": doc.get("document_id"),
                "type": "document",
                "title": name,
                "subtitle": doc.get("summary") or "Uploaded document",
                "path": "/documents",
            })

    for appt in _appointments_store.get(patient_id, []):
        doctor = str(appt.get("doctor_name") or "")
        if query in doctor.lower() or query in str(appt.get("specialization") or "").lower():
            results.append({
                "id": appt.get("appointment_id"),
                "type": "appointment",
                "title": doctor,
                "subtitle": appt.get("appointment_datetime") or "Appointment",
                "path": "/appointments",
            })

    for reminder in _reminders_store.values():
        if reminder.get("user_id") != patient_id:
            continue
        med_node = str(reminder.get("medication_node_id") or "")
        if query in med_node.lower():
            results.append({
                "id": reminder.get("reminder_id"),
                "type": "reminder",
                "title": med_node,
                "subtitle": f"Due at {reminder.get('reminder_time')}",
                "path": "/reminders",
            })

    return {"query": query, "results": results[:12]}


@router.get("/notifications")
async def list_notifications(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)

    unread_only = (request.query_params.get("unread_only") or "false").lower() == "true"
    try:
        items = get_notifications(patient_id, unread_only=unread_only)
        unread = len([n for n in get_notifications(patient_id) if not n.get("read")])
        return {"notifications": (items or [])[:20], "unread_count": unread}
    except Exception:
        logger.exception("Failed to fetch notifications patient_id=%s", patient_id)
        return {"notifications": [], "unread_count": 0}


@router.post("/notifications/mark-read")
async def mark_read(request: Request, body: MarkReadRequest):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)

    try:
        updated = mark_notifications_read(patient_id, ids=body.ids)
        unread = len([n for n in get_notifications(patient_id) if not n.get("read")])
        return {"updated": updated, "unread_count": unread}
    except Exception:
        logger.exception("Failed to mark notifications read patient_id=%s", patient_id)
        return {"updated": 0, "unread_count": 0}
