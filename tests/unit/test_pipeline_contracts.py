from pipeline.contracts import validate_extraction_payload


def test_validate_extraction_payload_normalizes_and_filters_invalid_items():
    payload = {
        "medications": [
            {"name": "  Metformin  ", "dosage": "500mg", "frequency": "BD", "condition_code": " e11.9 "},
            {"name": "x"},
            "not-a-dict",
        ],
        "labs": [
            {"name": "  HbA1c ", "value": "7.4", "unit": "%", "condition_code": " e11.9 "},
            {"name": "Creatinine", "value": "not-a-number"},
        ],
        "conditions": [
            {"name": "  Type 2 diabetes  ", "code": " e11.9 ", "confidence": 0.9},
            {"name": ""},
        ],
    }

    validated = validate_extraction_payload(payload)

    assert len(validated["medications"]) == 1
    assert validated["medications"][0]["name"] == "Metformin"
    assert validated["medications"][0]["condition_code"] == "E11.9"

    assert len(validated["labs"]) == 1
    assert validated["labs"][0]["name"] == "HbA1c"
    assert validated["labs"][0]["value"] == 7.4
    assert validated["labs"][0]["condition_code"] == "E11.9"

    assert len(validated["conditions"]) == 1
    assert validated["conditions"][0]["name"] == "Type 2 diabetes"
    assert validated["conditions"][0]["code"] == "E11.9"
