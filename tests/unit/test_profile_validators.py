import pytest
from datetime import date
from utils.profile_validators import (
    validate_date_of_birth, validate_gender, validate_preferred_language,
    validate_medical_literacy_level, validate_blood_type,
    validate_height_cm, validate_weight_kg, validate_emergency_phone,
    derive_age,
)


class TestDeriveAge:

    def test_age_basic(self):
        today = date(2026, 3, 6)
        assert derive_age(date(1990, 1, 1), today) == 36

    def test_age_birthday_today(self):
        today = date(2026, 3, 6)
        assert derive_age(date(1990, 3, 6), today) == 36

    def test_age_birthday_tomorrow(self):
        today = date(2026, 3, 6)
        assert derive_age(date(1990, 3, 7), today) == 35

    def test_age_newborn(self):
        today = date(2026, 3, 6)
        assert derive_age(date(2026, 1, 1), today) == 0

    def test_age_elderly(self):
        today = date(2026, 3, 6)
        assert derive_age(date(1920, 1, 1), today) == 106


class TestValidateDateOfBirth:

    def test_valid_date(self):
        result = validate_date_of_birth("1990-05-15")
        assert result == date(1990, 5, 15)

    def test_valid_date_elderly(self):
        result = validate_date_of_birth("1930-01-01")
        assert result == date(1930, 1, 1)

    def test_future_date_rejected(self):
        with pytest.raises(ValueError, match="future"):
            validate_date_of_birth("2099-01-01")

    def test_implausible_age_rejected(self):
        with pytest.raises(ValueError, match="Implausible"):
            validate_date_of_birth("1800-01-01")

    def test_invalid_format_rejected(self):
        with pytest.raises(ValueError, match="Invalid date format"):
            validate_date_of_birth("not-a-date")

    def test_wrong_format_rejected(self):
        with pytest.raises(ValueError, match="Invalid date format"):
            validate_date_of_birth("15/05/1990")

    def test_empty_string_rejected(self):
        with pytest.raises(ValueError):
            validate_date_of_birth("")


class TestValidateGender:

    @pytest.mark.parametrize("gender", ["male", "female", "other", "prefer_not_to_say"])
    def test_valid_genders(self, gender):
        assert validate_gender(gender) == gender

    def test_case_normalization(self):
        assert validate_gender("Male") == "male"
        assert validate_gender("FEMALE") == "female"

    def test_whitespace_stripped(self):
        assert validate_gender("  male  ") == "male"

    def test_invalid_gender_rejected(self):
        with pytest.raises(ValueError, match="Invalid gender"):
            validate_gender("unknown")


class TestValidatePreferredLanguage:

    @pytest.mark.parametrize("lang", ["en", "hi", "bn", "ta", "te", "mr", "gu", "kn", "ml"])
    def test_valid_languages(self, lang):
        assert validate_preferred_language(lang) == lang

    def test_case_normalization(self):
        assert validate_preferred_language("EN") == "en"
        assert validate_preferred_language("Hi") == "hi"

    def test_invalid_language_rejected(self):
        with pytest.raises(ValueError, match="Invalid language"):
            validate_preferred_language("fr")


class TestValidateMedicalLiteracyLevel:

    @pytest.mark.parametrize("level", ["basic", "intermediate", "advanced"])
    def test_valid_levels(self, level):
        assert validate_medical_literacy_level(level) == level

    def test_case_normalization(self):
        assert validate_medical_literacy_level("Basic") == "basic"
        assert validate_medical_literacy_level("ADVANCED") == "advanced"

    def test_invalid_level_rejected(self):
        with pytest.raises(ValueError, match="Invalid literacy level"):
            validate_medical_literacy_level("expert")


class TestValidateBloodType:

    @pytest.mark.parametrize("bt", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
    def test_valid_blood_types(self, bt):
        assert validate_blood_type(bt) == bt

    def test_case_normalization(self):
        assert validate_blood_type("a+") == "A+"
        assert validate_blood_type("ab-") == "AB-"

    def test_invalid_blood_type_rejected(self):
        with pytest.raises(ValueError, match="Invalid blood type"):
            validate_blood_type("C+")


class TestValidateHeightCm:

    def test_valid_height(self):
        assert validate_height_cm(170.0) == 170.0

    def test_minimum_height(self):
        assert validate_height_cm(30.0) == 30.0

    def test_maximum_height(self):
        assert validate_height_cm(300.0) == 300.0

    def test_below_minimum_rejected(self):
        with pytest.raises(ValueError, match="between 30 and 300"):
            validate_height_cm(10.0)

    def test_above_maximum_rejected(self):
        with pytest.raises(ValueError, match="between 30 and 300"):
            validate_height_cm(350.0)


class TestValidateWeightKg:

    def test_valid_weight(self):
        assert validate_weight_kg(70.0) == 70.0

    def test_minimum_weight(self):
        assert validate_weight_kg(1.0) == 1.0

    def test_maximum_weight(self):
        assert validate_weight_kg(500.0) == 500.0

    def test_below_minimum_rejected(self):
        with pytest.raises(ValueError, match="between 1 and 500"):
            validate_weight_kg(0.5)

    def test_above_maximum_rejected(self):
        with pytest.raises(ValueError, match="between 1 and 500"):
            validate_weight_kg(600.0)


class TestValidateEmergencyPhone:

    def test_valid_indian_phone(self):
        assert validate_emergency_phone("+919876543210") == "+919876543210"

    def test_valid_us_phone(self):
        assert validate_emergency_phone("+12025551234") == "+12025551234"

    def test_whitespace_stripped(self):
        assert validate_emergency_phone("  +919876543210  ") == "+919876543210"

    def test_no_plus_rejected(self):
        with pytest.raises(ValueError, match="E.164"):
            validate_emergency_phone("919876543210")

    def test_too_short_rejected(self):
        with pytest.raises(ValueError, match="E.164"):
            validate_emergency_phone("+123")

    def test_letters_rejected(self):
        with pytest.raises(ValueError, match="E.164"):
            validate_emergency_phone("+91abcdefghij")
