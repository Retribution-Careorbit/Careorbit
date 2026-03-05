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
**Phase B (Next):** TDD implementation sprint by sprint (RED → GREEN → REFACTOR).

## Tech Stack
- **Backend:** Python 3.12 + FastAPI 0.111.0
- **DB:** Azure PostgreSQL Flexible Server + pgcrypto + SQLAlchemy 2.0.30 async
- **Cache:** Redis (Azure Cache for Redis) — rate limiting + session
- **Queue:** Azure Service Bus — async reminder email delivery
- **Testing:** pytest 8.2.0 + pytest-asyncio 0.23.0 + httpx 0.27.0
- **Frontend (Sprint 6):** React 18 + Vite 5, Tailwind CSS 3.4, Zustand + TanStack Query v5
- **Azure Services (10):** Document Intelligence, OpenAI GPT-4o, Translator, Language NER, Blob Storage, Communication Services (Email), AI Search, PostgreSQL, Key Vault, Static Web Apps

## Project Structure
```
/
├── database/
│   └── schema.sql              # PostgreSQL schema (pgcrypto, 12 tables)
├── docs/
│   ├── sprint_plan.md          # 6-sprint TDD implementation plan
│   └── review_checklist.md     # Human review checklist with compliance tables
├── tests/
│   ├── conftest.py             # Shared fixtures, Azure mock factories, PHASE1_SOURCES
│   ├── coverage_matrix.py      # P0/P1 coverage verification (17 P0 + 1 P1)
│   ├── helpers/
│   │   └── mocks.py            # MockDBSession, MockResult, MockMappings
│   ├── unit/                   # 4 files: confidence, drug_db, encryption, auth_tokens
│   ├── functional/             # 10 files: auth, documents, confirmations, caregivers, etc.
│   ├── integration/            # 2 files: document state machine, orchestrator
│   ├── security/               # 8 files: rate limiting, RBAC, audit, cross-patient
│   ├── business_logic/         # 1 file: tier configuration
│   ├── false_positive_negative/# 2 files: interaction FP/FN (Rule 8 split)
│   ├── regression/             # 1 file: lab trend edge cases
│   └── e2e/                    # 1 file: Ramesh patient journey
├── .github/workflows/
│   └── ci.yml                  # 6-stage CI/CD pipeline
└── pyproject.toml              # Python project config with pytest markers
```

## 8 Absolute Test Rules
1. Zero conditional guards — no `if status_code == 200:` before assertions
2. Zero tautological mocks — never assert a mock's own return value
3. Zero stub tests — no `pass` bodies; use `@xfail(strict=True)` instead
4. Azure mock paths at service wrapper level, not SDK level
5. Correct phase markers: @phase2, @phase3, @demo_only, @slow, @critical
6. Unique state per test — uuid4-suffixed emails everywhere
7. Reminder delete hard-asserts create first — never silent skip
8. Interaction tests split into Wiring vs Algorithm layers

## Key Business Rules
- Confidence ceilings: prescription_photo=0.85, lab_report_photo=0.88, medicine_strip_photo=0.90, patient_text_input=0.60
- patient_confirmed/patient_corrected: hardcoded score=0.85, bypasses ConfidenceCalculator
- Tier prices (cents): free=0, premium_individual=799, premium_family=1999
- Allowed MIME types: image/jpeg, image/png, image/webp, image/heic; 10MB limit
- Caregiver delete: idempotent (always 200, never 404)
- Summary endpoint: GET /api/summary/generate (not POST); returns %PDF magic bytes
- Terminal document statuses only: success, needs_confirmation, failed (never "processing")
