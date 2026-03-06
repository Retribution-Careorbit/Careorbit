DEMO_USER_ID = "demo-ramesh-kumar-001"
DEMO_EMAIL = "ramesh@careorbit.dev"
DEMO_PASSWORD = "Ramesh123!"

RAMESH_PROFILE = {
    "id": DEMO_USER_ID,
    "name": "Ramesh Kumar",
    "email": DEMO_EMAIL,
    "phone_number": "+919876543210",
    "date_of_birth": "1958-03-15",
    "age": 68,
    "gender": "male",
    "city": "Durgapur",
    "state": "West Bengal",
    "preferred_language": "hi",
    "medical_literacy_level": "basic",
    "tier": "free",
    "onboarding_completed_at": "2026-01-10T08:00:00+00:00",
}

RAMESH_CONDITIONS = [
    {"name": "Type 2 Diabetes Mellitus", "code": "E11.9", "confidence": 0.85, "node_type": "condition"},
    {"name": "Essential Hypertension", "code": "I10", "confidence": 0.82, "node_type": "condition"},
    {"name": "Dyslipidemia", "code": "E78.5", "confidence": 0.78, "node_type": "condition"},
]

RAMESH_MEDICATIONS = [
    {"name": "Metformin", "dosage": "500mg BD", "frequency": "twice daily", "rxnorm": "6809", "confidence": 0.85, "confidence_label": "HIGH", "node_type": "medication"},
    {"name": "Amlodipine", "dosage": "5mg OD", "frequency": "once daily", "rxnorm": "17767", "confidence": 0.82, "confidence_label": "HIGH", "node_type": "medication"},
    {"name": "Atorvastatin", "dosage": "10mg HS", "frequency": "once daily at bedtime", "rxnorm": "83367", "confidence": 0.78, "confidence_label": "MODERATE", "node_type": "medication"},
    {"name": "Aspirin", "dosage": "75mg OD", "frequency": "once daily", "rxnorm": "1191", "confidence": 0.90, "confidence_label": "VERIFIED", "node_type": "medication"},
    {"name": "Ibuprofen", "dosage": "400mg SOS", "frequency": "as needed", "rxnorm": "5640", "confidence": 0.65, "confidence_label": "MODERATE", "node_type": "medication"},
]

RAMESH_LABS = [
    {"name": "HbA1c", "value": 7.8, "unit": "%", "ref_low": None, "ref_high": 5.6, "loinc": "4548-4", "abnormal": True, "reference_range": "<5.7%", "node_type": "lab_value"},
    {"name": "Creatinine", "value": 1.4, "unit": "mg/dL", "ref_low": 0.7, "ref_high": 1.3, "loinc": "2160-0", "abnormal": True, "reference_range": "0.7-1.3 mg/dL", "node_type": "lab_value"},
    {"name": "eGFR", "value": 52, "unit": "mL/min", "ref_low": 90, "ref_high": None, "loinc": "33914-3", "abnormal": True, "reference_range": ">90 mL/min", "node_type": "lab_value"},
]

RAMESH_INTERACTIONS = [
    {
        "drug_pair": "Metformin + Ibuprofen",
        "severity": "ELEVATED",
        "description": "NSAIDs may decrease renal function, increasing risk of lactic acidosis with Metformin. Ramesh's eGFR is 52 mL/min (below 60), elevating this risk.",
        "clinical_action": "Monitor renal function closely. Consider alternative analgesic.",
        "acknowledged": False,
    },
]

RAMESH_CARE_GAPS = [
    {"name": "Diabetic Retinopathy Screening", "status": "open", "description": "Annual eye exam recommended for Type 2 Diabetes"},
]

RAMESH_ORBIT_HISTORY = [
    {"total_score": 35.0, "computed_at": "2026-01-10T08:00:00+00:00", "delta": None},
    {"total_score": 48.5, "computed_at": "2026-01-20T10:30:00+00:00", "delta": 13.5},
    {"total_score": 55.2, "computed_at": "2026-02-01T14:00:00+00:00", "delta": 6.7},
    {"total_score": 61.8, "computed_at": "2026-02-15T09:00:00+00:00", "delta": 6.6},
]

RAMESH_NARRATIVE = (
    "Ramesh Kumar is a 68-year-old male from Durgapur, West Bengal, "
    "managing Type 2 Diabetes Mellitus, Essential Hypertension, and Dyslipidemia. "
    "He currently takes Metformin 500mg twice daily, Amlodipine 5mg once daily, "
    "Atorvastatin 10mg at bedtime, Aspirin 75mg once daily, and Ibuprofen 400mg as needed. "
    "Recent lab results show an HbA1c of 7.8% (above target of <5.7%), "
    "Creatinine of 1.4 mg/dL (mildly elevated), and eGFR of 52 mL/min "
    "indicating Stage 3a chronic kidney disease. "
    "An ELEVATED drug interaction has been flagged between Metformin and Ibuprofen "
    "due to reduced renal function. Ramesh Kumar's health profile is steadily improving "
    "as more records are uploaded and confirmed."
)


def get_phig_for_orbit():
    nodes = []
    for med in RAMESH_MEDICATIONS:
        nodes.append({"type": "medication", "name": med["name"], "confidence": med["confidence"]})
    for cond in RAMESH_CONDITIONS:
        nodes.append({"type": "condition", "name": cond["name"], "confidence": cond["confidence"]})
    for lab in RAMESH_LABS:
        nodes.append({"type": "lab_value", "name": lab["name"], "value": lab["value"], "confidence": 0.90})
    nodes.append({"type": "care_gap", "name": RAMESH_CARE_GAPS[0]["name"]})

    interactions = []
    for ix in RAMESH_INTERACTIONS:
        interactions.append({"severity": ix["severity"], "acknowledged": ix["acknowledged"]})

    care_gaps = []
    for cg in RAMESH_CARE_GAPS:
        care_gaps.append({"name": cg["name"], "status": cg["status"]})

    return {
        "nodes": nodes,
        "interactions": interactions,
        "care_gaps": care_gaps,
    }
