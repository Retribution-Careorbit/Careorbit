from uuid import uuid4
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone

import api.middleware.auth as auth_mod
import api.middleware.rbac as rbac_mod
from db.session import async_session
from db.seed_demo import DEMO_USER_ID, RAMESH_REMINDERS, RAMESH_REMINDER_EVENTS
from db.runtime_store import push_notification

router = APIRouter(prefix="/api/reminders", tags=["reminders"])

_reminders_store = {}

_known_medication_nodes = {
    "metformin-node-id", "amlodipine-node-id", "aspirin-node-id",
    "atorvastatin-node-id", "glycomet-node-id", "strip-node-id",
}

_reminder_events_store: dict[str, list[dict]] = {}

for _seed in RAMESH_REMINDERS:
    _reminders_store[_seed["reminder_id"]] = dict(_seed)
_reminder_events_store[DEMO_USER_ID] = list(RAMESH_REMINDER_EVENTS)


class CreateReminderRequest(BaseModel):
    medication_node_id: str
    reminder_time: str
    days_of_week: Optional[List[int]] = None


class ReminderStatusRequest(BaseModel):
    status: str
    reason: Optional[str] = None
    occurred_at: Optional[str] = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_hhmm(time_value: str) -> tuple[int, int]:
    try:
        hh, mm = time_value.split(":")
        return int(hh), int(mm)
    except (TypeError, ValueError, AttributeError):
        return 8, 0


def _is_due_today(reminder: dict, now: datetime) -> bool:
    days = reminder.get("days_of_week") or [1, 2, 3, 4, 5, 6, 7]
    if now.isoweekday() not in days:
        return False
    hh, mm = _parse_hhmm(reminder.get("reminder_time", "08:00"))
    return (now.hour, now.minute) >= (hh, mm)


def _latest_event_for_reminder(user_id: str, reminder_id: str) -> Optional[dict]:
    events = [
        ev for ev in _reminder_events_store.get(user_id, [])
        if ev.get("reminder_id") == reminder_id
    ]
    if not events:
        return None
    events.sort(key=lambda x: x.get("occurred_at", ""), reverse=True)
    return events[0]


def _has_event_for_date(user_id: str, reminder_id: str, day_iso: str) -> bool:
    for ev in _reminder_events_store.get(user_id, []):
        if ev.get("reminder_id") != reminder_id:
            continue
        occurred = str(ev.get("occurred_at") or "")
        if occurred.startswith(day_iso):
            return True
    return False


def _auto_mark_overdue_missed(user_id: str, now: datetime) -> int:
    auto_marked = 0
    day_iso = now.date().isoformat()
    for reminder in _reminders_store.values():
        if reminder.get("user_id") != user_id or not reminder.get("active", True):
            continue
        if now.isoweekday() not in (reminder.get("days_of_week") or [1, 2, 3, 4, 5, 6, 7]):
            continue
        if _has_event_for_date(user_id, reminder["reminder_id"], day_iso):
            continue

        hh, mm = _parse_hhmm(reminder.get("reminder_time", "08:00"))
        overdue_cutoff = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if now <= overdue_cutoff:
            continue

        event = {
            "event_id": str(uuid4()),
            "reminder_id": reminder["reminder_id"],
            "status": "missed",
            "reason": "Auto-marked missed: due time passed without confirmation.",
            "occurred_at": now.isoformat(),
        }
        _reminder_events_store.setdefault(user_id, []).append(event)
        reminder["adherence_streak"] = 0
        reminder["total_missed"] = int(reminder.get("total_missed", 0)) + 1
        reminder["last_status"] = "missed"
        reminder["last_reason"] = event["reason"]
        auto_marked += 1

    if auto_marked:
        push_notification(
            user_id,
            "reminder",
            "Reminder status updated",
            f"{auto_marked} dose(s) auto-marked as missed after due time elapsed.",
            path="/reminders",
            metadata={"auto_marked": auto_marked},
        )
    return auto_marked


def _compute_adherence(user_id: str) -> dict:
    reminders = [
        r for r in _reminders_store.values()
        if r.get("user_id") == user_id and r.get("active", True)
    ]
    total_taken = sum(int(r.get("total_taken", 0)) for r in reminders)
    total_missed = sum(int(r.get("total_missed", 0)) for r in reminders)
    denominator = total_taken + total_missed
    rate = round((total_taken / denominator) if denominator else 0.0, 3)
    streak = max([int(r.get("adherence_streak", 0)) for r in reminders], default=0)
    latest_reasons = [
        r.get("last_reason") for r in reminders
        if r.get("last_reason")
    ]
    return {
        "adherence_rate": rate,
        "streak_days": streak,
        "total_taken": total_taken,
        "total_missed": total_missed,
        "latest_missed_reason": latest_reasons[0] if latest_reasons else None,
    }


def get_adherence_snapshot_for_patient(patient_id: str) -> dict:
    return _compute_adherence(patient_id)


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


def _default_times_for_frequency(frequency: str | None) -> list[str]:
    text = (frequency or "").strip().lower()
    if not text:
        return ["08:00"]
    if any(token in text for token in ["tid", "thrice", "3", "three"]):
        return ["08:00", "14:00", "20:00"]
    if any(token in text for token in ["bid", "twice", "2", "two", "morning and evening"]):
        return ["08:00", "20:00"]
    return ["08:00"]


def upsert_document_reminders(patient_id: str, document_id: str, medications: list[dict]) -> int:
    created = 0

    for med in medications or []:
        med_name = str(med.get("name") or "").strip()
        if not med_name:
            continue
        node_id = str(med.get("phig_node_id") or med.get("node_id") or f"node-med-{med_name.lower().replace(' ', '-')}")
        times = _default_times_for_frequency(str(med.get("frequency") or ""))

        for reminder_time in times:
            source_marker = f"doc-reminder:{document_id}:{med_name.lower()}:{reminder_time}"
            existing = next(
                (
                    r for r in _reminders_store.values()
                    if r.get("user_id") == patient_id and (r.get("source_marker") or "") == source_marker
                ),
                None,
            )

            payload = {
                "user_id": patient_id,
                "medication_node_id": node_id,
                "medication_name": med_name,
                "reminder_time": reminder_time,
                "days_of_week": [1, 2, 3, 4, 5, 6, 7],
                "active": True,
                "source_marker": source_marker,
                "source_document_id": document_id,
            }

            if existing:
                existing.update(payload)
                continue

            reminder_id = str(uuid4())
            _reminders_store[reminder_id] = {
                "reminder_id": reminder_id,
                "adherence_streak": 0,
                "total_taken": 0,
                "total_missed": 0,
                "last_status": None,
                "last_reason": None,
                **payload,
            }
            created += 1

    return created


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

    try:
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
    except Exception:
        await session.rollback()

    _reminders_store[reminder_id] = {
        "reminder_id": reminder_id,
        "user_id": current_user["id"],
        "medication_node_id": body.medication_node_id,
        "reminder_time": body.reminder_time,
        "days_of_week": days,
        "active": True,
        "adherence_streak": 0,
        "total_taken": 0,
        "total_missed": 0,
        "last_status": None,
        "last_reason": None,
    }

    return {
        "reminder_id": reminder_id,
        "status": "created",
    }


@router.get("/list")
async def list_reminders(request: Request):
    current_user = await auth_mod.get_current_user(request)

    user_reminders: list[dict] = [
        r for r in _reminders_store.values()
        if r["user_id"] == current_user["id"] and r.get("active", True)
    ]

    for reminder in user_reminders:
        latest_event = _latest_event_for_reminder(current_user["id"], reminder["reminder_id"])
        reminder["latest_event"] = latest_event

    return user_reminders


@router.get("/due")
async def list_due_reminders(request: Request):
    current_user = await auth_mod.get_current_user(request)
    now = _utc_now()
    _auto_mark_overdue_missed(current_user["id"], now)

    due = []
    for reminder in _reminders_store.values():
        if reminder.get("user_id") != current_user["id"] or not reminder.get("active", True):
            continue
        if not _is_due_today(reminder, now):
            continue

        latest_event = _latest_event_for_reminder(current_user["id"], reminder["reminder_id"])
        due.append({
            "reminder_id": reminder["reminder_id"],
            "medication_node_id": reminder["medication_node_id"],
            "reminder_time": reminder["reminder_time"],
            "status": latest_event.get("status") if latest_event else "pending",
            "reason": latest_event.get("reason") if latest_event else None,
            "latest_event_at": latest_event.get("occurred_at") if latest_event else None,
        })

    return {
        "as_of": now.isoformat(),
        "due": due,
    }


@router.post("/{reminder_id}/mark")
async def mark_reminder_status(reminder_id: str, body: ReminderStatusRequest, request: Request):
    current_user = await auth_mod.get_current_user(request)

    reminder = _reminders_store.get(reminder_id)
    if not reminder or reminder["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Reminder not found")

    status = (body.status or "").strip().lower()
    if status not in ("taken", "missed"):
        raise HTTPException(status_code=400, detail="status must be either 'taken' or 'missed'")
    if status == "missed" and not (body.reason or "").strip():
        raise HTTPException(status_code=400, detail="Missed reason is required")

    occurred_at = body.occurred_at or _utc_now().isoformat()
    event = {
        "event_id": str(uuid4()),
        "reminder_id": reminder_id,
        "status": status,
        "reason": body.reason,
        "occurred_at": occurred_at,
    }
    _reminder_events_store.setdefault(current_user["id"], []).append(event)

    if status == "taken":
        reminder["adherence_streak"] = int(reminder.get("adherence_streak", 0)) + 1
        reminder["total_taken"] = int(reminder.get("total_taken", 0)) + 1
        reminder["last_reason"] = None
    else:
        reminder["adherence_streak"] = 0
        reminder["total_missed"] = int(reminder.get("total_missed", 0)) + 1
        reminder["last_reason"] = body.reason

    reminder["last_status"] = status

    push_notification(
        current_user["id"],
        "reminder",
        "Dose status updated",
        f"{reminder.get('medication_node_id', 'Medication')} marked as {status}.",
        path="/reminders",
        metadata={"reminder_id": reminder_id, "status": status},
    )

    return {
        "status": "updated",
        "event": event,
        "adherence": _compute_adherence(current_user["id"]),
        "orbit_recalculation_hint": "triggered",
    }


@router.get("/adherence/summary")
async def get_adherence_summary(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)
    _auto_mark_overdue_missed(patient_id, _utc_now())
    return get_adherence_snapshot_for_patient(patient_id)


@router.delete("/{reminder_id}")
async def delete_reminder(reminder_id: str, request: Request):
    current_user = await auth_mod.get_current_user(request)

    reminder = _reminders_store.get(reminder_id)
    if not reminder or reminder["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Reminder not found")

    _reminders_store.pop(reminder_id)
    _reminder_events_store[current_user["id"]] = [
        ev for ev in _reminder_events_store.get(current_user["id"], [])
        if ev.get("reminder_id") != reminder_id
    ]
    return {"status": "deleted"}
