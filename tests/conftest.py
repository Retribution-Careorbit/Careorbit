# tests/conftest.py
# V4 FIXES:
#   - datetime.utcnow() → datetime.now(timezone.utc)
#   - Removed deprecated event_loop fixture (asyncio_mode = auto handles it)
#   - phone_number field (not phone) throughout
#   - Unique emails per test run via uuid4
#   - medicine_strip_ocr and lab_report_ocr include 'lines' field
#   - MockDBSession/MockResult extracted to helpers/mocks.py
#   - Added PHASE1_SOURCES constant (restricts ceiling tests)
#   - Added DI wiring note for service mocks
#
# ══════════════════════════════════════════════════════
# SERVICE DEPENDENCY INJECTION — ARCHITECTURE NOTE
# ══════════════════════════════════════════════════════
# Current approach: @patch decorators in each test fixture (brittle but works).
#
# Recommended refactor (Sprint 3): Use FastAPI dependency injection:
#
#   # In routes:
#   def get_openai_service():
#       return AzureOpenAIService()
#
#   # In tests:
#   app.dependency_overrides[get_openai_service] = lambda: mock_openai_fixture
#
# Until refactored, each integration/E2E test must explicitly @patch
# the service import paths used by routes and pipeline modules.
# ══════════════════════════════════════════════════════
#
# AZURE MOCK PATHS (Rule 4 Compliant — Wrapper Level):
#   1. services.azure_vision.AzureVisionService.extract_text / .classify_document_type
#   2. services.azure_openai.AzureOpenAIService.extract_structured_data / .chat / .chat_with_history
#   3. services.azure_translator.AzureTranslatorService.translate / .detect_language
#   4. services.azure_language.AzureLanguageService.recognize_health_entities / .recognize_entities
#   5. services.azure_blob.AzureBlobService.upload_document / .upload_health_summary_pdf
#   6. services.azure_email.AzureEmailService.send_medication_reminder / .send_interaction_alert / .send_upload_result
#   7. services.azure_search.AzureSearchService.search_drug_interactions / .search_guidelines
#   8. Real DB in Docker for integration tests (asyncpg + SQLAlchemy)
#   9. services.azure_keyvault.AzureKeyVaultService.get_secret
#   Exception: Encryption/audit tests patch at async_session level

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import date
from uuid import uuid4
from tests.helpers.mocks import MockDBSession


# ── MOCK DATABASE ────────────────────────────────────

@pytest.fixture
def mock_db():
    return MockDBSession()


# ── MOCK AZURE SERVICES (Rule 4: wrapper-level mocks) ──

@pytest.fixture
def mock_openai():
    service = AsyncMock()
    service.chat = AsyncMock(return_value="Mocked AI response")
    service.chat_with_history = AsyncMock(return_value="Mocked AI response")
    service.extract_structured_data = AsyncMock(return_value={})
    return service


@pytest.fixture
def mock_vision():
    service = AsyncMock()
    service.extract_text = AsyncMock(return_value=MagicMock(
        full_text="Dr. Amit Roy\nMetformin 500mg BD\nAmlodipine 5mg OD",
        lines=["Dr. Amit Roy", "Metformin 500mg BD", "Amlodipine 5mg OD"],
        avg_confidence=0.92, page_count=1
    ))
    service.classify_document_type = AsyncMock(return_value="prescription")
    return service


@pytest.fixture
def mock_blob():
    service = AsyncMock()
    service.upload_document = AsyncMock(
        return_value="https://careorbitstorage.blob.core.windows.net/prescriptions/test.jpg"
    )
    service.upload_health_summary_pdf = AsyncMock(
        return_value="https://careorbitstorage.blob.core.windows.net/summaries/test.pdf"
    )
    return service


@pytest.fixture
def mock_search():
    service = AsyncMock()
    service.search_drug_interactions = AsyncMock(return_value=[{
        "drug_pair": "Metformin + Ibuprofen",
        "severity": "Moderate",
        "description": "NSAIDs may decrease renal function, affecting Metformin clearance",
        "clinical_action": "Monitor renal function closely",
        "severity_modifiers": {
            "renal_impairment": {
                "condition": "creatinine > 1.3 OR eGFR < 60",
                "escalation": "ELEVATED"
            },
            "age_over_65": {"escalation": "+1 severity level"}
        }
    }])
    service.search_guidelines = AsyncMock(return_value=[
        {
            "condition": "Type 2 Diabetes",
            "screening": "Diabetic Retinopathy Screening",
            "frequency": "Annual",
            "source": "ADA Standards of Care 2024",
            "evidence_grade": "A",
            "applicable_codes": ["E11.9"]
        },
        {
            "condition": "Type 2 Diabetes",
            "screening": "Comprehensive Foot Examination",
            "frequency": "Annual",
            "source": "ADA Standards of Care 2024",
            "evidence_grade": "B",
            "applicable_codes": ["E11.9"]
        },
    ])
    return service


@pytest.fixture
def mock_translator():
    service = AsyncMock()
    service.translate = AsyncMock(
        side_effect=lambda text, target, source=None: f"[{target}] {text}"
    )
    service.detect_language = AsyncMock(
        return_value={"language": "hi", "confidence": 0.95}
    )
    return service


@pytest.fixture
def mock_email():
    service = AsyncMock()
    service.send_medication_reminder = AsyncMock(return_value=True)
    service.send_interaction_alert = AsyncMock(return_value=True)
    service.send_upload_result = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_language():
    """Azure AI Language (NER) mock — wrapper level."""
    service = AsyncMock()
    service.recognize_entities = AsyncMock(return_value=[
        {"text": "Metformin", "category": "MedicationName", "confidence": 0.95},
        {"text": "500mg", "category": "Dosage", "confidence": 0.92},
    ])
    service.recognize_health_entities = AsyncMock(return_value=[
        {
            "text": "Metformin",
            "category": "MedicationName",
            "confidence": 0.95,
            "links": [{"data_source": "RxNorm", "id": "6809"}]
        }
    ])
    return service


@pytest.fixture
def mock_keyvault():
    """Azure Key Vault mock — wrapper level."""
    service = AsyncMock()
    service.get_secret = AsyncMock(return_value="test-secret-value-32chars-long!!")
    return service


# ── TEST DATA FACTORIES ──────────────────────────────

@pytest.fixture
def patient_ramesh():
    user_id = str(uuid4())
    return {
        "id": user_id,
        "name": "Ramesh Kumar",
        "email": f"ramesh.{user_id[:8]}@careorbit.dev",
        "phone_number": "+919876543210",
        "dob": date(1958, 3, 15),
        "age": 68, "gender": "male",
        "city": "Durgapur", "state": "West Bengal",
        "language": "hi", "tier": "free",
        "conditions": [
            {"name": "Type 2 Diabetes Mellitus", "code": "E11.9", "confidence": 0.85},
            {"name": "Essential Hypertension", "code": "I10", "confidence": 0.82},
            {"name": "Dyslipidemia", "code": "E78.5", "confidence": 0.78},
        ],
        "medications": [
            {"name": "Metformin", "dosage": "500mg BD", "rxnorm": "6809", "confidence": 0.85},
            {"name": "Amlodipine", "dosage": "5mg OD", "rxnorm": "17767", "confidence": 0.82},
            {"name": "Atorvastatin", "dosage": "10mg HS", "rxnorm": "83367", "confidence": 0.78},
            {"name": "Aspirin", "dosage": "75mg OD", "rxnorm": "1191", "confidence": 0.90},
            {"name": "Ibuprofen", "dosage": "400mg SOS", "rxnorm": "5640", "confidence": 0.65},
        ],
        "labs": [
            {"name": "HbA1c", "value": 7.8, "unit": "%", "ref_high": 5.6,
             "loinc": "4548-4", "abnormal": True},
            {"name": "Creatinine", "value": 1.4, "unit": "mg/dL", "ref_high": 1.3,
             "loinc": "2160-0", "abnormal": True},
            {"name": "eGFR", "value": 52, "unit": "mL/min", "ref_low": 90,
             "loinc": "33914-3", "abnormal": True},
        ],
    }


@pytest.fixture
def patient_priya():
    user_id = str(uuid4())
    return {
        "id": user_id,
        "name": "Priya Sharma",
        "email": f"priya.{user_id[:8]}@careorbit.dev",
        "phone_number": "+919876543211",
        "dob": date(1972, 8, 22),
        "age": 52, "gender": "female",
        "city": "Bangalore", "state": "Karnataka",
        "language": "en", "tier": "premium_individual",
    }


@pytest.fixture
def clear_prescription_ocr():
    return {
        "full_text": (
            "Dr. Amit Roy, MBBS, MD (Medicine)\nReg No: WB/12345\n"
            "Date: 15/01/2026\nRx:\n"
            "1. Tab Metformin 500mg - 1 BD\n"
            "2. Tab Amlodipine 5mg - 1 OD\n"
            "3. Tab Atorvastatin 10mg - 1 HS\n"
            "Dx: Type 2 DM, HTN, Dyslipidemia"
        ),
        "lines": [
            "Dr. Amit Roy, MBBS, MD (Medicine)", "Reg No: WB/12345",
            "Date: 15/01/2026", "Rx:",
            "1. Tab Metformin 500mg - 1 BD",
            "2. Tab Amlodipine 5mg - 1 OD",
            "3. Tab Atorvastatin 10mg - 1 HS",
            "Dx: Type 2 DM, HTN, Dyslipidemia",
        ],
        "avg_confidence": 0.94, "page_count": 1,
    }


@pytest.fixture
def medicine_strip_ocr():
    return {
        "full_text": (
            "GLYCOMET-GP 2\nMetformin Hydrochloride IP 500mg\n"
            "& Glimepiride IP 2mg\nUSV Private Limited\n"
            "Mfg: 06/2025  Exp: 05/2027\nBatch: GG2345"
        ),
        "lines": [
            "GLYCOMET-GP 2", "Metformin Hydrochloride IP 500mg",
            "& Glimepiride IP 2mg", "USV Private Limited",
            "Mfg: 06/2025  Exp: 05/2027", "Batch: GG2345",
        ],
        "avg_confidence": 0.97, "page_count": 1,
    }


@pytest.fixture
def lab_report_ocr():
    return {
        "full_text": (
            "PATHCARE LABS\nReport Date: 20/01/2026\n"
            "Patient: Ramesh Kumar\n"
            "HbA1c: 7.8% (Ref: <5.7%)\n"
            "Creatinine: 1.4 mg/dL (Ref: 0.7-1.3)\n"
            "eGFR: 52 mL/min/1.73m² (Ref: >90)"
        ),
        "lines": [
            "PATHCARE LABS", "Report Date: 20/01/2026",
            "Patient: Ramesh Kumar",
            "HbA1c: 7.8% (Ref: <5.7%)",
            "Creatinine: 1.4 mg/dL (Ref: 0.7-1.3)",
            "eGFR: 52 mL/min/1.73m² (Ref: >90)",
        ],
        "avg_confidence": 0.93, "page_count": 1,
    }


@pytest.fixture
def low_confidence_ocr():
    return {
        "full_text": "B1urr3d t3xt h3r3",
        "lines": ["B1urr3d t3xt h3r3"],
        "avg_confidence": 0.25, "page_count": 1,
    }


# ── PHASE 1 SOURCE CONSTANT ──────────────────────────
# Used to restrict ceiling tests to Phase 1 sources only.
# V3 FIX H5: Prevents Phase 2 sources from contaminating Phase 1 CI.
# V4.1-E FIX: patient_confirmed + patient_corrected moved here from Phase 2.
#   Evidence: confirmations.py (Phase 1) writes:
#     confidence_source="patient_confirmed"  (when confirmed=True)
#     confidence_source="patient_corrected"  (when corrected_name supplied)
#   No SOURCE_CEILING is defined for these — the confirmations route sets
#   confidence_score=0.85 directly (hardcoded). These are not scored by
#   ConfidenceCalculator; they bypass the ceiling mechanism entirely.

PHASE1_SOURCES = [
    "prescription_photo",
    "lab_report_photo",
    "medicine_strip_photo",
    "patient_text_input",
    "patient_confirmed",
    "patient_corrected",
]

# V4-5 FIX: Complete list of valid audit actions from all MVP route handlers
SCHEMA_VALID_ACTIONS = [
    "REGISTER",
    "LOGIN",
    "LOGOUT",
    "VIEW_PROFILE",
    "VIEW_MEDICATIONS",
    "VIEW_LABS",
    "VIEW_SUMMARY",
    "VIEW_OVERVIEW",
    "VIEW_CARE_GAPS",
    "UPDATE_PROFILE",
    "UPLOAD_DOCUMENT",
    "CONFIRM_DATA",
    "GENERATE_SUMMARY",
    "DOWNLOAD_PDF",
    "CHAT_QUERY",
    "ADD_CAREGIVER",
    "REVOKE_CAREGIVER",
    "UPGRADE_SUBSCRIPTION",
    "EXPORT_DATA",
    "DELETE_ACCOUNT",
]


def pytest_configure(config):
    config.addinivalue_line("markers", "phase2: Phase 2 features (not in Phase 1 MVP)")
    config.addinivalue_line("markers", "phase3: Phase 3 features (payment, ML models)")
    config.addinivalue_line("markers", "demo_only: Demo mode only (requires demo routes registered)")
    config.addinivalue_line("markers", "slow: Slow tests (>5s, often algorithm-level or real DB)")
    config.addinivalue_line("markers", "critical: Critical safety tests — must pass before any deployment")
