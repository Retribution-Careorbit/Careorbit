DEMO_USER_ID = "demo-ramesh-kumar-001"
DEMO_EMAIL = "ramesh@careorbit.dev"
DEMO_PASSWORD = "Ramesh123!"
FATHER_USER_ID = "demo-harish-kumar-002"
FATHER_EMAIL = "harish@careorbit.dev"
FATHER_PASSWORD = "Harish123!"

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

FATHER_PROFILE = {
    "id": FATHER_USER_ID,
    "name": "Harish Chandra Kumar",
    "email": FATHER_EMAIL,
    "phone_number": "+919876543310",
    "date_of_birth": "1939-11-02",
    "age": 86,
    "gender": "male",
    "city": "Durgapur",
    "state": "West Bengal",
    "preferred_language": "hi",
    "medical_literacy_level": "basic",
    "tier": "premium_family",
    "onboarding_completed_at": "2026-01-11T09:00:00+00:00",
}

RAMESH_CONDITIONS = [
    {"name": "Type 2 Diabetes Mellitus", "code": "E11.9", "confidence": 0.85, "node_type": "condition"},
    {"name": "Essential Hypertension", "code": "I10", "confidence": 0.82, "node_type": "condition"},
    {"name": "Dyslipidemia", "code": "E78.5", "confidence": 0.78, "node_type": "condition"},
]

RAMESH_MEDICATIONS = [
    {"name": "Metformin", "dosage": "500mg BD", "frequency": "twice daily", "rxnorm": "6809", "confidence": 0.85, "confidence_label": "HIGH", "prescribed_by_doctor": "Dr. Anjali Sharma", "node_type": "medication"},
    {"name": "Amlodipine", "dosage": "5mg OD", "frequency": "once daily", "rxnorm": "17767", "confidence": 0.82, "confidence_label": "HIGH", "prescribed_by_doctor": "Dr. Priya Gupta", "node_type": "medication"},
    {"name": "Atorvastatin", "dosage": "10mg HS", "frequency": "once daily at bedtime", "rxnorm": "83367", "confidence": 0.78, "confidence_label": "MODERATE", "prescribed_by_doctor": "Dr. Rajesh Mehta", "node_type": "medication"},
    {"name": "Aspirin", "dosage": "75mg OD", "frequency": "once daily", "rxnorm": "1191", "confidence": 0.90, "confidence_label": "VERIFIED", "prescribed_by_doctor": "Dr. Priya Gupta", "node_type": "medication"},
    {"name": "Ibuprofen", "dosage": "400mg SOS", "frequency": "as needed", "rxnorm": "5640", "confidence": 0.65, "confidence_label": "MODERATE", "prescribed_by_doctor": "Dr. Rajesh Mehta", "node_type": "medication"},
]

RAMESH_LABS = [
    {"name": "HbA1c", "value": 7.8, "unit": "%", "ref_low": None, "ref_high": 5.6, "loinc": "4548-4", "abnormal": True, "reference_range": "<5.7%", "node_type": "lab_value"},
    {"name": "Creatinine", "value": 1.4, "unit": "mg/dL", "ref_low": 0.7, "ref_high": 1.3, "loinc": "2160-0", "abnormal": True, "reference_range": "0.7-1.3 mg/dL", "node_type": "lab_value"},
    {"name": "eGFR", "value": 52, "unit": "mL/min", "ref_low": 90, "ref_high": None, "loinc": "33914-3", "abnormal": True, "reference_range": ">90 mL/min", "node_type": "lab_value"},
    {"name": "TSH", "value": 6.2, "unit": "uIU/mL", "ref_low": 0.4, "ref_high": 4.5, "loinc": "3016-3", "abnormal": True, "reference_range": "0.4-4.5 uIU/mL", "node_type": "lab_value"},
    {"name": "ALT", "value": 74, "unit": "U/L", "ref_low": 7, "ref_high": 55, "loinc": "1742-6", "abnormal": True, "reference_range": "7-55 U/L", "node_type": "lab_value"},
]

RAMESH_LAB_HISTORY = [
    {
        "area_key": "glycemic_control",
        "area_label": "Glycemic Control",
        "marker_name": "HbA1c",
        "unit": "%",
        "ref_low": None,
        "ref_high": 5.6,
        "points": [
            {"date": "2025-09-10", "value": 8.6},
            {"date": "2025-11-10", "value": 8.2},
            {"date": "2026-01-10", "value": 8.0},
            {"date": "2026-02-22", "value": 7.8},
        ],
    },
    {
        "area_key": "renal_function",
        "area_label": "Renal Function",
        "marker_name": "eGFR",
        "unit": "mL/min",
        "ref_low": 90,
        "ref_high": None,
        "points": [
            {"date": "2025-09-10", "value": 66},
            {"date": "2025-11-10", "value": 61},
            {"date": "2026-01-10", "value": 56},
            {"date": "2026-02-22", "value": 52},
        ],
    },
    {
        "area_key": "renal_marker",
        "area_label": "Kidney Enzyme Marker",
        "marker_name": "Creatinine",
        "unit": "mg/dL",
        "ref_low": 0.7,
        "ref_high": 1.3,
        "points": [
            {"date": "2025-09-10", "value": 1.18},
            {"date": "2025-11-10", "value": 1.26},
            {"date": "2026-01-10", "value": 1.34},
            {"date": "2026-02-22", "value": 1.40},
        ],
    },
    {
        "area_key": "thyroid",
        "area_label": "Thyroid Function",
        "marker_name": "TSH",
        "unit": "uIU/mL",
        "ref_low": 0.4,
        "ref_high": 4.5,
        "points": [
            {"date": "2025-09-10", "value": 4.9},
            {"date": "2025-11-10", "value": 5.3},
            {"date": "2026-01-10", "value": 5.7},
            {"date": "2026-02-22", "value": 6.2},
        ],
    },
    {
        "area_key": "liver_enzyme",
        "area_label": "Liver Enzyme Load",
        "marker_name": "ALT",
        "unit": "U/L",
        "ref_low": 7,
        "ref_high": 55,
        "points": [
            {"date": "2025-09-10", "value": 58},
            {"date": "2025-11-10", "value": 62},
            {"date": "2026-01-10", "value": 68},
            {"date": "2026-02-22", "value": 74},
        ],
    },
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

RAMESH_VITALS = [
    {"date": "2026-01-10", "type": "blood_pressure", "systolic": 148, "diastolic": 92, "heart_rate": 78},
    {"date": "2026-01-17", "type": "blood_pressure", "systolic": 142, "diastolic": 88, "heart_rate": 76},
    {"date": "2026-01-24", "type": "blood_pressure", "systolic": 138, "diastolic": 86, "heart_rate": 74},
    {"date": "2026-02-01", "type": "blood_pressure", "systolic": 135, "diastolic": 84, "heart_rate": 72},
    {"date": "2026-02-08", "type": "blood_pressure", "systolic": 132, "diastolic": 82, "heart_rate": 73},
    {"date": "2026-02-15", "type": "blood_pressure", "systolic": 130, "diastolic": 80, "heart_rate": 71},
    {"date": "2026-02-22", "type": "blood_pressure", "systolic": 128, "diastolic": 79, "heart_rate": 70},
    {"date": "2026-01-10", "type": "glucose", "fasting": 165, "post_meal": 220},
    {"date": "2026-01-24", "type": "glucose", "fasting": 155, "post_meal": 210},
    {"date": "2026-02-08", "type": "glucose", "fasting": 142, "post_meal": 195},
    {"date": "2026-02-22", "type": "glucose", "fasting": 138, "post_meal": 185},
    {"date": "2026-01-10", "type": "weight", "value": 82.5, "unit": "kg"},
    {"date": "2026-01-24", "type": "weight", "value": 81.8, "unit": "kg"},
    {"date": "2026-02-08", "type": "weight", "value": 81.2, "unit": "kg"},
    {"date": "2026-02-22", "type": "weight", "value": 80.5, "unit": "kg"},
    {"date": "2026-01-10", "type": "temperature", "value": 98.4, "unit": "F"},
    {"date": "2026-02-01", "type": "temperature", "value": 98.6, "unit": "F"},
    {"date": "2026-02-15", "type": "temperature", "value": 98.2, "unit": "F"},
]

RAMESH_APPOINTMENTS = [
    {
        "appointment_id": "appt-001",
        "doctor_name": "Dr. Anjali Sharma",
        "specialization": "Endocrinologist",
        "appointment_datetime": "2026-03-15T10:30:00+05:30",
        "clinic_name": "Apollo Clinic, Durgapur",
        "status": "upcoming",
        "brief_scheduled": True,
    },
    {
        "appointment_id": "appt-002",
        "doctor_name": "Dr. Rajesh Mehta",
        "specialization": "Nephrologist",
        "appointment_datetime": "2026-03-22T14:00:00+05:30",
        "clinic_name": "AMRI Hospital, Kolkata",
        "status": "upcoming",
        "brief_scheduled": False,
    },
    {
        "appointment_id": "appt-003",
        "doctor_name": "Dr. Priya Gupta",
        "specialization": "General Physician",
        "appointment_datetime": "2026-02-10T09:00:00+05:30",
        "clinic_name": "City Health Center",
        "status": "completed",
        "brief_scheduled": False,
        "visit_summary": "Follow-up visit focusing on BP stabilization and medication adherence.",
        "visit_findings": [
            "Blood pressure controlled at 128/79 with stable heart rate.",
            "Fasting glucose showing downward trend; continue dietary plan.",
            "Kidney function remains borderline; avoid NSAIDs.",
        ],
        "doctor_notes": "Continue current regimen, repeat labs in 6 weeks, and ensure hydration.",
        "visit_prescriptions": [
            {"name": "Metformin", "dosage": "500mg BD"},
            {"name": "Amlodipine", "dosage": "5mg OD"},
            {"name": "Atorvastatin", "dosage": "10mg HS"},
        ],
    },
]

RAMESH_UPLOADED_DOCUMENTS = [
    {
        "document_id": "doc-001",
        "file_name": "prescription_feb_2026.pdf",
        "document_type": "prescription",
        "valid": True,
        "uploaded_at": "2026-02-15T08:20:00+05:30",
        "doctor_name": "Dr. Priya Gupta",
        "summary": "Prescription for diabetes, BP, and lipid management.",
        "file_url": "https://careorbitstorage.blob.core.windows.net/documents/prescription_feb_2026.pdf",
    },
    {
        "document_id": "doc-002",
        "file_name": "lab_report_feb_2026.pdf",
        "document_type": "lab_report",
        "valid": True,
        "uploaded_at": "2026-02-22T09:10:00+05:30",
        "doctor_name": "Apollo Clinic Lab",
        "summary": "HbA1c, creatinine, eGFR, TSH, ALT results.",
        "file_url": "/api/documents/file/doc-002",
        "extracted_markers": [
            {"name": "HbA1c", "value": 7.8, "unit": "%", "ref_low": None, "ref_high": 5.6},
            {"name": "Creatinine", "value": 1.4, "unit": "mg/dL", "ref_low": 0.7, "ref_high": 1.3},
            {"name": "eGFR", "value": 52, "unit": "mL/min", "ref_low": 90, "ref_high": None},
            {"name": "TSH", "value": 6.2, "unit": "uIU/mL", "ref_low": 0.4, "ref_high": 4.5},
            {"name": "ALT", "value": 74, "unit": "U/L", "ref_low": 7, "ref_high": 55},
        ],
    },
    {
        "document_id": "doc-004",
        "file_name": "lab_report_jan_2026.pdf",
        "document_type": "lab_report",
        "valid": True,
        "uploaded_at": "2026-01-10T08:55:00+05:30",
        "doctor_name": "Apollo Clinic Lab",
        "summary": "HbA1c, creatinine and eGFR panel.",
        "file_url": "/api/documents/file/doc-004",
        "extracted_markers": [
            {"name": "HbA1c", "value": 8.0, "unit": "%", "ref_low": None, "ref_high": 5.6},
            {"name": "Creatinine", "value": 1.34, "unit": "mg/dL", "ref_low": 0.7, "ref_high": 1.3},
            {"name": "eGFR", "value": 56, "unit": "mL/min", "ref_low": 90, "ref_high": None},
        ],
    },
    {
        "document_id": "doc-005",
        "file_name": "lab_report_nov_2025.pdf",
        "document_type": "lab_report",
        "valid": True,
        "uploaded_at": "2025-11-10T09:40:00+05:30",
        "doctor_name": "AMRI Diagnostic Lab",
        "summary": "Renal and thyroid profile follow-up.",
        "file_url": "/api/documents/file/doc-005",
        "extracted_markers": [
            {"name": "Creatinine", "value": 1.26, "unit": "mg/dL", "ref_low": 0.7, "ref_high": 1.3},
            {"name": "eGFR", "value": 61, "unit": "mL/min", "ref_low": 90, "ref_high": None},
            {"name": "TSH", "value": 5.3, "unit": "uIU/mL", "ref_low": 0.4, "ref_high": 4.5},
            {"name": "ALT", "value": 62, "unit": "U/L", "ref_low": 7, "ref_high": 55},
        ],
    },
    {
        "document_id": "doc-006",
        "file_name": "lab_report_sep_2025.pdf",
        "document_type": "lab_report",
        "valid": True,
        "uploaded_at": "2025-09-10T08:05:00+05:30",
        "doctor_name": "City Health Lab",
        "summary": "Baseline glycemic, kidney, thyroid, and liver markers.",
        "file_url": "/api/documents/file/doc-006",
        "extracted_markers": [
            {"name": "HbA1c", "value": 8.6, "unit": "%", "ref_low": None, "ref_high": 5.6},
            {"name": "Creatinine", "value": 1.18, "unit": "mg/dL", "ref_low": 0.7, "ref_high": 1.3},
            {"name": "eGFR", "value": 66, "unit": "mL/min", "ref_low": 90, "ref_high": None},
            {"name": "TSH", "value": 4.9, "unit": "uIU/mL", "ref_low": 0.4, "ref_high": 4.5},
            {"name": "ALT", "value": 58, "unit": "U/L", "ref_low": 7, "ref_high": 55},
        ],
    },
    {
        "document_id": "doc-007",
        "file_name": "lab_report_invalid_blur_2025.pdf",
        "document_type": "lab_report",
        "valid": False,
        "uploaded_at": "2025-10-01T10:15:00+05:30",
        "doctor_name": "Unknown",
        "summary": "Low confidence OCR extraction; values not trusted.",
        "file_url": "/api/documents/file/doc-007",
    },
    {
        "document_id": "doc-003",
        "file_name": "prescription_dec_2025.pdf",
        "document_type": "prescription",
        "valid": False,
        "uploaded_at": "2025-12-12T10:05:00+05:30",
        "doctor_name": "Unknown",
        "summary": "Old prescription; incomplete signature.",
        "file_url": "/api/documents/file/doc-003",
    },
]

RAMESH_EMERGENCY_CONTACTS = [
    {"name": "Sunita Kumar", "relation": "Wife", "phone": "+919876543211"},
    {"name": "Amit Kumar", "relation": "Son", "phone": "+919876543212"},
    {"name": "Emergency Ambulance", "relation": "Emergency", "phone": "108"},
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

RAMESH_NARRATIVE_EVENTS = [
    {
        "date": "2026-01-10",
        "event": "Onboarding completed",
        "impact": "Profile baseline established",
    },
    {
        "date": "2026-01-24",
        "event": "HbA1c reduced",
        "impact": "Glycemic control trend improving",
    },
    {
        "date": "2026-02-08",
        "event": "Blood pressure stabilized",
        "impact": "Reduced hypertension risk trajectory",
    },
    {
        "date": "2026-02-22",
        "event": "Medication adherence streak",
        "impact": "Higher expected Orbit score reliability",
    },
]

RAMESH_REMINDERS = [
    {
        "reminder_id": "rem-001",
        "user_id": DEMO_USER_ID,
        "medication_node_id": "metformin-node-id",
        "reminder_time": "08:00",
        "days_of_week": [1, 2, 3, 4, 5, 6, 7],
        "active": True,
        "adherence_streak": 4,
        "total_taken": 18,
        "total_missed": 2,
        "last_status": "taken",
        "last_reason": None,
    },
    {
        "reminder_id": "rem-002",
        "user_id": DEMO_USER_ID,
        "medication_node_id": "amlodipine-node-id",
        "reminder_time": "21:00",
        "days_of_week": [1, 2, 3, 4, 5, 6, 7],
        "active": True,
        "adherence_streak": 1,
        "total_taken": 14,
        "total_missed": 4,
        "last_status": "missed",
        "last_reason": "Travelled and forgot evening dose",
    },
]

RAMESH_REMINDER_EVENTS = [
    {
        "event_id": "evt-001",
        "reminder_id": "rem-001",
        "status": "taken",
        "reason": None,
        "occurred_at": "2026-02-20T08:15:00+05:30",
    },
    {
        "event_id": "evt-002",
        "reminder_id": "rem-001",
        "status": "taken",
        "reason": None,
        "occurred_at": "2026-02-21T08:05:00+05:30",
    },
    {
        "event_id": "evt-003",
        "reminder_id": "rem-001",
        "status": "taken",
        "reason": None,
        "occurred_at": "2026-02-22T08:01:00+05:30",
    },
    {
        "event_id": "evt-004",
        "reminder_id": "rem-002",
        "status": "missed",
        "reason": "Family event outside home",
        "occurred_at": "2026-02-22T21:45:00+05:30",
    },
]

RAMESH_TEST_SCENARIOS = [
    {
        "case_id": "scenario-hba1c-borderline",
        "title": "Borderline HbA1c Drift",
        "potential_outcome": "Escalate to dietary intervention if HbA1c crosses 7.5% twice.",
        "limit_flag": "warning",
        "threshold": "HbA1c >= 7.5%",
    },
    {
        "case_id": "scenario-egfr-safety",
        "title": "Renal Safety With NSAID Use",
        "potential_outcome": "Flag high-risk metformin + NSAID interaction and prompt nephrology consult.",
        "limit_flag": "critical",
        "threshold": "eGFR < 60 with NSAID usage",
    },
    {
        "case_id": "scenario-adherence-dip",
        "title": "Medication Adherence Dip",
        "potential_outcome": "Reduce adherence score component and reset streak after two misses in 7 days.",
        "limit_flag": "warning",
        "threshold": "missed_doses >= 2 in last 7 days",
    },
    {
        "case_id": "scenario-hypotension-guard",
        "title": "Hypotension Guardrail",
        "potential_outcome": "Recommend physician review if systolic BP trends below 100 with dizziness notes.",
        "limit_flag": "monitor",
        "threshold": "systolic < 100",
    },
]

FATHER_CONDITIONS = [
    {"name": "Coronary Artery Disease", "code": "I25.10", "confidence": 0.86, "node_type": "condition"},
    {"name": "Chronic Kidney Disease Stage 3", "code": "N18.30", "confidence": 0.82, "node_type": "condition"},
    {"name": "Benign Prostatic Hyperplasia", "code": "N40.1", "confidence": 0.75, "node_type": "condition"},
]

FATHER_MEDICATIONS = [
    {"name": "Telmisartan", "dosage": "40mg OD", "frequency": "once daily", "rxnorm": "73494", "confidence": 0.84, "confidence_label": "HIGH", "prescribed_by_doctor": "Dr. S. Banerjee", "node_type": "medication"},
    {"name": "Clopidogrel", "dosage": "75mg OD", "frequency": "once daily", "rxnorm": "32968", "confidence": 0.88, "confidence_label": "HIGH", "prescribed_by_doctor": "Dr. A. Sengupta", "node_type": "medication"},
    {"name": "Rosuvastatin", "dosage": "10mg HS", "frequency": "once daily at bedtime", "rxnorm": "301542", "confidence": 0.81, "confidence_label": "HIGH", "prescribed_by_doctor": "Dr. A. Sengupta", "node_type": "medication"},
    {"name": "Tamsulosin", "dosage": "0.4mg HS", "frequency": "once daily at bedtime", "rxnorm": "77492", "confidence": 0.74, "confidence_label": "MODERATE", "prescribed_by_doctor": "Dr. R. Dutta", "node_type": "medication"},
]

FATHER_LABS = [
    {"name": "LDL Cholesterol", "value": 112, "unit": "mg/dL", "ref_low": None, "ref_high": 100, "loinc": "13457-7", "abnormal": True, "reference_range": "<100 mg/dL", "node_type": "lab_value"},
    {"name": "Creatinine", "value": 1.6, "unit": "mg/dL", "ref_low": 0.7, "ref_high": 1.3, "loinc": "2160-0", "abnormal": True, "reference_range": "0.7-1.3 mg/dL", "node_type": "lab_value"},
    {"name": "eGFR", "value": 44, "unit": "mL/min", "ref_low": 90, "ref_high": None, "loinc": "33914-3", "abnormal": True, "reference_range": ">90 mL/min", "node_type": "lab_value"},
    {"name": "Hemoglobin", "value": 11.2, "unit": "g/dL", "ref_low": 13.5, "ref_high": 17.5, "loinc": "718-7", "abnormal": True, "reference_range": "13.5-17.5 g/dL", "node_type": "lab_value"},
]

FATHER_LAB_HISTORY = [
    {
        "area_key": "cardio_lipids",
        "area_label": "Cardiac Lipids",
        "marker_name": "LDL Cholesterol",
        "unit": "mg/dL",
        "ref_low": None,
        "ref_high": 100,
        "points": [
            {"date": "2025-10-10", "value": 132},
            {"date": "2025-12-10", "value": 124},
            {"date": "2026-01-20", "value": 118},
            {"date": "2026-02-22", "value": 112},
        ],
    },
    {
        "area_key": "renal_function",
        "area_label": "Renal Function",
        "marker_name": "eGFR",
        "unit": "mL/min",
        "ref_low": 90,
        "ref_high": None,
        "points": [
            {"date": "2025-10-10", "value": 50},
            {"date": "2025-12-10", "value": 48},
            {"date": "2026-01-20", "value": 46},
            {"date": "2026-02-22", "value": 44},
        ],
    },
]

FATHER_INTERACTIONS = [
    {
        "drug_pair": "Clopidogrel + Ibuprofen",
        "severity": "ELEVATED",
        "description": "NSAID co-use can increase bleeding risk in patients on antiplatelet therapy.",
        "clinical_action": "Avoid over-the-counter NSAIDs and consult physician for pain management.",
        "acknowledged": False,
    }
]

FATHER_CARE_GAPS = [
    {"name": "Annual Cardiology Review", "status": "open", "description": "Follow-up CAD review is due this quarter."},
]

FATHER_ORBIT_HISTORY = [
    {"total_score": 41.0, "computed_at": "2026-01-11T09:00:00+00:00", "delta": None},
    {"total_score": 46.4, "computed_at": "2026-01-27T11:00:00+00:00", "delta": 5.4},
    {"total_score": 52.1, "computed_at": "2026-02-10T08:45:00+00:00", "delta": 5.7},
]

FATHER_VITALS = [
    {"date": "2026-01-12", "type": "blood_pressure", "systolic": 152, "diastolic": 90, "heart_rate": 72},
    {"date": "2026-01-28", "type": "blood_pressure", "systolic": 146, "diastolic": 86, "heart_rate": 70},
    {"date": "2026-02-22", "type": "blood_pressure", "systolic": 140, "diastolic": 84, "heart_rate": 69},
    {"date": "2026-01-12", "type": "weight", "value": 69.4, "unit": "kg"},
    {"date": "2026-02-22", "type": "weight", "value": 68.7, "unit": "kg"},
]

FATHER_APPOINTMENTS = [
    {
        "appointment_id": "appt-f-001",
        "doctor_name": "Dr. Arindam Sengupta",
        "specialization": "Cardiologist",
        "appointment_datetime": "2026-03-20T10:00:00+05:30",
        "clinic_name": "Heart Care Clinic, Durgapur",
        "status": "upcoming",
        "brief_scheduled": True,
    }
]

FATHER_UPLOADED_DOCUMENTS = [
    {
        "document_id": "doc-f-001",
        "file_name": "cardiology_followup_feb_2026.pdf",
        "document_type": "prescription",
        "valid": True,
        "uploaded_at": "2026-02-18T08:40:00+05:30",
        "doctor_name": "Dr. Arindam Sengupta",
        "summary": "CAD follow-up and lipid management prescription.",
        "file_url": "/api/documents/file/doc-f-001",
    },
    {
        "document_id": "doc-f-002",
        "file_name": "renal_panel_feb_2026.pdf",
        "document_type": "lab_report",
        "valid": True,
        "uploaded_at": "2026-02-22T09:20:00+05:30",
        "doctor_name": "AMRI Diagnostic Lab",
        "summary": "Kidney panel and anemia markers.",
        "file_url": "/api/documents/file/doc-f-002",
        "extracted_markers": [
            {"name": "Creatinine", "value": 1.6, "unit": "mg/dL", "ref_low": 0.7, "ref_high": 1.3},
            {"name": "eGFR", "value": 44, "unit": "mL/min", "ref_low": 90, "ref_high": None},
            {"name": "Hemoglobin", "value": 11.2, "unit": "g/dL", "ref_low": 13.5, "ref_high": 17.5},
        ],
    },
]

FATHER_EMERGENCY_CONTACTS = [
    {"name": "Ramesh Kumar", "relation": "Son", "phone": "+919876543210"},
    {"name": "Sunita Kumar", "relation": "Daughter-in-law", "phone": "+919876543211"},
    {"name": "Emergency Ambulance", "relation": "Emergency", "phone": "108"},
]

FATHER_NARRATIVE = (
    "Harish Chandra Kumar is an 86-year-old male with coronary artery disease and chronic kidney disease stage 3. "
    "He is on Telmisartan, Clopidogrel, Rosuvastatin, and Tamsulosin with improving blood pressure trends. "
    "Recent labs show persistent kidney risk with eGFR of 44 mL/min and Creatinine of 1.6 mg/dL, and mild anemia."
)

FATHER_NARRATIVE_EVENTS = [
    {"date": "2026-01-11", "event": "Family onboarding completed", "impact": "Profile activated under family plan"},
    {"date": "2026-01-27", "event": "Cardiology review done", "impact": "Medication plan stabilized"},
    {"date": "2026-02-22", "event": "Renal panel uploaded", "impact": "CKD risk monitoring tightened"},
]

FATHER_REMINDERS = [
    {
        "reminder_id": "rem-f-001",
        "user_id": FATHER_USER_ID,
        "medication_node_id": "telmisartan-node-id",
        "reminder_time": "08:30",
        "days_of_week": [1, 2, 3, 4, 5, 6, 7],
        "active": True,
        "adherence_streak": 3,
        "total_taken": 15,
        "total_missed": 3,
        "last_status": "taken",
        "last_reason": None,
    },
]

FATHER_REMINDER_EVENTS = [
    {
        "event_id": "evt-f-001",
        "reminder_id": "rem-f-001",
        "status": "taken",
        "reason": None,
        "occurred_at": "2026-02-22T08:33:00+05:30",
    }
]

FAMILY_MEMBER_IDS = [DEMO_USER_ID, FATHER_USER_ID]

FAMILY_CAREGIVER_LINKS = [
    {
        "patient_id": FATHER_USER_ID,
        "caregiver_id": DEMO_USER_ID,
        "caregiver_name": RAMESH_PROFILE["name"],
        "relationship": "son",
        "permission_level": "full",
        "revoked": False,
    },
    {
        "patient_id": DEMO_USER_ID,
        "caregiver_id": FATHER_USER_ID,
        "caregiver_name": FATHER_PROFILE["name"],
        "relationship": "parent",
        "permission_level": "full",
        "revoked": False,
    },
]

_PATIENT_SEED_BUNDLE = {
    DEMO_USER_ID: {
        "profile": RAMESH_PROFILE,
        "conditions": RAMESH_CONDITIONS,
        "medications": RAMESH_MEDICATIONS,
        "labs": RAMESH_LABS,
        "lab_history": RAMESH_LAB_HISTORY,
        "interactions": RAMESH_INTERACTIONS,
        "care_gaps": RAMESH_CARE_GAPS,
        "orbit_history": RAMESH_ORBIT_HISTORY,
        "vitals": RAMESH_VITALS,
        "appointments": RAMESH_APPOINTMENTS,
        "documents": RAMESH_UPLOADED_DOCUMENTS,
        "emergency_contacts": RAMESH_EMERGENCY_CONTACTS,
        "narrative": RAMESH_NARRATIVE,
        "narrative_events": RAMESH_NARRATIVE_EVENTS,
        "reminders": RAMESH_REMINDERS,
        "reminder_events": RAMESH_REMINDER_EVENTS,
    },
    FATHER_USER_ID: {
        "profile": FATHER_PROFILE,
        "conditions": FATHER_CONDITIONS,
        "medications": FATHER_MEDICATIONS,
        "labs": FATHER_LABS,
        "lab_history": FATHER_LAB_HISTORY,
        "interactions": FATHER_INTERACTIONS,
        "care_gaps": FATHER_CARE_GAPS,
        "orbit_history": FATHER_ORBIT_HISTORY,
        "vitals": FATHER_VITALS,
        "appointments": FATHER_APPOINTMENTS,
        "documents": FATHER_UPLOADED_DOCUMENTS,
        "emergency_contacts": FATHER_EMERGENCY_CONTACTS,
        "narrative": FATHER_NARRATIVE,
        "narrative_events": FATHER_NARRATIVE_EVENTS,
        "reminders": FATHER_REMINDERS,
        "reminder_events": FATHER_REMINDER_EVENTS,
    },
}


def get_seed_bundle_for_patient(patient_id: str) -> dict:
    return _PATIENT_SEED_BUNDLE.get(patient_id, {})


def get_seed_list_for_patient(patient_id: str, key: str) -> list:
    value = get_seed_bundle_for_patient(patient_id).get(key)
    return value if isinstance(value, list) else []


def get_seed_value_for_patient(patient_id: str, key: str, default=None):
    value = get_seed_bundle_for_patient(patient_id).get(key)
    return default if value is None else value


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
