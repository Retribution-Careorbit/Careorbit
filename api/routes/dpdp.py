from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request
from api.middleware.auth import get_current_user
from api.middleware.audit import log_audit
from db.session import async_session

router = APIRouter(prefix="/api/auth", tags=["dpdp"])


def _row_to_dict(row):
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    if hasattr(row, "_mapping"):
        return dict(row._mapping)
    if hasattr(row, "_asdict"):
        return row._asdict()
    return {}


@router.delete("/delete-account")
async def delete_account(request: Request):
    current_user = await get_current_user(request)
    user_id = current_user["id"]

    await log_audit(user_id, user_id, "DELETE_ACCOUNT", request)

    async with async_session() as session:
        await session.execute(
            "DELETE FROM chat_messages WHERE patient_id = :uid",
            {"uid": user_id}
        )
        await session.execute(
            "DELETE FROM documents WHERE patient_id = :uid",
            {"uid": user_id}
        )
        await session.execute(
            "DELETE FROM medication_reminders WHERE patient_id = :uid",
            {"uid": user_id}
        )
        await session.execute(
            "DELETE FROM patient_profiles WHERE user_id = :uid",
            {"uid": user_id}
        )
        await session.execute(
            "DELETE FROM refresh_tokens WHERE user_id = :uid",
            {"uid": user_id}
        )
        await session.execute(
            "DELETE FROM caregiver_links WHERE patient_id = :uid OR caregiver_id = :uid",
            {"uid": user_id}
        )
        await session.execute(
            "DELETE FROM users WHERE id = :uid",
            {"uid": user_id}
        )
        await session.commit()

    return {
        "status": "account_deleted",
        "message": "Your account and all associated data have been permanently deleted per DPDP Act 2023.",
        "deleted_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/export-data")
async def export_data(request: Request):
    current_user = await get_current_user(request)
    user_id = current_user["id"]

    user_data = {"user_id": user_id}

    async with async_session() as session:
        result = await session.execute(
            "SELECT id, name, email, phone_number, date_of_birth, gender, city, state, "
            "preferred_language, tier, created_at FROM users WHERE id = :uid",
            {"uid": user_id}
        )
        row = result.first() if hasattr(result, 'first') else None
        profile = _row_to_dict(row)
        user_data["profile"] = profile if profile else {"id": user_id}

        doc_result = await session.execute(
            "SELECT id, document_type, original_filename, created_at FROM documents WHERE patient_id = :uid",
            {"uid": user_id}
        )
        raw_docs = doc_result.all() if hasattr(doc_result, 'all') else []
        user_data["documents"] = [_row_to_dict(d) or {} for d in raw_docs]

        chat_result = await session.execute(
            "SELECT id, role, message, created_at FROM chat_messages WHERE patient_id = :uid",
            {"uid": user_id}
        )
        raw_chats = chat_result.all() if hasattr(chat_result, 'all') else []
        user_data["chat_history"] = [_row_to_dict(c) or {} for c in raw_chats]

    await log_audit(user_id, user_id, "EXPORT_DATA", request)

    return {
        "status": "export_complete",
        "data": user_data,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "format": "JSON",
        "compliance": "DPDP Act 2023 Section 11",
    }
