# CareOrbit — Replit Agent Prompt 2
## Implementation Plan + Full Test Suite Generation for Human Review

---

> **HOW TO USE:** Paste everything between the triple-backtick fences below
> into Replit Agent as a single message. Do not modify it before pasting.

---

```
You are a senior TDD architect building CareOrbit — a healthcare AI platform for
Indian patients. Your ONLY job in this prompt is two things:
  1. Produce a sprint-by-sprint implementation plan
  2. Generate every test file in full, production-quality Python for human review

DO NOT write any application code yet. Do not create routes, services, models,
or any implementation files. Tests only. The human will review and approve
the test files before implementation begins.

════════════════════════════════════════════════════════════════
CONFIRMED STACK — DO NOT DEVIATE FROM THIS
════════════════════════════════════════════════════════════════

Backend:
  Python 3.12 + FastAPI 0.111.0
  SQLAlchemy 2.0.30 async + asyncpg 0.29.0
  pytest 8.2.0 + pytest-asyncio 0.23.0 + httpx 0.27.0

Azure Services (all confirmed — integrate into test mocks exactly):
  1.  azure-ai-documentintelligence==1.0.0   (OCR on prescriptions, labs, strips)
  2.  openai==1.35.0                          (Azure OpenAI GPT-4o structured extraction)
  3.  httpx==0.27.0                           (Azure Translator — no async SDK exists)
  4.  azure-ai-textanalytics==5.3.0           (Healthcare NER → RxNorm / ICD-10 linking)
  5.  azure-storage-blob==12.20.0             (prescription images + PDF summaries)
  6.  azure-communication-email==1.0.0        (reminders, alerts, upload notifications)
  7.  azure-search-documents==11.6.0          (RAG: drug interactions + clinical guidelines)
  8.  asyncpg==0.29.0 + sqlalchemy==2.0.30    (PostgreSQL + pgcrypto for PII encryption)
  9.  azure-keyvault-secrets==4.8.0           (ENCRYPTION_KEY, JWT_SECRET, all API keys)
  10. Azure Static Web Apps                   (frontend deployment — no SDK, not tested)

Frontend (not tested in backend test suite, listed for context):
  React 18 + Vite 5, Turborepo monorepo, Tailwind CSS 3.4

════════════════════════════════════════════════════════════════
ABSOLUTE RULES — EVERY SINGLE TEST FILE MUST FOLLOW ALL OF THESE
════════════════════════════════════════════════════════════════

RULE 1 — ZERO CONDITIONAL GUARDS
  A conditional guard is any test that passes silently when the system under
  test does not execute. These are worse than no test because they give false
  confidence. They are banned unconditionally.

  ❌ BANNED — silent pass if route returns 500:
      if response.status_code == 200:
          assert response.json()["tier"] == "free"

  ❌ BANNED — silent pass if mock was never called:
      if mock_session.execute.called:
          assert "pgp_sym_encrypt" in str(mock_session.execute.call_args)

  ❌ BANNED — always-true fallback:
      assert len(agents_used) >= 1 or len(agents_used) >= 0

  ✅ REQUIRED:
      assert response.status_code == 200
      assert response.json()["tier"] == "free"

  ✅ REQUIRED:
      assert mock_session.execute.call_count >= 2, (
          f"Expected at least 2 DB calls (SELECT + INSERT). "
          f"Actual: {mock_session.execute.call_count}"
      )
      all_calls = " ".join(str(c) for c in mock_session.execute.call_args_list)
      assert "pgp_sym_encrypt" in all_calls.lower()

RULE 2 — ZERO TAUTOLOGICAL MOCK TESTS
  A tautological mock test patches the system under test then asserts the
  mock's own return value. It tests Python's mock library, not your code.

  ❌ BANNED:
      with patch.object(phig_builder, "check_interactions_for_node") as mock:
          mock.return_value = [{"severity": "HIGH"}]
          result = await phig_builder.check_interactions_for_node(...)
          assert result[0]["severity"] == "HIGH"   # asserting the mock itself

  ✅ REQUIRED (Wiring test — patch pipeline, test API response contract):
      with patch("api.routes.patients.phig_builder.check_interactions_for_node",
                 new_callable=AsyncMock, return_value=[{"severity": "HIGH"}]):
          response = client.get("/api/patients/medications")
          assert response.json()["interactions"][0]["severity"] == "HIGH"

  ✅ REQUIRED (Algorithm test — patch only external service, run real logic):
      with patch("graph.phig_builder.search_service.search_drug_interactions",
                 new_callable=AsyncMock, return_value=[{...interaction data...}]):
          result = await phig_builder.check_interactions_for_node(
              patient_id="test", medication_node_id="ibuprofen-id"
          )
          assert len(result) >= 1   # real engine ran, produced real result

RULE 3 — ZERO STUB TESTS
  A test with no assertions is not a test. It is a false promise.

  ❌ BANNED:
      def test_caregiver_limit_exceeded():
          with patch("api.routes.caregivers.feature_gate") as mock:
              pass   # full test needs DB fixture

  ✅ REQUIRED — use xfail with strict=True when feature not yet wired:
      @pytest.mark.xfail(
          strict=True,
          reason="Gate enforcement not wired in caregivers.py yet — remove xfail once done"
      )
      def test_caregiver_limit_exceeded_returns_429():
          from fastapi import HTTPException
          with patch("api.routes.caregivers.enforce_caregiver_limit",
                     side_effect=HTTPException(status_code=429, detail="limit reached")):
              response = client.post("/api/caregivers/add", json={...})
              assert response.status_code == 429

RULE 4 — AZURE MOCK PATHS MUST MATCH THE SERVICE WRAPPER, NOT THE SDK
  Every Azure SDK call in the application is wrapped in a service class
  (e.g. AzureVisionService, AzureOpenAIService). Mock the service method,
  not the underlying SDK client. This way tests survive SDK version upgrades.

  ❌ BANNED:
      patch("azure.ai.documentintelligence.DocumentIntelligenceClient.begin_analyze_document")

  ✅ REQUIRED:
      patch("pipeline.document_pipeline.vision_service.extract_text")
      patch("services.azure_vision.AzureVisionService.extract_text")

  Exception: encryption tests must patch at the SQLAlchemy session level
  because encryption happens inside the DB query, not in a service wrapper:
      patch("api.routes.auth.async_session")

RULE 5 — PHASE MARKERS APPLIED CORRECTLY
  @pytest.mark.phase2   → OTP, voice input, FHIR export, WhatsApp
  @pytest.mark.phase3   → Stripe/Razorpay payment processing
  @pytest.mark.demo_only → upgrade flow only (payment not implemented)
  @pytest.mark.slow     → tests that require real Postgres in Docker
  @pytest.mark.critical → safety-critical clinical tests (run in CI Stage 1)

  Phase 1 CI command: pytest -m "not phase2 and not phase3 and not demo_only"

RULE 6 — UNIQUE STATE PER TEST
  Every test that registers a user must use uuid4-suffixed email:
      email = f"test.{uuid4().hex[:8]}@careorbit.dev"
  Never reuse emails across tests. Never hardcode "test@test.com".

RULE 7 — REMINDER DELETE TEST MUST HARD-ASSERT CREATE FIRST
  The delete test creates a reminder then deletes the real returned ID.
  If create fails, the test must fail immediately — no silent skip.

  ❌ BANNED:
      if create.status_code in (200, 201):
          reminder_id = create.json().get("reminder_id", "rem-001")

  ✅ REQUIRED:
      assert create.status_code in (200, 201), \
          f"Reminder create must succeed before delete can be tested. Got: {create.status_code}"
      reminder_id = create.json()["reminder_id"]   # KeyError is correct failure mode

RULE 8 — INTERACTION TESTS MUST BE SPLIT INTO WIRING vs ALGORITHM
  False positive/negative tests must exist at two distinct layers:
  Layer 1 (Wiring): patch the entire pipeline → test HTTP response contract
  Layer 2 (Algorithm): patch only Azure Search → run real phig_builder logic
  Label each class clearly in its docstring.

════════════════════════════════════════════════════════════════
PART A — SPRINT-BY-SPRINT IMPLEMENTATION PLAN
════════════════════════════════════════════════════════════════

Output a plan with exactly 6 sprints. For each sprint output:
  - Sprint goal
  - Azure services introduced
  - The following table:

  | Step | Order | File | Type | Azure Mock Used | Passes When |
  |------|-------|------|------|-----------------|-------------|

  Step order must always be: WRITE TEST → RUN (RED) → WRITE CODE → RUN (GREEN)
  Never write code before tests. Never skip the RED step.

Sprint 1 — Infrastructure + Auth
  Goal: JWT auth, bcrypt passwords, pgcrypto PII encryption, append-only
        audit trail, rate limiting, refresh token rotation
  Azure introduced: Azure PostgreSQL (pgcrypto), Azure Key Vault

Sprint 2 — Document Pipeline
  Goal: Upload prescription/lab/strip photos, Azure Vision OCR,
        Azure Language Healthcare NER → RxNorm, PHIG node creation,
        Blob Storage for image persistence, document state machine
  Azure introduced: Document Intelligence, Language (NER), Blob Storage

Sprint 3 — Drug Interaction + Care Gap Engine
  Goal: PHIG graph drug interaction detection via Azure Search RAG,
        severity escalation for renal impairment, clinical guideline
        retrieval for care gap detection, patient confirmation flow
  Azure introduced: Azure AI Search (hybrid keyword+vector)

Sprint 4 — AI Chat + Multi-Agent Orchestrator
  Goal: Multi-agent routing (Medication/CareGap/History agents),
        Hindi ↔ English translation via Azure Translator,
        Azure OpenAI GPT-4o structured extraction and chat
  Azure introduced: Azure OpenAI (GPT-4o), Azure Translator

Sprint 5 — Summaries + Reminders + Subscriptions + Tier Gates
  Goal: Health summary PDF generation → Blob Storage, medication reminder
        CRUD with RBAC enforcement, subscription tier gates (free/premium/family),
        email reminders via Azure Communication Services
  Azure introduced: Azure Communication Services (Email)

Sprint 6 — Frontend + E2E Playwright
  Goal: React + Vite dashboard components, Playwright E2E Ramesh journey,
        tier gate UI, interaction alert display, PDF download
  Azure introduced: Azure Static Web Apps (deployment)

════════════════════════════════════════════════════════════════
PART B — GENERATE ALL 31 TEST FILES
════════════════════════════════════════════════════════════════

Generate each file as a complete, runnable Python file in a fenced code block
with the file path as the block label. Every file must be complete — no
ellipsis (...), no "# rest of tests here", no truncation.

─────────────────────────────────────────────────────────────
FILE 01: tests/helpers/mocks.py
─────────────────────────────────────────────────────────────
A shared MockDBSession class used by all unit tests that need a database mock.
Must include:
  class MockDBSession:
    - execute(query, params=None): stores calls in self.calls list
    - assert_query_contains(substring): asserts any stored query contains substring
    - assert_param_value(key, value): asserts any param dict contains key=value
    - first() → None by default, configurable via set_first_result(value)
    - mappings() → MagicMock with first() → None
    - __aenter__ / __aexit__ for async context manager support
    - call_count property
    - call_args_list property (compatible with unittest.mock interface)

─────────────────────────────────────────────────────────────
FILE 02: tests/conftest.py
─────────────────────────────────────────────────────────────
Must include exactly these fixtures and constants:

PHASE1_SOURCES constant (list):
  "prescription_photo", "lab_report_photo", "medicine_strip_photo",
  "patient_text_input",
  "patient_confirmed",   # Phase 1 — confirmations.py sets score=0.85 directly
  "patient_corrected"    # Phase 1 — confirmations.py sets score=0.85 directly

SCHEMA_VALID_ACTIONS constant (list) — all actions logged in audit trail:
  From auth.py:       REGISTER, LOGIN, LOGOUT
  From patients.py:   VIEW_PROFILE, VIEW_MEDICATIONS, VIEW_LABS, VIEW_SUMMARY,
                      VIEW_OVERVIEW, VIEW_CARE_GAPS, UPDATE_PROFILE
  From documents.py:  UPLOAD_DOCUMENT
  From confirmations: CONFIRM_DATA
  From summary.py:    GENERATE_SUMMARY, DOWNLOAD_PDF
  From chat.py:       CHAT_QUERY
  From caregivers.py: ADD_CAREGIVER, REVOKE_CAREGIVER
  From subscriptions: UPGRADE_SUBSCRIPTION
  General:            EXPORT_DATA, DELETE_ACCOUNT

Azure service fixtures (all as AsyncMock with realistic return values):

  mock_vision fixture:
    Wraps AzureVisionService (services/azure_vision.py)
    mock.extract_text returns OCRResult(
        full_text="Dr. Amit Roy\nMetformin 500mg BD\nAmlodipine 5mg OD",
        lines=["Dr. Amit Roy", "Metformin 500mg BD", "Amlodipine 5mg OD"],
        avg_confidence=0.92, page_count=1
    )
    mock.classify_document_type returns "prescription"

  mock_openai fixture:
    Wraps AzureOpenAIService (services/azure_openai.py)
    mock.extract_structured_data returns dict with medications list
    mock.chat returns "Mocked AI response"
    mock.chat_with_history returns "Mocked AI response"

  mock_translator fixture:
    Wraps AzureTranslatorService (services/azure_translator.py)
    mock.translate has side_effect=lambda text, target, source=None: f"[{target}] {text}"
    mock.detect_language returns {"language": "hi", "confidence": 0.95}

  mock_language fixture:
    Wraps AzureLanguageService (services/azure_language.py)
    mock.recognize_health_entities returns list of typed entity dicts with
    "links" containing [{"data_source": "RxNorm", "id": "6809"}] for Metformin

  mock_blob fixture:
    Wraps AzureBlobService (services/azure_blob.py)
    mock.upload_document returns "https://careorbitstorage.blob.core.windows.net/..."
    mock.upload_health_summary_pdf returns valid blob URL

  mock_email fixture:
    Wraps AzureEmailService (services/azure_email.py)
    mock.send_medication_reminder returns True
    mock.send_interaction_alert returns True
    mock.send_upload_result returns True

  mock_search fixture:
    Wraps AzureSearchService (services/azure_search.py)
    mock.search_drug_interactions returns [{
        "drug_pair": "Metformin + Ibuprofen",
        "severity": "Moderate",
        "description": "NSAIDs may decrease renal function affecting Metformin clearance",
        "clinical_action": "Monitor renal function closely",
        "severity_modifiers": {
            "renal_impairment": {
                "condition": "creatinine > 1.3 OR eGFR < 60",
                "escalation": "ELEVATED"
            },
            "age_over_65": {"escalation": "+1 severity level"}
        }
    }]
    mock.search_guidelines returns 2 ADA care gap records for Type 2 Diabetes

  mock_keyvault fixture:
    Wraps AzureKeyVaultService (services/azure_keyvault.py)
    mock.get_secret side_effect maps:
      "ENCRYPTION-KEY" → "test-encryption-key-32-characters!"
      "JWT-SECRET"     → "test-jwt-secret-for-testing-only"
      Any other key    → raises KeyVaultError("Secret not found")

Patient data fixtures:
  patient_ramesh fixture — free tier, age 68, Durgapur WB, language="hi"
    Conditions: Type 2 DM (E11.9), Hypertension (I10), Dyslipidemia (E78.5)
    Medications with RxNorm: Metformin(6809), Amlodipine(17767),
      Atorvastatin(83367), Aspirin(1191), Ibuprofen(5640)
    Labs: HbA1c=7.8%(abnormal), Creatinine=1.4mg/dL(abnormal), eGFR=52(abnormal)
    All emails must be uuid4-suffixed: f"ramesh.{uuid4().hex[:8]}@careorbit.dev"

  patient_priya fixture — premium_individual, age 52, Bangalore KA, language="en"
    Medications: Levothyroxine(10582), Telmisartan(73494)
    Labs: TSH=6.8 mIU/L (abnormal)
    All emails uuid4-suffixed

OCR data fixtures (dict with full_text, lines, avg_confidence, page_count):
  clear_prescription_ocr — Dr. Amit Roy, 3 medications, avg_confidence=0.94
  medicine_strip_ocr — GLYCOMET-GP 2 strip, avg_confidence=0.97
  lab_report_ocr — PATHCARE LABS, HbA1c/Creatinine/eGFR, avg_confidence=0.93
  low_confidence_ocr — illegible text, avg_confidence=0.21

pytest_configure: register markers phase2, phase3, demo_only, slow, critical

─────────────────────────────────────────────────────────────
FILE 03: tests/unit/test_confidence_scoring.py
─────────────────────────────────────────────────────────────
Tests for graph/confidence.py → ConfidenceCalculator class.

class TestSourceCeilingsPhase1:
  test_prescription_photo_ceiling_is_enforced:
    Input: source_type="prescription_photo", all quality signals perfect (1.0)
    Assert: result.final_score <= SOURCE_CEILINGS["prescription_photo"]
    Assert: result.final_score > 0.0

  test_lab_report_photo_ceiling_is_enforced: same pattern for lab_report_photo

  test_medicine_strip_ceiling_is_enforced: same pattern for medicine_strip_photo

  test_patient_text_input_ceiling_is_enforced: same pattern

  test_ceiling_enforced_for_all_phase1_sources:
    Loop over all PHASE1_SOURCES that appear in SOURCE_CEILINGS
    (patient_confirmed and patient_corrected bypass the calculator — skip them)
    Assert each returns <= its ceiling

  test_new_source_in_ceilings_must_be_in_known_sources:
    known_all_sources = set(PHASE1_SOURCES) | {"fhir_api","doctor_portal","patient_voice_input"}
    For each source in ConfidenceCalculator.SOURCE_CEILINGS:
      assert source in known_all_sources

@pytest.mark.phase2
@pytest.mark.skip(reason="Phase 2 source ceilings not yet specified in design doc")
class TestSourceCeilingsPhase2: pass

class TestMedicationConfidence:
  test_perfect_prescription_photo:
    all quality signals at max → score between 0.85-0.95 (ceiling enforcement)
  test_low_ocr_confidence_reduces_score: avg_confidence=0.2 → score < 0.5
  test_missing_date_reduces_score: date_found=False → score lower than date_found=True
  test_drug_match_score_affects_result: drug_match_score=0.3 vs 0.9 → lower vs higher
  test_patient_confirmed_boost:
    patient_confirmed=True → score = 0.85 exactly (hardcoded in confirmations.py)
    This bypasses ConfidenceCalculator entirely — test calls the confirmation
    route logic directly, not ConfidenceCalculator.calculate_medication_confidence
  test_score_never_negative:
    All inputs at zero/False → assert result.final_score >= 0.0
  test_breakdown_factors_are_reproducible:
    Call with identical inputs 10 times
    Assert all 10 final_scores are equal (no randomness)
    Assert all 10 breakdown component counts are equal

class TestLabConfidence:
  test_complete_lab_report_score: all fields present → high confidence
  test_missing_unit_reduces_score: unit_recognized=False → lower score
  test_missing_reference_range_reduces_score

class TestConfidenceRanking:
  test_prescription_photo_ranks_higher_than_patient_text:
    prescription_photo all-good > patient_text_input all-good
  test_medicine_strip_ranks_higher_than_patient_text: same pattern

─────────────────────────────────────────────────────────────
FILE 04: tests/unit/test_drug_database.py
─────────────────────────────────────────────────────────────
Tests for utils/drug_database.py → DrugDatabase class.

class TestRxNormCodes:
  test exact RxNorm lookup for all 10 drugs (one test per drug):
    Metformin    → 6809
    Amlodipine   → 17767
    Atorvastatin → 83367
    Aspirin      → 1191   (generic, not Ecosprin)
    Ibuprofen    → 5640
    Telmisartan  → 73494
    Levothyroxine→ 10582
    Losartan     → 202272  (INGREDIENT-LEVEL code — not the salt form)
    Omeprazole   → 7646
    Paracetamol  → 161

class TestFuzzyMatching:
  test_indian_brand_to_generic: "Thyronorm" → "Levothyroxine" with RxNorm 10582
  test_indian_brand_glycomet: "Glycomet" → "Metformin" with RxNorm 6809
  test_ecosprin_to_aspirin: "Ecosprin" → "Aspirin" with RxNorm 1191
  test_misspelled_metformin: "Metformn" → matches Metformin with confidence > 0.8
  test_partial_name_amlodipine: "Amlo" → matches Amlodipine with confidence > 0.7
  test_unknown_drug_returns_low_confidence: "XYZNOTADRUG123" → confidence < 0.3
  test_dosage_abbreviation_bd: "BD" → "twice daily" or frequency=2
  test_dosage_abbreviation_od: "OD" → "once daily" or frequency=1
  test_dosage_abbreviation_hs: "HS" → "at bedtime"
  test_dosage_abbreviation_sos: "SOS" → "as needed" or frequency="prn"

─────────────────────────────────────────────────────────────
FILE 05: tests/unit/test_encryption.py
─────────────────────────────────────────────────────────────
Tests for utils/encryption.py → encrypt_sql(), get_encryption_params()

class TestEncryptionHelpers:
  test_encrypt_sql_is_pass_through:
    result = encrypt_sql("test_value")
    assert result == "test_value"
    # encrypt_sql() returns the input unchanged — it is a placeholder
    # that signals where pgp_sym_encrypt runs at SQL query level

  test_encrypt_sql_does_not_modify_none:
    assert encrypt_sql(None) is None

  test_get_encryption_params_returns_key:
    params = get_encryption_params()
    assert "encryption_key" in params
    assert len(params["encryption_key"]) >= 16

  test_get_encryption_params_reads_from_settings:
    with patch("utils.encryption.settings") as mock_settings:
        mock_settings.ENCRYPTION_KEY = "test-key-32-chars-exactly!!!!"
        params = get_encryption_params()
        assert params["encryption_key"] == "test-key-32-chars-exactly!!!!"

class TestSQLEncryptionAtQueryLevel:
  test_registration_insert_uses_pgp_sym_encrypt:
    Patch "api.routes.auth.async_session" with MockDBSession
    POST /api/auth/register with valid payload
    assert mock_session.execute.call_count >= 2  ← HARD ASSERT, never if .called
    Collect all calls: all_calls_str = " ".join(str(c) for c in call_args_list)
    assert "pgp_sym_encrypt" in all_calls_str.lower() or \
           "encryption_key" in all_calls_str

  test_registration_params_include_encryption_key:
    Same setup as above
    assert mock_session.execute.call_count >= 2  ← HARD ASSERT
    Search all call args for dict containing "encryption_key" key
    assert found is True, f"encryption_key not in any execute params: {all_params}"

─────────────────────────────────────────────────────────────
FILE 06: tests/unit/test_auth_tokens.py
─────────────────────────────────────────────────────────────
Tests for api/middleware/auth.py — JWT and bcrypt functions.
No HTTP calls. Pure function tests.

class TestJWTTokens:
  test_access_token_contains_user_id
  test_access_token_type_is_access
  test_access_token_expires_in_15_minutes:
    exp - iat == 900 seconds (15 * 60)
  test_refresh_token_expires_in_7_days:
    exp - iat == 604800 seconds (7 * 24 * 60 * 60)
  test_token_subject_is_string_user_id
  test_different_users_produce_different_tokens
  test_tampered_token_raises_exception:
    Modify payload bytes → decode raises JWTError or similar
  test_expired_token_raises_exception:
    Create token with exp = now() - 1 second → verify raises

class TestPasswordHashing:
  test_hash_starts_with_bcrypt_prefix:
    assert hashed.startswith("$2b$")
  test_verify_correct_password_returns_true
  test_verify_wrong_password_returns_false
  test_hash_is_different_each_call_same_password:
    bcrypt uses random salt — two calls produce different hashes
  test_hash_is_not_reversible:
    assert hash != original_password

class TestRefreshTokenCreation:
  test_create_refresh_token_returns_string
  test_create_refresh_token_is_url_safe:
    No characters that break URL or JSON encoding
  test_two_refresh_tokens_are_different

─────────────────────────────────────────────────────────────
FILE 07: tests/functional/test_api_auth.py
─────────────────────────────────────────────────────────────
Tests for POST /api/auth/register, /login, /refresh, /logout
Uses FastAPI TestClient with async_session patched.

class TestRegistration:
  test_register_success_returns_tokens_immediately:
    POST /api/auth/register → 200 or 201
    response has "access_token" key
    response has "refresh_token" key
    NO OTP step in Phase 1 — tokens returned immediately on registration
    Assert status first unconditionally before inspecting body

  test_register_duplicate_email_returns_409:
    Register same email twice → second returns 409

  test_register_weak_password_returns_422:
    password="abc" → 422 (validation error)

  test_register_missing_name_returns_422
  test_register_missing_phone_returns_422
  test_register_invalid_email_format_returns_422

class TestLogin:
  test_login_success_returns_tokens:
    Register user first, then login → 200, access_token + refresh_token in body

  test_login_wrong_password_returns_401
  test_login_nonexistent_email_returns_401
  test_login_inactive_account_returns_403:
    @pytest.mark.xfail(strict=True, reason="is_active flag not yet checked in login route")

class TestRefreshAndLogout:
  test_refresh_uses_json_body_not_cookie:
    POST /api/auth/refresh with json={"refresh_token": token} → 200
    Never: cookies={"refresh_token": token}

  test_refresh_returns_new_access_token
  test_refresh_with_invalid_token_returns_401
  test_refresh_rotates_token:
    Old refresh_token rejected after rotation → 401

  test_logout_uses_json_body_not_cookie:
    POST /api/auth/logout with json={"refresh_token": token} → 200

  test_logout_revokes_token:
    Logout, then try to use same refresh_token → 401

@pytest.mark.phase2
class TestOTPVerification:
  (All OTP tests here — none in Phase 1 CI)

─────────────────────────────────────────────────────────────
FILE 08: tests/functional/test_api_documents.py
─────────────────────────────────────────────────────────────
Tests for POST /api/documents/upload

Helpers needed:
  _auth(tier="free") → patch get_current_user returning {id, tier, language}
  _services() → patch vision_service, language_service, blob_service, openai_service

class TestDocumentUpload:
  test_upload_prescription_returns_nodes_created:
    With _auth() and _services() mocked:
    POST /api/documents/upload with prescription JPEG (5KB fixture bytes)
    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes_created"]) >= 2
    assert data["processing_status"] == "success"

  test_upload_produces_terminal_status:
    processing_status in ("success", "needs_confirmation", "failed")
    "processing" must NEVER be returned as final status

  test_upload_needs_confirmation_for_low_confidence:
    Mock vision returning avg_confidence=0.25
    assert data["processing_status"] == "needs_confirmation"
    assert len(data["confirmation_needed"]) >= 1

  test_upload_detects_drug_interaction:
    Mock that patient already has Metformin node
    Upload Ibuprofen prescription
    assert len(data["interactions_detected"]) >= 1
    assert data["interactions_detected"][0]["severity"] is not None
    No conditional — assert unconditionally

  test_upload_requires_auth:
    POST without auth header → 401 or 403

  test_upload_sends_result_email:
    mock_email.send_upload_result.assert_called_once()
    assert mock_email.send_upload_result.call_count == 1
    Never: if mock_email.called: ...

─────────────────────────────────────────────────────────────
FILE 09: tests/functional/test_api_documents_boundaries.py
─────────────────────────────────────────────────────────────
Tests for file validation at the upload endpoint boundary.

class TestUploadFileBoundaries:
  test_file_over_10mb_returns_400:
    Generate bytes of length 10 * 1024 * 1024 + 1
    POST → assert status_code == 400
    assert "size" in response.json()["detail"].lower()

  test_zero_byte_file_returns_400:
    POST with empty bytes → 400

  test_pdf_mime_type_rejected:
    POST with content_type="application/pdf" → 400
    assert "format" in response.json()["detail"].lower() or \
           "type" in response.json()["detail"].lower()

  test_text_file_rejected:
    POST with content_type="text/plain" → 400

  test_jpeg_accepted:
    POST with content_type="image/jpeg", valid small fixture → 200 or 202

  test_png_accepted:
    POST with content_type="image/png" → 200 or 202

  test_missing_file_field_returns_422:
    POST with no file field → 422 (FastAPI validation)

─────────────────────────────────────────────────────────────
FILE 10: tests/functional/test_api_confirmations.py
─────────────────────────────────────────────────────────────
Tests for POST /api/confirmations/confirm

class TestPatientConfirmation:
  test_confirm_existing_node_sets_score_085:
    Mock phig_builder._get_node returning a valid node
    Mock phig_builder._update_node_confidence
    POST /api/confirmations/confirm with {node_id, confirmed: true}
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"
    assert data["new_confidence"] == 0.85

  test_confirm_nonexistent_node_returns_200_with_error:
    Mock phig_builder._get_node returning None
    POST with nonexistent node_id
    assert response.status_code == 200   ← NOT 404 — route uses return not raise
    assert "error" in response.json()
    assert response.json()["error"] == "Node not found"
    # TODO: Route should raise HTTPException(404) — fix in route, then update test

  test_correction_updates_medication_name:
    confirmed=False, corrected_name="Metformin 500mg"
    Mock drug_db.fuzzy_match returning match with confidence > 0.8
    assert data["status"] == "corrected"

  test_confirmation_requires_edit_permission:
    Caregiver with permission_level="view" → 403

─────────────────────────────────────────────────────────────
FILE 11: tests/functional/test_api_caregivers.py
─────────────────────────────────────────────────────────────
Tests for POST /api/caregivers/add, DELETE /api/caregivers/{user_id}, GET /api/caregivers/

class TestCaregiverAdd:
  test_add_caregiver_success_returns_correct_fields:
    Response must contain: status, caregiver_name, permission_level
    Response must NOT contain: link_id (not in route response)
    assert "link_id" not in data   ← V4-1 fix

  test_add_caregiver_invalid_relationship_returns_400:
    relationship="admin" or relationship="neighbor" → 400

  test_add_caregiver_invalid_permission_returns_400:
    permission_level="superuser" → 400

  test_add_caregiver_unregistered_email_returns_404:
    caregiver_email not in users table → 404

  test_add_requires_auth: no auth header → 401 or 403

  @pytest.mark.xfail(strict=True, reason=(
      "enforce_caregiver_limit not yet wired in caregivers.py. "
      "Remove xfail once feature gate is called before INSERT."
  ))
  test_caregiver_limit_exceeded_returns_429:
    from fastapi import HTTPException
    with patch("api.routes.caregivers.enforce_caregiver_limit",
               side_effect=HTTPException(status_code=429, detail={
                   "error": "Caregiver limit reached", "limit": 2, "tier": "free"
               })):
        response = client.post("/api/caregivers/add", json={valid caregiver data})
        assert response.status_code == 429
        assert "limit" in str(response.json())

class TestCaregiverDelete:
  test_delete_caregiver_is_idempotent:
    DELETE /api/caregivers/{some_user_id} → always 200
    DELETE same ID again → still 200  ← V4-2 fix (no 404 on already-deleted)
    assert response.json()["status"] == "revoked"

  test_delete_requires_auth

class TestCaregiverViews:
  test_list_caregivers_returns_array
  test_caregiver_with_view_permission_cannot_add_new_caregiver: → 403

─────────────────────────────────────────────────────────────
FILE 12: tests/functional/test_api_summary.py
─────────────────────────────────────────────────────────────
Tests for GET /api/summary/generate (NOT POST)

class TestSummaryGeneration:
  test_summary_returns_pdf_when_nodes_exist:
    Mock phig_builder query returning 3 nodes (total_nodes=3)
    GET /api/summary/generate?patient_id=...
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"   ← magic bytes check
    assert "content-disposition" in response.headers

  test_summary_empty_patient_returns_200_with_json_error:
    Mock total_nodes == 0
    GET /api/summary/generate?patient_id=...
    assert response.status_code == 200   ← NOT 404, NOT 204
    data = response.json()
    assert "error" in data
    assert "no" in data["error"].lower() or "health data" in data["error"].lower()
    # Route uses return {"error": "..."} not raise HTTPException
    # Unconditional assertion — no if/else guard

  test_summary_requires_auth
  test_summary_caregiver_view_can_access:
    Caregiver with permission_level="view" → 200 + PDF

─────────────────────────────────────────────────────────────
FILE 13: tests/functional/test_api_reminders.py
─────────────────────────────────────────────────────────────
Tests for POST /api/reminders/create, GET /api/reminders/list,
DELETE /api/reminders/{reminder_id}

class TestReminderCreate:
  test_create_reminder_returns_reminder_id:
    POST /api/reminders/create?patient_id=... with:
      {"medication_node_id": "...", "reminder_time": "09:00", "days_of_week": [1,2,3,4,5]}
    assert response.status_code in (200, 201)
    assert "reminder_id" in response.json()

  test_create_reminder_default_days_all_week:
    POST without days_of_week field
    assert response.json()["days_of_week"] == [0,1,2,3,4,5,6] or [1,2,3,4,5,6,7]
    (accept either 0-indexed or 1-indexed depending on implementation)

  test_create_reminder_days_must_be_integers:
    days_of_week=["Monday", "Tuesday"] → 422

  test_create_reminder_requires_edit_permission:
    Caregiver with permission_level="view" → 403 on POST /create

  test_create_requires_auth

class TestReminderList:
  test_list_reminders_returns_array:
    GET /api/reminders/list?patient_id=... → 200
    assert isinstance(response.json(), list)

  test_list_requires_auth

class TestReminderDelete:
  test_delete_existing_reminder:
    # RULE 7 APPLIED — hard assert create first, use real reminder_id
    create = client.post("/api/reminders/create", params={"patient_id": ...}, json={...})
    assert create.status_code in (200, 201), \
        f"Reminder create must succeed. Got: {create.status_code} — {create.text}"
    reminder_id = create.json()["reminder_id"]   # KeyError here = correct failure
    delete = client.delete(f"/api/reminders/{reminder_id}")
    assert delete.status_code in (200, 204)

  test_delete_nonexistent_reminder_returns_404:
    DELETE /api/reminders/{uuid4()} → 404

  test_delete_requires_auth

class TestReminderEmailIntegration:
  test_scheduler_triggers_email_service:
    Mock email_service.send_medication_reminder
    Trigger the reminder scheduler with a due reminder
    assert email_service.send_medication_reminder.call_count == 1
    call_args = email_service.send_medication_reminder.call_args[1]
    assert "medication_name" in call_args
    assert "patient_name" in call_args

─────────────────────────────────────────────────────────────
FILE 14: tests/functional/test_api_subscriptions.py
─────────────────────────────────────────────────────────────
NOTE: subscriptions.router IS registered in main.py v0.3.0
DO NOT use include_router hack inside fixture.
DO NOT mark /current or /plans tests as demo_only.
Standard TestClient(app) is sufficient.

class TestSubscriptionCurrent:
  test_free_user_shows_ads_true:
    Mock get_current_user returning tier="free"
    GET /api/subscriptions/current → 200
    assert response.json()["features"]["shows_ads"] is True

  test_free_user_tier_is_free:
    assert response.json()["tier"] == "free"

  test_subscription_requires_auth:
    No auth header → 401 or 403

class TestSubscriptionPlans:
  test_get_plans_returns_three_tiers:
    GET /api/subscriptions/plans → 200
    tiers = [p["tier"] for p in response.json()["plans"]]
    assert "free" in tiers
    assert "premium_individual" in tiers
    assert "premium_family" in tiers

  test_free_plan_price_zero:
    free_plan["price_monthly_cents"] == 0

  test_premium_individual_price_799:
    # Business model: $7.99/month
    premium_individual["price_monthly_cents"] == 799

  test_family_plan_price_1999:
    # Business model: $19.99/month
    premium_family["price_monthly_cents"] == 1999

@pytest.mark.demo_only
class TestTierUpgradeJourney:
  # Payment is Phase 3 — upgrade flow is demo mode only
  # Uses standard client (no include_router hack)
  test_upgrade_to_premium_disables_ads
  test_upgrade_to_premium_removes_document_limit

─────────────────────────────────────────────────────────────
FILE 15: tests/functional/test_api_health.py
─────────────────────────────────────────────────────────────

class TestHealthEndpoint:
  test_health_returns_200:
    GET /health → 200

  test_health_returns_correct_fields:
    assert data["status"] == "healthy"
    assert data["service"] == "careorbit-api"
    assert "version" in data

  test_health_requires_no_auth:
    GET /health without any Authorization header → 200
    (health endpoint must be publicly accessible for load balancer checks)

─────────────────────────────────────────────────────────────
FILE 16: tests/integration/test_document_state_machine.py
─────────────────────────────────────────────────────────────
Tests for pipeline/document_pipeline.py → process_document() function.
Patches vision_service, language_service, openai_service at the pipeline level.

class TestDocumentStateMachine:
  test_successful_prescription_returns_terminal_success:
    Mock vision returning high-confidence OCR
    Mock language returning Metformin entity with RxNorm 6809
    result = await process_document(image_bytes, patient_id, "prescription")
    assert result["processing_status"] == "success"
    assert result["processing_status"] != "processing"   ← explicit
    assert len(result["nodes_created"]) >= 1

  test_vision_timeout_returns_terminal_failed:
    Mock vision raising asyncio.TimeoutError
    result = await process_document(...)
    assert result["processing_status"] == "failed"
    assert result["error_message"] is not None
    assert len(result["error_message"]) > 0

  test_low_ocr_confidence_returns_needs_confirmation:
    Mock vision returning avg_confidence=0.20
    assert result["processing_status"] == "needs_confirmation"
    assert len(result["confirmation_needed"]) >= 1

  test_unreadable_document_returns_failed:
    Mock vision returning avg_confidence=0.10
    assert result["processing_status"] == "failed"

  test_upload_produces_terminal_status:
    # V4-9: "processing" is an unobservable intermediate state
    # The final status returned to the caller must always be terminal
    TERMINAL_STATUSES = {"success", "needs_confirmation", "failed"}
    assert result["processing_status"] in TERMINAL_STATUSES

  test_blob_upload_called_on_success:
    Mock blob_service.upload_document
    assert blob_service.upload_document.call_count == 1   ← hard assert

  test_medicine_strip_extracts_expiry_date:
    Mock vision returning medicine strip OCR
    result = await process_document(..., doc_type="medicine_strip")
    assert result["processing_status"] in ("success", "needs_confirmation")

─────────────────────────────────────────────────────────────
FILE 17: tests/integration/test_orchestrator.py
─────────────────────────────────────────────────────────────
Tests for agents/orchestrator.py

class TestOrchestrator:
  test_medication_keyword_routes_to_medication_agent:
    query = "what medications am I taking?"
    result = await orchestrator.run(query, patient_id, language="en")
    assert "medication" in str(result["agents_used"]).lower() or \
           "MedicationAgent" in result["agents_used"]
    # Strict check — no "or len >= 1" fallback

  test_care_gap_keyword_routes_to_care_gap_agent:
    query = "do I need any screenings?"
    assert "CareGapAgent" in result["agents_used"] or \
           "care_gap" in str(result["agents_used"]).lower()

  test_history_keyword_routes_to_history_agent:
    query = "show my past diagnoses"
    assert "HistoryAgent" in result["agents_used"] or \
           "history" in str(result["agents_used"]).lower()

  test_no_keyword_uses_all_three_agents:
    query = "hello"
    assert len(result["agents_used"]) == 3

  test_hindi_query_triggers_translation:
    Mock translator_service.translate
    query = "मेरी दवाइयां क्या हैं"
    await orchestrator.run(query, patient_id, language="hi")
    assert translator_service.translate.call_count >= 1   ← hard assert

  test_response_has_required_fields:
    result must have keys: message, agents_used, alerts, confidence
    assert "message" in result
    assert "agents_used" in result
    assert isinstance(result["agents_used"], list)
    assert len(result["agents_used"]) >= 1   ← strict minimum

─────────────────────────────────────────────────────────────
FILE 18: tests/security/test_rate_limiting.py
─────────────────────────────────────────────────────────────
Falsifiable design — real user attempts real logins.

class TestAuthRateLimiting:
  test_sixth_failed_login_returns_429:
    Register a real user with unique email
    Attempt login with wrong password 5 times → each returns 401
    6th attempt with wrong password → assert 429
    # Falsifiable: if rate limiter broke, this returns 401 (not 429) → test fails

  test_correct_password_after_lockout_returns_429:
    After 5 wrong attempts, correct password on 6th → still 429
    # Rate limit applies to the attempt count, not just wrong passwords

  test_different_ip_not_rate_limited:
    @pytest.mark.xfail(strict=True, reason="IP-based rate limiting not yet implemented")
    5 wrong attempts from IP-A, attempt from IP-B → should not be rate limited

─────────────────────────────────────────────────────────────
FILE 19: tests/security/test_refresh_token_security.py
─────────────────────────────────────────────────────────────

class TestRefreshTokenSecurity:
  test_refresh_token_stored_as_sha256_hash:
    Patch async_session with MockDBSession
    POST /api/auth/login
    assert mock_session.execute.call_count >= 2   ← hard assert
    Find the INSERT call (usually call index 1 or 2)
    Verify params dict contains token_hash key
    Verify token_hash length == 64 (SHA-256 hex string)
    assert len(stored_hash) == 64

  test_raw_token_not_stored:
    Same setup — verify no call stores the raw token value

  test_revoked_token_rejected:
    Login, logout (revoke token), attempt refresh → 401

  test_token_rotation_invalidates_old_token:
    Login → refresh → try using old refresh token → 401

  test_forged_token_rejected:
    POST /api/auth/refresh with json={"refresh_token": "totally-fake-token"} → 401

─────────────────────────────────────────────────────────────
FILE 20: tests/security/test_audit_trail.py
─────────────────────────────────────────────────────────────

class TestAuditStructure:
  test_login_creates_audit_record:
    Patch the audit log function (api.middleware.audit.log_audit)
    POST /api/auth/login
    assert log_audit.call_count >= 1   ← hard assert
    call_kwargs = log_audit.call_args[1]  # keyword args, NOT str(call_args)
    assert "user_id" in call_kwargs
    assert "action" in call_kwargs
    assert call_kwargs["action"] == "LOGIN"

  test_audit_record_contains_ip_address:
    call_kwargs must have "request" key OR "ip_address" key
    assert call_kwargs.get("request") is not None or \
           call_kwargs.get("ip_address") is not None

  test_audit_record_contains_patient_id:
    For patient data access endpoint, call_kwargs must have patient_id

class TestValidAuditActions:
  SCHEMA_VALID_ACTIONS = [all 20 actions listed in conftest above]

  test_valid_actions_has_no_duplicates
  test_valid_actions_minimum_count: assert len >= 15
  test_register_action_is_included:
    assert "REGISTER" in SCHEMA_VALID_ACTIONS
    # V4-5: REGISTER was incorrectly removed — auth.py logs it
  test_view_overview_is_included: assert "VIEW_OVERVIEW" in SCHEMA_VALID_ACTIONS
  test_upgrade_subscription_is_included: assert "UPGRADE_SUBSCRIPTION" in SCHEMA_VALID_ACTIONS

─────────────────────────────────────────────────────────────
FILE 21: tests/security/test_audit_append_only.py
─────────────────────────────────────────────────────────────
DB-level append-only constraint for HIPAA compliance.

class TestAuditAppendOnly:
  test_application_user_cannot_update_audit_log:
    @pytest.mark.slow  (requires real Postgres connection)
    Connect to test DB as application user
    INSERT a test audit record
    Try UPDATE on that record → assert raises OperationalError or InsufficientPrivilege

  test_application_user_cannot_delete_audit_log:
    @pytest.mark.slow
    INSERT audit record, attempt DELETE → assert raises

  test_audit_log_has_no_updated_at_column:
    Inspect audit_log table schema
    column_names = get column names from information_schema
    assert "updated_at" not in column_names

  test_insert_audit_record_succeeds:
    INSERT works (application user can still write)
    Verify record exists after insert

─────────────────────────────────────────────────────────────
FILE 22: tests/security/test_rbac_enforcement.py
─────────────────────────────────────────────────────────────

class TestRBACEnforcement:
  test_unauthenticated_request_rejected:
    GET /api/patients/overview with no Authorization header → 401 or 403

  test_invalid_token_rejected:
    Authorization: Bearer invalid-token → 401 or 403

  test_expired_token_rejected:
    Create token with exp in past → 401

  test_valid_token_accepted:
    Register, login, use access_token → 200

  test_patient_can_access_own_data:
    Patient A token → Patient A overview → 200

─────────────────────────────────────────────────────────────
FILE 23: tests/security/test_rbac_permission_levels.py
─────────────────────────────────────────────────────────────

class TestRBACPermissionBoundaries:
  test_caregiver_view_permission_cannot_upload:
    Caregiver with permission="view" → POST /api/documents/upload → 403

  test_caregiver_view_permission_cannot_create_reminder:
    Caregiver with permission="view" → POST /api/reminders/create → 403

  test_caregiver_view_permission_can_read_medications:
    Caregiver with permission="view" → GET /api/patients/medications → 200

  test_caregiver_edit_permission_can_upload:
    Caregiver with permission="edit" → POST /api/documents/upload → not 403

  test_caregiver_edit_permission_can_create_reminder:
    Caregiver with permission="edit" → POST /api/reminders/create → not 403

─────────────────────────────────────────────────────────────
FILE 24: tests/security/test_cross_patient_rbac.py
─────────────────────────────────────────────────────────────
HIPAA-critical: Patient A must never access Patient B's data.

class TestCrossPatientIsolation:
  Setup: Register Patient A and Patient B with separate unique emails and tokens

  test_patient_a_cannot_access_patient_b_medications:
    GET /api/patients/medications?patient_id=PATIENT_B_ID
    with headers containing PATIENT_A's token
    assert response.status_code == 403

  test_patient_a_cannot_access_patient_b_overview:
    GET /api/patients/overview?patient_id=PATIENT_B_ID with A's token → 403

  test_patient_a_cannot_generate_patient_b_summary:
    GET /api/summary/generate?patient_id=PATIENT_B_ID with A's token → 403

  test_patient_a_cannot_upload_to_patient_b:
    POST /api/documents/upload?patient_id=PATIENT_B_ID with A's token → 403

  test_patient_a_cannot_view_patient_b_caregivers:
    GET /api/caregivers/?patient_id=PATIENT_B_ID with A's token → 403

  test_patient_a_can_access_own_data:
    GET /api/patients/overview?patient_id=PATIENT_A_ID with A's token → 200
    # Verify non-cross access still works

─────────────────────────────────────────────────────────────
FILE 25: tests/security/test_password_change_revocation.py
─────────────────────────────────────────────────────────────

class TestPasswordChangeRevocation:
  test_password_change_revokes_all_refresh_tokens:
    Register user, login from 2 "devices" (2 refresh tokens)
    POST /api/auth/change-password with new password
    Try using old refresh_token_1 → 401
    Try using old refresh_token_2 → 401

  test_password_change_allows_new_login:
    After change, login with new password → 200

  test_old_password_rejected_after_change:
    After change, login with old password → 401

─────────────────────────────────────────────────────────────
FILE 26: tests/business_logic/test_tier_config.py
─────────────────────────────────────────────────────────────
Tests for api/middleware/feature_gate.py → TIER_LIMITS, check_feature_allowed()

class TestTierLimitsConfiguration:
  test_all_three_tiers_defined:
    assert "free" in TIER_LIMITS
    assert "premium_individual" in TIER_LIMITS
    assert "premium_family" in TIER_LIMITS

  test_free_tier_shows_ads:
    assert TIER_LIMITS["free"]["shows_ads"] is True

  test_premium_individual_no_ads:
    assert TIER_LIMITS["premium_individual"]["shows_ads"] is False

  test_premium_family_no_ads:
    assert TIER_LIMITS["premium_family"]["shows_ads"] is False

  test_free_tier_document_limit_is_100:
    assert TIER_LIMITS["free"]["docs_per_month"] == 100

  test_free_tier_summary_limit_is_5:
    assert TIER_LIMITS["free"]["summaries_per_month"] == 5

  test_premium_individual_no_document_limit:
    assert TIER_LIMITS["premium_individual"]["docs_per_month"] is None

  test_free_tier_caregiver_limit_is_2:
    assert TIER_LIMITS["free"]["max_caregivers"] == 2

  test_family_tier_max_members_is_3:
    assert TIER_LIMITS["premium_family"]["max_family_members"] == 3

  test_free_data_retention_is_24_months:
    assert TIER_LIMITS["free"]["data_retention_months"] == 24

  test_premium_data_retention_is_lifetime:
    assert TIER_LIMITS["premium_individual"]["data_retention_months"] is None

  test_family_dashboard_only_for_family_tier:
    assert TIER_LIMITS["premium_family"]["family_dashboard"] is True
    assert TIER_LIMITS["free"]["family_dashboard"] is False
    assert TIER_LIMITS["premium_individual"]["family_dashboard"] is False

class TestFeatureGateLogic:
  test_check_usage_at_limit_returns_not_allowed:
    simulate current_count == limit → allowed is False

  test_check_usage_below_limit_returns_allowed:
    current_count < limit → allowed is True

  test_check_usage_above_limit_returns_not_allowed:
    current_count > limit → allowed is False

  test_none_limit_always_returns_allowed:
    premium user, docs_per_month=None → always allowed regardless of count

  test_get_tier_limits_unknown_tier_defaults_to_free:
    get_tier_limits("enterprise_ultra") → returns free tier config

─────────────────────────────────────────────────────────────
FILE 27: tests/false_positive_negative/test_interaction_false_positives.py
─────────────────────────────────────────────────────────────
SPLIT ARCHITECTURE — RULE 8 APPLIED:
  Class 1: Wiring tests (mock pipeline → test API HTTP contract)
  Class 2: Algorithm tests (mock only Azure Search → run real engine)

class TestInteractionWiringFP:
  """
  WIRING TESTS: Verify API surfaces empty interaction list correctly.
  These test HTTP response contract, NOT clinical detection accuracy.
  It is correct to mock the full pipeline here.
  """
  test_api_returns_empty_alerts_when_pipeline_finds_none:
    Patch "api.routes.patients.phig_builder.check_interactions_for_node"
    returning []
    GET /api/patients/medications
    assert response.json()["interactions"] == []
    assert response.status_code == 200

class TestInteractionDetectionFP:
  """
  ALGORITHM TESTS: Patch ONLY Azure Search service.
  Real phig_builder detection logic runs.
  Tests whether the engine correctly produces zero alerts for safe combinations.
  """
  @pytest.mark.slow
  test_metformin_atorvastatin_no_interaction:
    Patch "services.azure_search.AzureSearchService.search_drug_interactions"
    returning []  (no interaction data from RAG)
    result = await phig_builder.check_interactions_for_node(
        patient_id="test", medication_node_id="atorvastatin-id"
    )
    assert len(result) == 0, \
        f"Metformin + Atorvastatin: safe combination, must produce 0 alerts. Got: {result}"

  @pytest.mark.slow
  test_amlodipine_atorvastatin_no_interaction:
    Same pattern with search returning []
    assert len(result) == 0

─────────────────────────────────────────────────────────────
FILE 28: tests/false_positive_negative/test_interaction_false_negatives.py
─────────────────────────────────────────────────────────────

class TestInteractionWiringFN:
  """
  WIRING TESTS: Verify API surfaces interaction alerts when pipeline finds them.
  """
  test_api_surfaces_interaction_from_pipeline:
    Patch check_interactions_for_node returning [{severity: "HIGH"}]
    GET /api/patients/medications
    assert len(response.json()["interactions"]) >= 1
    assert response.json()["interactions"][0]["severity"] == "HIGH"

@pytest.mark.critical
class TestInteractionDetectionFN:
  """
  ALGORITHM TESTS — CLINICAL SAFETY CRITICAL.
  Patch ONLY Azure Search. Real engine runs.
  Failure here = known dangerous drug interaction being silently missed.
  These run in CI Stage 1 and block all subsequent stages on failure.
  """
  @pytest.mark.slow
  test_metformin_ibuprofen_interaction_detected:
    Patch search returning Metformin+Ibuprofen interaction data
    result = await phig_builder.check_interactions_for_node(...)
    assert len(result) >= 1, (
        "SAFETY FAILURE: Metformin + Ibuprofen interaction not detected. "
        "NSAIDs reduce Metformin clearance — clinically significant."
    )

  @pytest.mark.slow
  test_severity_escalation_for_renal_impairment:
    Ramesh's context: creatinine=1.4 (>1.3), eGFR=52 (<60)
    Patch search returning interaction with severity_modifiers.renal_impairment
    Patch phig_builder._get_patient_labs returning Ramesh's abnormal lab values
    result = await phig_builder.check_interactions_for_node(...)
    assert result[0]["severity"] in ("HIGH", "ELEVATED", "CRITICAL"), (
        "SAFETY FAILURE: Severity must escalate for renal-impaired patient. "
        f"Ramesh has creatinine=1.4, eGFR=52. Got: {result[0].get('severity')}"
    )

─────────────────────────────────────────────────────────────
FILE 29: tests/regression/test_lab_trend_edge_cases.py
─────────────────────────────────────────────────────────────
Regression tests for lab value trend logic.
All marked xfail until labs.py is implemented in Sprint 1 (promoted to P0 in v0.3.0).

@pytest.mark.xfail(strict=False, reason="labs.py not yet implemented")
class TestLabTrendEdgeCases:
  test_single_lab_value_shows_no_trend:
    Only 1 data point → trend should be None or "insufficient_data"

  test_two_identical_values_shows_stable_trend:
    Two identical readings → trend == "stable"

  test_consistently_rising_values_show_upward_trend:
    [5.0, 5.5, 6.0, 6.5, 7.8] → trend in ("rising", "upward", "worsening")

  test_single_outlier_does_not_flip_trend:
    [7.0, 7.1, 7.2, 2.0, 7.3] → trend still upward despite the outlier dip

─────────────────────────────────────────────────────────────
FILE 30: tests/e2e/test_patient_journey_ramesh.py
─────────────────────────────────────────────────────────────
Complete 8-step E2E journey for Ramesh Kumar (Imagine Cup demo patient).
All Azure services mocked at the service wrapper level.
All assertions unconditional — no if/else guards anywhere.

class TestRameshJourney:
  @pytest.fixture(scope="class")
  def ramesh_tokens(self):
    # Register Ramesh with uuid4-suffixed email
    reg = client.post("/api/auth/register", json={
        "name": "Ramesh Kumar",
        "email": f"ramesh.e2e.{uuid4().hex[:8]}@careorbit.dev",
        "password": "RameshPass123!",
        "phone_number": "+919876543210"
    })
    assert reg.status_code in (200, 201)
    return reg.json()

  def test_step1_register_as_free_tier(self, ramesh_tokens):
    assert "access_token" in ramesh_tokens
    assert "refresh_token" in ramesh_tokens

  def test_step2_upload_prescription_creates_medication_nodes(self, ramesh_tokens):
    Mock vision returning Metformin+Amlodipine+Atorvastatin OCR
    POST /api/documents/upload
    assert data["processing_status"] == "success"
    assert len(data["nodes_created"]) >= 2

  def test_step3_upload_ibuprofen_triggers_interaction(self, ramesh_tokens):
    Mock vision returning Ibuprofen prescription OCR
    Mock search returning Metformin+Ibuprofen interaction
    POST /api/documents/upload
    assert data["processing_status"] in ("success", "needs_confirmation")
    assert len(data["interactions_detected"]) >= 1   ← unconditional

  def test_step4_upload_lab_report_creates_lab_nodes(self, ramesh_tokens):
    Mock vision returning HbA1c/Creatinine/eGFR OCR
    assert len(data["nodes_created"]) >= 2

  def test_step5_confirm_medication_node(self, ramesh_tokens):
    POST /api/confirmations/confirm with node from step 2
    assert data["status"] == "confirmed"
    assert data["new_confidence"] == 0.85

  def test_step6_care_gaps_detected(self, ramesh_tokens):
    Mock search returning ADA guidelines for E11.9 (Type 2 DM)
    GET /api/patients/care-gaps
    assert response.status_code == 200
    assert len(response.json()["care_gaps"]) >= 1   ← unconditional
    gap_names = [g["screening"] for g in response.json()["care_gaps"]]
    assert any("retinopathy" in g.lower() or "eye" in g.lower() for g in gap_names)

  def test_step7_generate_health_summary_pdf(self, ramesh_tokens):
    Mock phig_builder returning 5+ nodes for Ramesh
    GET /api/summary/generate?patient_id=...
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"

  def test_step8a_chat_english_query(self, ramesh_tokens):
    POST /api/chat/query with {"message": "what are my medications?", "language": "en"}
    assert response.status_code == 200
    assert "message" in response.json()
    assert len(response.json()["message"]) > 0

  def test_step8b_chat_hindi_query(self, ramesh_tokens):
    Mock translator.translate
    POST /api/chat/query with {"message": "मेरी दवाइयां क्या हैं", "language": "hi"}
    assert response.status_code == 200
    assert translator_service.translate.call_count >= 1   ← hard assert

─────────────────────────────────────────────────────────────
FILE 31: tests/coverage_matrix.py
─────────────────────────────────────────────────────────────

COVERAGE_MATRIX dictionary mapping 17 P0 features + 1 P1 feature to test files.

P0-01 through P0-14: original 14 MVP features
P0-15: History Agent          (promoted from P1 in v0.3.0 — "NOW P0")
P0-16: Lab Value Trends       (labs.router registered in v0.3.0 main.py)
P0-17: Adherence Tracking     (adherence.router registered in v0.3.0 main.py)
P1-01: Family Caregiver Dashboard (not promoted in v0.3.0)

class TestCoverageCompleteness:
  test_all_17_p0_features_covered:
    p0_features = [k for k in COVERAGE_MATRIX if k.startswith("P0")]
    assert len(p0_features) == 17, \
        f"Expected 17 P0 features (14 original + 3 promoted in v0.3.0). Got: {len(p0_features)}"

  test_one_p1_feature_remaining:
    p1_features = [k for k in COVERAGE_MATRIX if k.startswith("P1")]
    assert len(p1_features) == 1

  test_safety_features_have_fp_and_fn_tests:
    For features P0-06 and P0-07 (drug interaction + care gap detection):
    assert "false_positive" in tests
    assert "false_negative" in tests

  test_auth_has_five_or_more_security_test_files:
    p0_auth = COVERAGE_MATRIX["P0-10: Healthcare-Grade Auth"]
    assert len(p0_auth.get("security", [])) >= 5

════════════════════════════════════════════════════════════════
PART C — HUMAN REVIEW CHECKLIST (generate this table at the end)
════════════════════════════════════════════════════════════════

After generating all 31 files, output the following:

TABLE 1 — Test File Summary
| # | File | Classes | Test Count | Azure Mock Used | Conditional Guards | Tautological |
|---|------|---------|------------|-----------------|-------------------|--------------|
(fill every row from the files you just generated)

TABLE 2 — Azure Service Mock Coverage
| Service | Mock Path Used | SDK Method Mocked | Used In Files |
|---------|---------------|------------------|---------------|
(list all 9 services — exclude Static Web Apps which has no SDK)

TABLE 3 — Phase Marker Verification
| Marker | Files Using It | Tests Marked |
|--------|---------------|-------------|

TABLE 4 — Absolute Rules Compliance
| Rule | Status | Any Violations Found |
|------|--------|---------------------|
| RULE 1: Zero conditional guards        | PASS/FAIL | |
| RULE 2: Zero tautological mock tests   | PASS/FAIL | |
| RULE 3: Zero stub tests (bare pass)    | PASS/FAIL | |
| RULE 4: Azure mocks at service wrapper | PASS/FAIL | |
| RULE 5: Phase markers correct          | PASS/FAIL | |
| RULE 6: Unique emails via uuid4        | PASS/FAIL | |
| RULE 7: Reminder delete hard-asserts   | PASS/FAIL | |
| RULE 8: Interaction tests split        | PASS/FAIL | |

Final counts:
  Total test files generated: ___
  Total test classes: ___
  Total test functions (def test_*): ___
  Tests in default Phase 1 CI run: ___
  Tests excluded (phase2/phase3/demo_only): ___

END WITH THIS EXACT LINE:
"READY FOR HUMAN REVIEW — All 31 test files generated.
Do not proceed to implementation until the human confirms approval."
```
