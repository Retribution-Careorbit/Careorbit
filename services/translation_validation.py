import re


def _extract_numbers(text: str) -> list[str]:
    return re.findall(r"\d+(?:\.\d+)?", str(text or ""))


def validate_translation_integrity(original_text: str, translated_text: str) -> bool:
    original = str(original_text or "").strip()
    translated = str(translated_text or "").strip()

    if not translated:
        return False

    # Clinical safety guard: numeric clinical values must survive translation.
    return _extract_numbers(original) == _extract_numbers(translated)
