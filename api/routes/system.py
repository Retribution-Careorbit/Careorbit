from fastapi import APIRouter, Request
from pydantic import BaseModel

import api.middleware.auth as auth_mod
import api.middleware.rbac as rbac_mod
from graph.phig_builder import phig_builder
from api.routes.orbit import _appointments_store
from api.routes.reminders import _reminders_store
from db.runtime_store import get_patient_documents, get_notifications, mark_notifications_read

router = APIRouter(prefix="/api/system", tags=["system"])


class MarkReadRequest(BaseModel):
    ids: list[str] | None = None


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
    items = get_notifications(patient_id, unread_only=unread_only)
    unread = len([n for n in get_notifications(patient_id) if not n.get("read")])
    return {"notifications": items[:20], "unread_count": unread}


@router.post("/notifications/mark-read")
async def mark_read(request: Request, body: MarkReadRequest):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)

    updated = mark_notifications_read(patient_id, ids=body.ids)
    unread = len([n for n in get_notifications(patient_id) if not n.get("read")])
    return {"updated": updated, "unread_count": unread}
