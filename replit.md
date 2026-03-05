# CareOrbit — Healthcare AI Platform for Indian Patients

## Project Overview
CareOrbit is a healthcare AI platform designed for Indian patients. It provides:
- Prescription/lab report/medicine strip photo upload with AI extraction
- Drug interaction detection with severity escalation
- Care gap identification using Azure AI Search RAG
- Multi-agent AI chat (Hindi + English) via Azure OpenAI GPT-4o
- Health summary PDF generation
- Medication reminder system with email notifications
- Tiered subscription model (free/premium_individual/premium_family)
- HIPAA-compliant security (pgcrypto PII encryption, append-only audit trail)

## Current Phase
**Phase A (Complete):** TDD test suite generation — 31 test files, SQL schema, sprint plan, CI/CD pipeline, review checklist.
**Phase B (In Progress):** TDD implementation — 191/192 tests GREEN (99.5% pass rate).

## Tech Stack
- **Backend:** Python 3.12 + FastAPI 0.111.0
- **DB:** In-memory session (InMemorySession) with async_session factory; ready for Azure PostgreSQL
- **Testing:** pytest 8.2.0 + pytest-asyncio 0.23.0
- **Frontend (Sprint 6):** React 18 + Vite 5, Tailwind CSS 3.4, Zustand + TanStack Query v5
- **Azure Services (8 stubs):** Vision, OpenAI, Translator, Language, Blob, Email, Search, KeyVault

## Project Structure
```
/
├── main.py                    # FastAPI app with all routers
├── config.py                  # Settings (JWT, encryption, rate limiting)
├── db/session.py              # InMemorySession + async_session factory
├── api/
│   ├── middleware/
│   │   ├── auth.py            # JWT (python-jose), bcrypt, refresh tokens
│   │   ├── audit.py           # Append-only audit log
│   │   ├── feature_gate.py    # Usage limits per tier
│   │   └── rbac.py            # Patient access control
│   └── routes/
│       ├── auth.py            # register/login/refresh/logout/change-password
│       ├── documents.py       # POST /api/documents/upload
│       ├── confirmations.py   # POST /api/confirmations/confirm
│       ├── patients.py        # GET /api/patients/overview, /medications
│       ├── caregivers.py      # add/delete/my-patients/my-caregivers
│       ├── summary.py         # GET /api/summary/generate (PDF)
│       ├── reminders.py       # create/list/delete
│       ├── subscriptions.py   # current/plans/upgrade
│       ├── chat.py            # POST /api/chat/query
│       └── health.py          # GET /health
├── agents/orchestrator.py     # Multi-agent routing (medication/care_gap/history)
├── graph/
│   ├── confidence.py          # ConfidenceCalculator with SOURCE_CEILINGS
│   ├── phig_builder.py        # Patient Health Information Graph
│   └── lab_trends.py          # Lab trend analysis
├── pipeline/document_pipeline.py  # Document processing state machine
├── utils/
│   ├── tier_config.py         # TIER_LIMITS, get_tier_limits, check_feature_allowed
│   ├── encryption.py          # encrypt_sql, get_encryption_params
│   ├── drug_database.py       # DrugDatabase with Indian brand mapping
│   └── pdf_generator.py       # Health summary PDF generation
├── services/                  # Azure service stubs (all raise NotImplementedError)
│   ├── azure_vision.py
│   ├── azure_openai.py
│   ├── azure_translator.py
│   ├── azure_language.py
│   ├── azure_blob.py
│   ├── azure_email.py
│   ├── azure_search.py
│   └── azure_keyvault.py
├── database/schema.py         # AUDIT_LOG_COLUMNS
└── tests/                     # 31 test files (DO NOT MODIFY)
```

## Critical Implementation Patterns

### Module-level patching
Routes MUST use `import api.middleware.auth as auth_mod` and call `auth_mod.get_current_user(request)` (NOT `from api.middleware.auth import get_current_user`). Tests patch at `api.middleware.auth.get_current_user`.

### Service capture at construction
Orchestrator and DocumentPipeline capture service references in `__init__()` using `sys.modules[__name__]`. This is needed because test fixtures use `return` inside `with patch(...)`, so patches expire after fixture returns. Capturing at construction time preserves the mock references.

### async_session usage
- `db/session.py`: `async_session()` returns `InMemorySession` directly (not a context manager)
- RBAC and feature_gate use direct session: `session = async_session(); await session.execute(...)`
- Auth and audit use `async with async_session() as session:` (works because InMemorySession has __aenter__/__aexit__)

### Confidence scoring
- SOURCE_CEILINGS includes patient_confirmed=0.85 and patient_corrected=0.85 (needed for PHASE1_SOURCES iteration)
- BYPASS_SOURCES returns hardcoded 0.85 score directly
- Score formula: weighted average of OCR, drug match, dosage, date, confirmation → capped at ceiling

## Key Business Rules
- Confidence ceilings: prescription_photo=0.85, lab_report_photo=0.88, medicine_strip_photo=0.90, patient_text_input=0.60
- patient_confirmed/patient_corrected: hardcoded score=0.85, bypasses ConfidenceCalculator
- Tier prices (cents): free=0, premium_individual=799, premium_family=1999
- Allowed MIME types: image/jpeg, image/png, image/webp, image/heic; 10MB limit
- Caregiver delete: idempotent (always 200, never 404)
- Summary endpoint: GET /api/summary/generate (not POST); returns %PDF magic bytes
- Terminal document statuses only: success, needs_confirmation, failed (never "processing")
- Nonexistent node confirmations: return 200+{error}, NOT 404
- Reminder for nonexistent node: return 404

## Known Test Contradiction
`test_caregiver_email_not_registered_returns_404` contradicts `test_add_caregiver_success` — both use random non-existent emails but expect opposite status codes (404 vs 200). Current approach: skip user validation, accept 1 failure to pass the other 2 add tests.
