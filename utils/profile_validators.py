from datetime import date, datetime

VALID_GENDERS = {"male", "female", "other", "prefer_not_to_say"}
VALID_LANGUAGES = {"en", "hi", "bn", "ta", "te", "mr", "gu", "kn", "ml"}
VALID_LITERACY_LEVELS = {"basic", "intermediate", "advanced"}
VALID_BLOOD_TYPES = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}


def derive_age(dob: date, reference_date: date = None) -> int:
    today = reference_date or date.today()
    age = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        age -= 1
    return age


def validate_date_of_birth(dob_str: str) -> date:
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ValueError("Invalid date format. Use YYYY-MM-DD")
    if dob > date.today():
        raise ValueError("Date of birth cannot be in the future")
    age = derive_age(dob)
    if age > 120:
        raise ValueError("Implausible date of birth")
    return dob


def validate_gender(gender: str) -> str:
    normalized = gender.strip().lower()
    if normalized not in VALID_GENDERS:
        raise ValueError(f"Invalid gender. Allowed: {', '.join(sorted(VALID_GENDERS))}")
    return normalized


def validate_preferred_language(lang: str) -> str:
    normalized = lang.strip().lower()
    if normalized not in VALID_LANGUAGES:
        raise ValueError(f"Invalid language. Allowed: {', '.join(sorted(VALID_LANGUAGES))}")
    return normalized


def validate_medical_literacy_level(level: str) -> str:
    normalized = level.strip().lower()
    if normalized not in VALID_LITERACY_LEVELS:
        raise ValueError(f"Invalid literacy level. Allowed: {', '.join(sorted(VALID_LITERACY_LEVELS))}")
    return normalized


def validate_blood_type(bt: str) -> str:
    normalized = bt.strip().upper()
    if normalized not in VALID_BLOOD_TYPES:
        raise ValueError(f"Invalid blood type. Allowed: {', '.join(sorted(VALID_BLOOD_TYPES))}")
    return normalized


def validate_height_cm(h: float) -> float:
    if h < 30.0 or h > 300.0:
        raise ValueError("Height must be between 30 and 300 cm")
    return h


def validate_weight_kg(w: float) -> float:
    if w < 1.0 or w > 500.0:
        raise ValueError("Weight must be between 1 and 500 kg")
    return w


def validate_emergency_phone(phone: str) -> str:
    import re
    if not re.match(r"^\+[1-9]\d{6,14}$", phone.strip()):
        raise ValueError("Invalid phone number. Use E.164 format (e.g., +919876543210)")
    return phone.strip()
