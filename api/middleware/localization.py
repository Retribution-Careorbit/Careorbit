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

_HI_TEXT_OVERRIDES = {
    "Ramesh Kumar is a 68-year-old male from Durgapur, West Bengal, managing Type 2 Diabetes Mellitus, Essential Hypertension, and Dyslipidemia. He currently takes Metformin 500mg twice daily, Amlodipine 5mg once daily, Atorvastatin 10mg at bedtime, Aspirin 75mg once daily, and Ibuprofen 400mg as needed. Recent lab results show an HbA1c of 7.8% (above target of <5.7%), Creatinine of 1.4 mg/dL (mildly elevated), and eGFR of 52 mL/min indicating Stage 3a chronic kidney disease. An ELEVATED drug interaction has been flagged between Metformin and Ibuprofen due to reduced renal function. Ramesh Kumar's health profile is steadily improving as more records are uploaded and confirmed.": "रमेश कुमार, 68 वर्षीय पुरुष, दुर्गापुर (पश्चिम बंगाल) के निवासी हैं और टाइप 2 डायबिटीज, आवश्यक उच्च रक्तचाप तथा डिस्लिपिडेमिया का प्रबंधन कर रहे हैं। वे वर्तमान में मेटफॉर्मिन 500mg दिन में दो बार, एम्लोडिपिन 5mg दिन में एक बार, एटोरवास्टेटिन 10mg रात में, एस्पिरिन 75mg दिन में एक बार और इबुप्रोफेन 400mg आवश्यकता अनुसार लेते हैं। हाल की लैब रिपोर्ट में HbA1c 7.8% (लक्ष्य <5.7% से अधिक), क्रिएटिनिन 1.4 mg/dL (हल्का बढ़ा हुआ) और eGFR 52 mL/min (स्टेज 3a क्रोनिक किडनी डिज़ीज़) दिखा। कम गुर्दा कार्यक्षमता के कारण मेटफॉर्मिन और इबुप्रोफेन के बीच उच्च-स्तरीय दवा इंटरैक्शन चिन्हित हुआ है। अधिक रिकॉर्ड अपलोड और पुष्टि होने से रमेश कुमार की स्वास्थ्य प्रोफ़ाइल लगातार बेहतर हो रही है।",
    "Harish Chandra Kumar is an 86-year-old male with coronary artery disease and chronic kidney disease stage 3. He is on Telmisartan, Clopidogrel, Rosuvastatin, and Tamsulosin with improving blood pressure trends. Recent labs show persistent kidney risk with eGFR of 44 mL/min and Creatinine of 1.6 mg/dL, and mild anemia.": "हरीश चंद्र कुमार, 86 वर्षीय पुरुष, कोरोनरी आर्टरी रोग और स्टेज 3 क्रोनिक किडनी डिज़ीज़ से पीड़ित हैं। वे टेल्मिसार्टन, क्लोपिडोग्रेल, रोसुवास्टेटिन और टैम्सुलोसिन ले रहे हैं, तथा रक्तचाप की प्रवृत्ति में सुधार दिख रहा है। हाल की लैब रिपोर्ट में eGFR 44 mL/min और क्रिएटिनिन 1.6 mg/dL के साथ लगातार किडनी जोखिम तथा हल्का एनीमिया दर्शाया गया है।",
    "Family onboarding completed": "परिवार ऑनबोर्डिंग पूर्ण",
    "Profile activated under family plan": "फैमिली प्लान के तहत प्रोफ़ाइल सक्रिय",
    "Cardiology review done": "कार्डियोलॉजी समीक्षा पूर्ण",
    "Medication plan stabilized": "दवा योजना स्थिर हुई",
    "Renal panel uploaded": "रीनल पैनल अपलोड हुआ",
    "CKD risk monitoring tightened": "सीकेडी जोखिम निगरानी कड़ी की गई",
    "Onboarding completed": "ऑनबोर्डिंग पूर्ण",
    "Profile baseline established": "प्रोफ़ाइल बेसलाइन स्थापित",
    "HbA1c reduced": "HbA1c में कमी",
    "Glycemic control trend improving": "ग्लाइसेमिक नियंत्रण प्रवृत्ति में सुधार",
    "Blood pressure stabilized": "रक्तचाप स्थिर",
    "Reduced hypertension risk trajectory": "उच्च रक्तचाप जोखिम प्रवृत्ति घटी",
    "Medication adherence streak": "दवा अनुपालन श्रृंखला",
    "Higher expected Orbit score reliability": "ऑर्बिट स्कोर विश्वसनीयता में सुधार",
    "twice daily": "दिन में दो बार",
    "once daily": "दिन में एक बार",
    "once daily at bedtime": "रात में दिन में एक बार",
    "as needed": "आवश्यकता अनुसार",
    "Mark reminders on time and avoid missing evening doses for 7 consecutive days.": "रिमाइंडर समय पर चिह्नित करें और लगातार 7 दिनों तक शाम की खुराक न छोड़ें।",
    "Adherence consistency directly improves confidence and Orbit score stability.": "अनुपालन की निरंतरता सीधे कॉन्फिडेंस और ऑर्बिट स्कोर स्थिरता को बेहतर करती है।",
    "Target fasting glucose under 130 mg/dL and review Metformin timing with your doctor.": "फास्टिंग ग्लूकोज़ 130 mg/dL से नीचे रखने का लक्ष्य रखें और अपने डॉक्टर के साथ मेटफॉर्मिन का समय पुनः देखें।",
    "Lower HbA1c trends significantly improve overall risk-adjusted scoring.": "HbA1c में गिरावट की प्रवृत्ति समग्र जोखिम-समायोजित स्कोर को उल्लेखनीय रूप से बेहतर करती है।",
    "Avoid NSAIDs unless prescribed and repeat renal panel in 2-4 weeks.": "डॉक्टर द्वारा लिखे बिना NSAIDs से बचें और 2-4 सप्ताह में रीनल पैनल दोहराएँ।",
    "Improving renal risk factors reduces medication interaction penalties.": "गुर्दा जोखिम कारकों में सुधार से दवा इंटरैक्शन दंड कम होता है।",
}

_HI_PHRASE_REPLACEMENTS = [
    ("Interaction Alerts", "इंटरैक्शन अलर्ट"),
    ("No upcoming appointments", "कोई आगामी अपॉइंटमेंट नहीं"),
    ("Upcoming", "आगामी"),
    ("Past", "पिछले"),
    ("Completed", "पूर्ण"),
]


def _fallback_hi_transform(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return text
    mapped = _HI_TEXT_OVERRIDES.get(text)
    if mapped:
        return mapped

    updated = text
    for src, dst in _HI_PHRASE_REPLACEMENTS:
        updated = updated.replace(src, dst)
    return updated


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

    fallback_text = _fallback_hi_transform(text)
    if fallback_text != text:
        return fallback_text

    try:
        return await _translator.translate(text, "hi")
    except Exception:
        return fallback_text


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
