def medication_to_fhir(med: dict) -> dict:
    coding = []
    if med.get("rxnorm"):
        coding.append({
            "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
            "code": med["rxnorm"],
            "display": med.get("name", ""),
        })

    dosage_instruction = []
    if med.get("dosage"):
        dosage_instruction.append({"text": med["dosage"]})

    return {
        "resourceType": "MedicationStatement",
        "status": "active",
        "medicationCodeableConcept": {
            "coding": coding,
            "text": med.get("name", ""),
        },
        "dosageInstruction": dosage_instruction,
    }


def lab_to_fhir(lab: dict) -> dict:
    coding = []
    if lab.get("loinc"):
        coding.append({
            "system": "http://loinc.org",
            "code": lab["loinc"],
            "display": lab.get("name", ""),
        })

    value_quantity = {}
    if lab.get("value") is not None:
        value_quantity["value"] = lab["value"]
    if lab.get("unit"):
        value_quantity["unit"] = lab["unit"]

    reference_range = []
    ref_low = lab.get("ref_low")
    ref_high = lab.get("ref_high")
    if ref_low is not None or ref_high is not None:
        range_entry = {}
        if ref_low is not None:
            range_entry["low"] = {"value": ref_low, "unit": lab.get("unit", "")}
        if ref_high is not None:
            range_entry["high"] = {"value": ref_high, "unit": lab.get("unit", "")}
        reference_range.append(range_entry)

    return {
        "resourceType": "Observation",
        "status": "final",
        "code": {
            "coding": coding,
            "text": lab.get("name", ""),
        },
        "valueQuantity": value_quantity,
        "referenceRange": reference_range,
    }
