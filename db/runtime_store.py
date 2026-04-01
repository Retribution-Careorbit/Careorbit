from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from db.seed_demo import FAMILY_MEMBER_IDS, get_seed_list_for_patient

_patient_documents: dict[str, list[dict[str, Any]]] = {
    patient_id: deepcopy(get_seed_list_for_patient(patient_id, "documents"))
    for patient_id in FAMILY_MEMBER_IDS
}

_patient_extracted_medications: dict[str, list[dict[str, Any]]] = {}
_pending_document_reviews: dict[str, dict[str, dict[str, Any]]] = {}

_patient_notifications: dict[str, list[dict[str, Any]]] = {
    patient_id: [
        {
            "id": f"notif-boot-{idx + 1:03d}",
            "type": "system",
            "title": "CareOrbit Live Updates Enabled",
            "message": "New uploads and reminder updates will appear here.",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "read": False,
            "path": "/documents",
            "metadata": {},
        }
    ]
    for idx, patient_id in enumerate(FAMILY_MEMBER_IDS)
}

_patient_orbit_score_history: dict[str, list[dict[str, Any]]] = {
    patient_id: deepcopy(get_seed_list_for_patient(patient_id, "orbit_history"))
    for patient_id in FAMILY_MEMBER_IDS
}


def _ensure_patient(patient_id: str) -> None:
    _patient_documents.setdefault(patient_id, [])
    _patient_notifications.setdefault(patient_id, [])
    _patient_extracted_medications.setdefault(patient_id, [])
    _pending_document_reviews.setdefault(patient_id, {})
    _patient_orbit_score_history.setdefault(patient_id, [])


def get_patient_documents(patient_id: str) -> list[dict[str, Any]]:
    _ensure_patient(patient_id)
    return _patient_documents[patient_id]


def add_patient_document(patient_id: str, doc: dict[str, Any]) -> None:
    _ensure_patient(patient_id)
    _patient_documents[patient_id].insert(0, doc)


def update_patient_document(patient_id: str, document_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    _ensure_patient(patient_id)
    for doc in _patient_documents[patient_id]:
        if doc.get("document_id") == document_id:
            doc.update(updates or {})
            return doc
    return None


def get_valid_lab_reports(patient_id: str) -> list[dict[str, Any]]:
    docs = [
        d for d in get_patient_documents(patient_id)
        if d.get("document_type") == "lab_report" and d.get("valid")
    ]
    docs.sort(key=lambda d: d.get("uploaded_at", ""), reverse=True)
    return docs


def get_latest_lab_markers(patient_id: str) -> dict[str, dict[str, Any]]:
    marker_map: dict[str, dict[str, Any]] = {}
    reports = get_valid_lab_reports(patient_id)
    reports.sort(key=lambda d: d.get("uploaded_at", ""))
    for report in reports:
        report_date = (report.get("uploaded_at") or "")[:10]
        for marker in report.get("extracted_markers") or []:
            name = marker.get("name")
            if not name:
                continue
            marker_map[name] = {
                "name": name,
                "value": marker.get("value"),
                "unit": marker.get("unit"),
                "ref_low": marker.get("ref_low"),
                "ref_high": marker.get("ref_high"),
                "date": report_date,
            }
    return marker_map


def add_extracted_medications(patient_id: str, meds: list[dict[str, Any]]) -> None:
    _ensure_patient(patient_id)
    existing = _patient_extracted_medications[patient_id]
    index = {m.get("name", "").lower(): m for m in existing if m.get("name")}
    for med in meds:
        name = (med.get("name") or "").strip()
        if not name:
            continue
        key = name.lower()
        confidence_raw = med.get("confidence")
        try:
            confidence = float(confidence_raw if confidence_raw is not None else 0.72)
        except (TypeError, ValueError):
            confidence = 0.72
        payload = {
            "name": name,
            "dosage": med.get("dosage") or "",
            "frequency": med.get("frequency") or "",
            "confidence": confidence,
            "confidence_label": med.get("confidence_label") or "MODERATE",
            "prescribed_by_doctor": med.get("prescribed_by_doctor") or "Uploaded Document",
            "interactions": [],
        }
        if key in index:
            index[key].update(payload)
        else:
            existing.append(payload)
            index[key] = payload


def get_extracted_medications(patient_id: str) -> list[dict[str, Any]]:
    _ensure_patient(patient_id)
    return _patient_extracted_medications[patient_id]


def save_pending_document_review(patient_id: str, document_id: str, payload: dict[str, Any]) -> None:
    _ensure_patient(patient_id)
    _pending_document_reviews[patient_id][document_id] = payload


def get_pending_document_review(patient_id: str, document_id: str) -> dict[str, Any] | None:
    _ensure_patient(patient_id)
    return _pending_document_reviews[patient_id].get(document_id)


def remove_pending_document_review(patient_id: str, document_id: str) -> dict[str, Any] | None:
    _ensure_patient(patient_id)
    return _pending_document_reviews[patient_id].pop(document_id, None)


def push_notification(patient_id: str, notif_type: str, title: str, message: str, path: str = "/", metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    _ensure_patient(patient_id)
    notif = {
        "id": f"notif-{int(datetime.now(timezone.utc).timestamp() * 1000)}-{len(_patient_notifications[patient_id]) + 1}",
        "type": notif_type,
        "title": title,
        "message": message,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "read": False,
        "path": path,
        "metadata": metadata or {},
    }
    _patient_notifications[patient_id].insert(0, notif)
    return notif


def get_notifications(patient_id: str, unread_only: bool = False) -> list[dict[str, Any]]:
    _ensure_patient(patient_id)
    items = _patient_notifications[patient_id]
    if unread_only:
        return [n for n in items if not n.get("read")]
    return items


def mark_notifications_read(patient_id: str, ids: list[str] | None = None) -> int:
    _ensure_patient(patient_id)
    count = 0
    idset = set(ids or [])
    for notif in _patient_notifications[patient_id]:
        if notif.get("read"):
            continue
        if ids is not None and notif.get("id") not in idset:
            continue
        notif["read"] = True
        count += 1
    return count


def get_orbit_score_history(patient_id: str) -> list[dict[str, Any]]:
    _ensure_patient(patient_id)
    return _patient_orbit_score_history[patient_id]


def get_latest_orbit_score_record(patient_id: str) -> dict[str, Any] | None:
    _ensure_patient(patient_id)
    items = _patient_orbit_score_history[patient_id]
    return items[0] if items else None


def add_orbit_score_record(
    patient_id: str,
    total_score: float,
    delta: float | None,
    breakdown: dict[str, Any] | None = None,
    trigger: str | None = None,
) -> dict[str, Any]:
    _ensure_patient(patient_id)
    record = {
        "total_score": float(total_score),
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "delta": delta,
        "breakdown": deepcopy(breakdown) if isinstance(breakdown, dict) else None,
        "trigger": trigger or "manual",
    }
    _patient_orbit_score_history[patient_id].insert(0, record)
    return record
