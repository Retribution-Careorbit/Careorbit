from services.translation_validation import validate_translation_integrity


def test_translation_integrity_accepts_numeric_preservation():
    original = "Take Metformin 500 mg twice daily for 14 days."
    translated = "Metformin 500 mg ko roz do baar 14 din tak lein."
    assert validate_translation_integrity(original, translated) is True


def test_translation_integrity_rejects_numeric_drift():
    original = "Take Metformin 500 mg twice daily for 14 days."
    translated = "Metformin 250 mg ko din mein 2 baar 7 din tak lein."
    assert validate_translation_integrity(original, translated) is False


def test_translation_integrity_rejects_empty_translation():
    assert validate_translation_integrity("HbA1c is 8.2", "") is False
