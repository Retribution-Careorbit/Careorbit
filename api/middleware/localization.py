from __future__ import annotations

from typing import Any

from db.session import async_session
from db.seed_demo import get_seed_value_for_patient
from services.azure_translator import AzureTranslatorService

_translator = AzureTranslatorService()

_TRANSLATABLE_TEXT_KEYS = {
    "summary",
    "message",
    "description",
    "clinical_action",
    "validation_notes",
    "frequency",
    "dose_to_take",
    "error_message",
    "title",
    "narrative",
    "event",
    "impact",
    "focus",
    "action",
    "why",
    "label",
    "clinical_priorities",
}


def get_patient_preferred_language(patient_id: str, fallback: str = "en") -> str:
    try:
        from api.routes.auth import _users_store

        user = _users_store.get(patient_id, {})
        lang = str(user.get("preferred_language") or "").strip().lower()
        if lang:
            return lang
    except Exception:
        pass

    profile = get_seed_value_for_patient(patient_id, "profile", {}) or {}
    lang = str(profile.get("preferred_language") or "").strip().lower()
    if lang:
        return lang

    return fallback


async def get_patient_preferred_language_async(patient_id: str, fallback: str = "en") -> str:
    in_memory = get_patient_preferred_language(patient_id, fallback="")
    if in_memory:
        return in_memory

    try:
        async with async_session() as session:
            result = await session.execute(
                "SELECT preferred_language FROM users WHERE id = :uid LIMIT 1",
                {"uid": patient_id},
            )
            row = result.mappings().first() if hasattr(result, "mappings") else None
            db_lang = str((row or {}).get("preferred_language") or "").strip().lower()
            if db_lang:
                return db_lang
    except Exception:
        pass

    return fallback


async def translate_text_for_patient(text: str, patient_id: str) -> str:
    language = await get_patient_preferred_language_async(patient_id)
    if language != "hi":
        return text
    if not isinstance(text, str) or not text.strip():
        return text

    try:
        return await _translator.translate(text, "hi")
    except Exception:
        return text


async def localize_payload_for_patient(payload: Any, patient_id: str) -> Any:
    language = await get_patient_preferred_language_async(patient_id)
    if language != "hi":
        return payload

    async def _translate_value(value: Any, key: str | None = None) -> Any:
        if isinstance(value, dict):
            localized: dict[str, Any] = {}
            for child_key, child_value in value.items():
                localized[child_key] = await _translate_value(child_value, child_key)
            return localized

        if isinstance(value, list):
            return [await _translate_value(item, key) for item in value]

        if isinstance(value, str):
            if not value.strip():
                return value
            if key == "reasons":
                return await translate_text_for_patient(value, patient_id)
            if key in _TRANSLATABLE_TEXT_KEYS:
                return await translate_text_for_patient(value, patient_id)
            return value

        return value

    return await _translate_value(payload)
