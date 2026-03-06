# CareOrbit — Onboarding & Profile-Completion Implementation Plan

**Version:** 1.0.0
**Date:** 2026-03-06
**Author:** Architecture & QA Lead
**Status:** Proposed

---

## Executive Summary

CareOrbit's AI pipeline (drug interaction severity escalation, living narrative generation, pre-visit briefs, and care gap identification) produces materially better outputs when patient demographics are available. Today, registration accepts `date_of_birth`, `gender`, and `preferred_language` as optional fields — meaning most users skip them, and downstream models operate on incomplete profiles.

This plan introduces a **mandatory onboarding gate** that collects four critical fields (`date_of_birth`, `gender`, `preferred_language`, `medical_literacy_level`) before the user can access core features. Six additional fields (`blood_type`, `height_cm`, `weight_kg`, `city`, `state`, `country`) remain optional. The plan recommends a **post-registration / first-login onboarding flow** (Option B) over registration-time collection, with detailed justification across five dimensions.

The plan includes exact backend changes, validation rules, security analysis, 67 production-grade test cases organized into 6 categories, API contracts, a 4-phase delivery schedule, and risk analysis — all grounded in the current codebase state (322 passing tests, `_users_store` in-memory dict, `async_session()` returning `InMemorySession`, no real PostgreSQL connected).

**Current codebase state (verified):**
- `users` table schema has `date_of_birth DATE`, `gender VARCHAR(10)`, `preferred_language VARCHAR(5)`, `city`, `state` — but the `INSERT` in `/api/auth/register` only persists `id`, `name` (encrypted), `email`, `phone_number`, `password_hash` to SQL. DOB/gender/language are stored only in the in-memory `_users_store` dict.
- `patient_profiles` table has `blood_type VARCHAR(5)` (not `blood_group`), `emergency_contact BYTEA`, `conditions JSONB`, `allergies JSONB`. No `height_cm`, `weight_kg`, `country`, or `emergency_contact_name` columns.
- No `medical_literacy_level` column exists anywhere in the schema.
- No profile update endpoint exists — `api/routes/patients.py` has only GET `/overview` and GET `/medications`.
- Login response currently returns `user: {id, name, email}` (added during Ramesh seed data work). Register returns `user: {id}`.
- No onboarding state machine, no `onboarding_completed_at` flag.

---

## Table of Contents

1. [Objective](#section-1--objective)
2. [Recommended Product Flow](#section-2--recommended-product-flow)
3. [Backend Change Plan](#section-3--backend-change-plan)
4. [Validation Rules](#section-4--validation-rules)
5. [Security / Privacy / Compliance Impact](#section-5--security--privacy--compliance-impact)
6. [Test Strategy](#section-6--test-strategy)
7. [Exact Test Case Inventory](#section-7--exact-test-case-inventory)
8. [API Contract Proposals](#section-8--api-contract-proposals)
9. [Suggested File Layout](#section-9--suggested-file-layout)
10. [Priority and Delivery Plan](#section-10--priority-and-delivery-plan)
11. [Risks / Ambiguities](#section-11--risks--ambiguities)
12. [Final Recommendation](#section-12--final-recommendation)

---

## SECTION 1 — Objective

### Goal

Add mandatory onboarding signals to CareOrbit that improve personalization quality, clinical safety, and user experience across every AI-powered feature.

### Why These Four Fields Matter

| Field | Impact |
|-------|--------|
| `date_of_birth` | Drug interaction severity escalation uses age thresholds (e.g., `age_over_65` modifier in `conftest.py` mock_search fixture). Pre-visit briefs contextualize findings by age. Living narrative includes age. Family dashboard groups by age. Lab reference ranges are age-dependent. |
| `gender` | Lab reference ranges differ by sex (creatinine, hemoglobin). Drug dosing guidelines reference biological sex. Care gap screening schedules are gender-specific. Living narrative and pre-visit briefs need gender pronouns. |
| `preferred_language` | Azure Translator service selection (`hi` vs `en`). Chat orchestrator language routing. Summary PDF language. Notification email language. Already exists in schema but has no validation — any string is accepted. |
| `medical_literacy_level` | Controls AI response verbosity and medical jargon density. A `basic` user gets "Your blood sugar is a bit high" while an `advanced` user gets "HbA1c 7.8% exceeds ADA target of <7.0%, suggesting suboptimal glycemic control." Directly affects Azure OpenAI system prompt construction. |

### Why Store `date_of_birth`, Not `age`

1. **Age is a derived, time-varying quantity.** Storing `age = 68` becomes stale after the patient's next birthday. Every query that needs age would require a separate "last updated" check.
2. **DOB enables precise age-at-event calculations.** A pre-visit brief generated on 2026-03-14 for a patient born 1958-03-15 should say "67 years old" — but 24 hours later should say "68 years old." This is only possible with DOB.
3. **Regulatory alignment.** HIPAA, ABDM (Ayushman Bharat Digital Mission), and FHIR R4 `Patient` resource all use `birthDate`, not age.
4. **Current codebase:** The `users` table already has `date_of_birth DATE` (schema.sql line 25). The `patient_ramesh` fixture in conftest.py stores both `dob: date(1958, 3, 15)` and `age: 68` — the age field should be computed dynamically, not persisted.

---

## SECTION 2 — Recommended Product Flow

### Option Comparison

| Dimension | Option A: Collect at Registration | Option B: Collect at First Login (Recommended) |
|-----------|-----------------------------------|-----------------------------------------------|
| **Product UX** | Registration form becomes 8+ fields, increasing abandonment. Users want to try the app before investing personal details. | Registration stays lean (name + email + password). Onboarding feels like a guided "complete your profile" step after first login — lower cognitive load, higher conversion. |
| **Backend Complexity** | All validation in one route (`/api/auth/register`). No state machine needed. Simple but rigid. | Requires an `onboarding_completed_at` flag and a lightweight middleware gate. Slightly more complex but decoupled — profile logic separated from auth logic. |
| **Security / Privacy** | Collects sensitive data (DOB, gender) before the user has verified their email or built trust. | User has already authenticated and entered the app. Higher trust context for sharing health demographics. |
| **Testability** | Fewer endpoints to test but registration tests become large and brittle (many field combinations). | Clean separation: auth tests stay small, onboarding tests are isolated. Easier to test incomplete/complete transitions. |
| **MVP Alignment** | Current `RegisterRequest` already has optional DOB/gender/language. Making them required would break existing tests (`test_register_success_returns_tokens` sends no DOB/gender). | Non-breaking. Registration contract unchanged. New endpoints/behavior added alongside. Existing 322 tests unaffected. |

### Recommendation: Option B — First-Login Onboarding

**Rationale:** CareOrbit's existing registration tests (`tests/functional/test_api_auth.py`) pass with minimal fields (name, email, password). Making DOB/gender mandatory at registration would break 3+ existing tests and contradict the current API contract. Option B preserves backward compatibility while adding a clear onboarding state machine.

### User Journey

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER JOURNEY                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. REGISTER                                                    │
│     POST /api/auth/register                                     │
│     Body: { name, email, password }                             │
│     Response: { access_token, refresh_token, user: {id} }       │
│     State: onboarding_completed_at = NULL                       │
│                                                                 │
│  2. FIRST AUTHENTICATED REQUEST                                 │
│     GET /api/patients/overview (or any protected route)          │
│     → Middleware checks onboarding_completed_at                  │
│     → If NULL: returns 200 with header                          │
│       X-Onboarding-Required: true                               │
│     → Frontend redirects to /onboarding                         │
│                                                                 │
│  3. COMPLETE ONBOARDING                                         │
│     PUT /api/patients/profile                                   │
│     Body: {                                                     │
│       date_of_birth: "1958-03-15",   // mandatory               │
│       gender: "male",                // mandatory               │
│       preferred_language: "hi",      // mandatory               │
│       medical_literacy_level: "basic", // mandatory             │
│       blood_type: "B+",             // optional                  │
│       height_cm: 170,               // optional                 │
│       weight_kg: 78,                // optional                 │
│       city: "Durgapur",             // optional                 │
│       state: "West Bengal",         // optional                 │
│       country: "IN"                 // optional                 │
│     }                                                           │
│     Response: 200 { profile: {...}, onboarding_complete: true } │
│     State: onboarding_completed_at = NOW()                      │
│     Audit: PROFILE_ONBOARDING_COMPLETE                          │
│                                                                 │
│  4. SUBSEQUENT SESSIONS                                         │
│     Login → onboarding_completed_at is set                      │
│     → No redirect, full access to all features                  │
│     → Profile updates via same PUT /api/patients/profile        │
│       (mandatory fields not re-required if already set)         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### State Transitions

| State | `onboarding_completed_at` | Behavior |
|-------|---------------------------|----------|
| `REGISTERED` | `NULL` | User can log in. Protected routes return `X-Onboarding-Required: true` header. Frontend shows onboarding screen. |
| `ONBOARDING_COMPLETE` | Timestamp | Full access to all features. Profile can still be updated. |

### Why NOT Block API Access

Blocking all API routes for incomplete onboarding would break existing functional tests and create a hard gate that complicates caregiver flows. Instead, the onboarding signal is **advisory** — the backend sets a response header, and the frontend handles the redirect. API endpoints remain functional for automated/test clients.

---

## SECTION 3 — Backend Change Plan

### 3.1 Schema Changes

#### `users` table — add onboarding timestamp

```sql
ALTER TABLE users ADD COLUMN medical_literacy_level VARCHAR(20) DEFAULT NULL;
ALTER TABLE users ADD COLUMN onboarding_completed_at TIMESTAMPTZ DEFAULT NULL;
```

**No migration needed for:** `date_of_birth`, `gender`, `preferred_language`, `city`, `state` — these already exist on the `users` table.

#### `patient_profiles` table — add physical/demographic fields

```sql
ALTER TABLE patient_profiles ADD COLUMN height_cm FLOAT;
ALTER TABLE patient_profiles ADD COLUMN weight_kg FLOAT;
ALTER TABLE patient_profiles ADD COLUMN country VARCHAR(3) DEFAULT 'IN';
ALTER TABLE patient_profiles ADD COLUMN emergency_contact_name VARCHAR(255);
ALTER TABLE patient_profiles ADD COLUMN emergency_contact_phone BYTEA; -- pgp_sym_encrypt
```

**No migration needed for:** `blood_type` (already exists as `VARCHAR(5)` on `patient_profiles`), `emergency_contact` (already exists as `BYTEA` on `patient_profiles`).

#### In-Memory Store Changes

Since CareOrbit uses `_users_store` (dict) in `api/routes/auth.py`, the schema changes translate to:

- Add `medical_literacy_level` and `onboarding_completed_at` keys to user dicts in `_users_store`
- Add a `_patient_profiles_store` dict (keyed by user_id) for extended profile data
- Or extend the existing `_users_store` entries with profile fields (simpler for MVP)

**Recommended:** Extend `_users_store` with all profile fields for simplicity. Split into a real `patient_profiles` table when PostgreSQL is connected.

**Note on current SQL gap:** The register route currently executes `INSERT INTO users (id, name, email, phone_number, password_hash)` — it does NOT persist DOB, gender, language, city, or state to SQL even though the schema supports these columns. The profile update route should also update the SQL INSERT/UPDATE to include these fields when real DB is connected. For now, in-memory `_users_store` is the source of truth.

### 3.2 Request Models

#### New: `ProfileUpdateRequest` (in `api/routes/patients.py`)

```python
class ProfileUpdateRequest(BaseModel):
    date_of_birth: Optional[str] = None        # ISO 8601 date
    gender: Optional[str] = None               # male|female|other|prefer_not_to_say
    preferred_language: Optional[str] = None    # en|hi|bn|ta|te|mr|gu|kn|ml
    medical_literacy_level: Optional[str] = None # basic|intermediate|advanced
    blood_type: Optional[str] = None             # A+|A-|B+|B-|AB+|AB-|O+|O-
    height_cm: Optional[float] = None           # 30.0–300.0
    weight_kg: Optional[float] = None           # 1.0–500.0
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None               # ISO 3166-1 alpha-2
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
```

All fields are individually optional in the model, but **first-time onboarding** requires the four mandatory fields to be non-null after the update.

**Important codebase gap:** The current register route stores DOB/gender/language/city/state only in the in-memory `_users_store` dict — the SQL INSERT does NOT include these fields. The profile update route must handle both in-memory store writes and SQL persistence (when real DB is connected).

### 3.3 Route Changes

| Route | File | Change |
|-------|------|--------|
| `PUT /api/patients/profile` | `api/routes/patients.py` | **NEW.** Accepts `ProfileUpdateRequest`. Validates fields. Updates `_users_store` and/or DB. Sets `onboarding_completed_at` if all mandatory fields present. Logs `PROFILE_UPDATE` audit event. |
| `GET /api/patients/profile` | `api/routes/patients.py` | **NEW.** Returns current profile with all fields + `onboarding_complete: bool` + `age` (derived from DOB). |
| `POST /api/auth/register` | `api/routes/auth.py` | **NO CHANGE** to request contract. Add `onboarding_completed_at: None` and `medical_literacy_level: None` to stored user dict in `_users_store`. If DOB/gender/language/literacy all provided at registration (forward-compatible), set `onboarding_completed_at`. Response `user` object gets `onboarding_complete: false`. |
| `POST /api/auth/login` | `api/routes/auth.py` | **MINOR CHANGE.** Login response already returns `user: {id, name, email}`. Add `onboarding_complete: bool` and `preferred_language: str` to this object. |
| Onboarding middleware | `api/middleware/onboarding.py` | **NEW.** Not a global ASGI middleware — instead, a helper function called explicitly from protected routes (matching the existing `get_current_user` call pattern). Adds `X-Onboarding-Required: true` header when `onboarding_completed_at` is NULL. Does NOT block requests. |

### 3.4 Validation Layer

Create `utils/profile_validators.py` with pure functions:

```python
def validate_date_of_birth(dob_str: str) -> date        # raises ValueError
def validate_gender(gender: str) -> str                  # raises ValueError
def validate_preferred_language(lang: str) -> str        # raises ValueError
def validate_medical_literacy_level(level: str) -> str   # raises ValueError
def validate_blood_type(bt: str) -> str                   # raises ValueError
def validate_height_cm(h: float) -> float                # raises ValueError
def validate_weight_kg(w: float) -> float                # raises ValueError
def validate_emergency_phone(phone: str) -> str          # raises ValueError
def derive_age(dob: date) -> int                         # pure computation
```

### 3.5 Audit Events

| Action | When | Metadata |
|--------|------|----------|
| `PROFILE_UPDATE` | Any profile field updated | `{"fields_updated": ["date_of_birth", "gender", ...]}` |
| `PROFILE_ONBOARDING_COMPLETE` | First time all mandatory fields are set | `{"mandatory_fields": ["date_of_birth", "gender", "preferred_language", "medical_literacy_level"]}` |

### 3.6 Encryption Handling

| Field | Storage | Encryption |
|-------|---------|-----------|
| `date_of_birth` | `users.date_of_birth` (DATE) | **Plaintext** — needed for age derivation queries. Considered sensitive-but-functional. HIPAA allows date storage without encryption if access-controlled. |
| `gender` | `users.gender` (VARCHAR) | **Plaintext** — low sensitivity, needed for care gap queries. |
| `preferred_language` | `users.preferred_language` (VARCHAR) | **Plaintext** — not PII. |
| `medical_literacy_level` | `users.medical_literacy_level` (VARCHAR) | **Plaintext** — not PII. |
| `emergency_contact_phone` | `patient_profiles.emergency_contact_phone` (BYTEA) | **Encrypted** — `pgp_sym_encrypt`. Phone numbers are PII. |
| `emergency_contact_name` | `patient_profiles.emergency_contact_name` (VARCHAR) | **Plaintext** in MVP. Consider encryption in Phase 2. |
| `city`, `state`, `country` | `users` / `patient_profiles` | **Plaintext** — demographic, not PII per HIPAA. |

### 3.7 Response Contract Changes

| Endpoint | Change |
|----------|--------|
| `POST /api/auth/login` | Add `user.onboarding_complete: bool` to response |
| `POST /api/auth/register` | Add `user.onboarding_complete: false` to response |
| `GET /api/patients/profile` | New endpoint — returns full profile |
| `PUT /api/patients/profile` | New endpoint — returns updated profile |

---

## SECTION 4 — Validation Rules

### 4.1 `date_of_birth`

| Rule | Constraint | Error |
|------|-----------|-------|
| Format | ISO 8601 date string (`YYYY-MM-DD`) | 400: "Invalid date format. Use YYYY-MM-DD" |
| Not future | `dob <= today` | 400: "Date of birth cannot be in the future" |
| Plausible age | `0 < age <= 120` (computed from DOB) | 400: "Implausible date of birth" |
| Age derivation | `age = floor((today - dob).days / 365.25)` | Pure computation, never stored |

**Edge cases:**
- Leap year birthdays (Feb 29): valid, age computed correctly
- Today's date as DOB (newborn): valid, age = 0
- DOB = "1900-01-01" (age 126): rejected as implausible

### 4.2 `gender`

| Rule | Constraint |
|------|-----------|
| Allowed values | `male`, `female`, `other`, `prefer_not_to_say` |
| Case | Case-insensitive input, stored lowercase |
| Model behavior when `prefer_not_to_say` | AI prompts omit gender context. Lab reference ranges use combined/unisex ranges. Care gap screening uses age-only criteria. |

### 4.3 `preferred_language`

| Rule | Constraint |
|------|-----------|
| Allowed values (MVP) | `en` (English), `hi` (Hindi), `bn` (Bengali), `ta` (Tamil), `te` (Telugu), `mr` (Marathi), `gu` (Gujarati), `kn` (Kannada), `ml` (Malayalam) |
| Default | `en` |
| Fallback | If Azure Translator does not support the language, fall back to `en` with a warning in the response |

These are ISO 639-1 codes for India's 8 most-spoken languages plus English.

### 4.4 `medical_literacy_level`

| Rule | Constraint |
|------|-----------|
| Allowed values | `basic`, `intermediate`, `advanced` |
| Default | `basic` (if not provided) |
| Impact on AI responses | `basic`: Plain language, analogies, no medical jargon. `intermediate`: Medical terms with brief explanations. `advanced`: Full clinical terminology, lab values with context. |

### 4.5 `height_cm`

| Rule | Constraint |
|------|-----------|
| Type | Float |
| Range | 30.0 – 300.0 cm |
| Optional | Yes — not required for onboarding |

### 4.6 `weight_kg`

| Rule | Constraint |
|------|-----------|
| Type | Float |
| Range | 1.0 – 500.0 kg |
| Optional | Yes — not required for onboarding |

### 4.7 `blood_type`

| Rule | Constraint |
|------|-----------|
| Allowed values | `A+`, `A-`, `B+`, `B-`, `AB+`, `AB-`, `O+`, `O-` |
| Case | Case-insensitive input, stored uppercase |
| Optional | Yes |
| Schema | Already exists as `patient_profiles.blood_type VARCHAR(5)` |

### 4.8 Emergency Contact Fields

| Field | Validation |
|-------|-----------|
| `emergency_contact_name` | 1–255 characters. Optional. |
| `emergency_contact_phone` | Validated against E.164 pattern (`^\+[1-9]\d{6,14}$`). Optional. Encrypted at rest. |

---

## SECTION 5 — Security / Privacy / Compliance Impact

### 5.1 Encryption Requirements

| Field | Classification | Encryption Required | Rationale |
|-------|---------------|-------------------|-----------|
| `date_of_birth` | PHI (Protected Health Information) | No (at-rest in DB with access control) | Needed for age derivation in SQL queries. Access-controlled via RBAC. |
| `gender` | Demographic | No | Low sensitivity. Required for care gap logic. |
| `preferred_language` | Preference | No | Not PII. |
| `medical_literacy_level` | Preference | No | Not PII. |
| `emergency_contact_phone` | PII | **Yes** — `pgp_sym_encrypt` | Phone numbers are always PII. Follows existing pattern for `users.phone_number`. |
| `emergency_contact_name` | PII-adjacent | No (MVP) | Name alone is low-risk. Consider encrypting in Phase 2 if combined with phone. |

### 5.2 RBAC Implications

| Scenario | Access Level | Behavior |
|----------|-------------|----------|
| Patient reads own profile | `full` (self-access) | Returns all fields including DOB, gender |
| Caregiver with `view` reads patient profile | `view` | Returns profile **without** emergency contact fields |
| Caregiver with `edit` updates patient profile | `edit` | Can update optional fields. Cannot change mandatory fields (DOB, gender) on behalf of patient. |
| Caregiver with `full` updates patient profile | `full` | Full write access, same as patient |
| Unauthenticated request | None | 401 Unauthorized |
| Patient A reads Patient B's profile | Denied | 403 Forbidden |

### 5.3 Audit Trail Requirements

The following actions MUST generate audit log entries:

| Action | `audit_log.action` | Metadata |
|--------|---------------------|----------|
| Profile update | `PROFILE_UPDATE` | `{"fields_updated": [...], "onboarding_triggered": false}` |
| Onboarding completion | `PROFILE_ONBOARDING_COMPLETE` | `{"mandatory_fields_set": true, "completed_at": "..."}` |
| Profile read by caregiver | `PROFILE_VIEW` | `{"viewer_id": "...", "viewer_role": "caregiver"}` |

**Test cases required for audit correctness:**
- Audit entry created on every profile update (even no-op updates)
- Audit metadata contains exact field names that changed
- Audit log is append-only (no UPDATE/DELETE on audit_log table)
- Audit log cannot be bypassed by direct SQL
- Onboarding completion audit event fires exactly once

### 5.4 API Exposure

| Field | Exposed in `GET /api/patients/profile` | Exposed in login response | Exposed in `/api/patients/overview` |
|-------|----------------------------------------|--------------------------|-------------------------------------|
| `date_of_birth` | Yes | No | No |
| `age` (derived) | Yes | No | Yes (for dashboard) |
| `gender` | Yes | No | No |
| `preferred_language` | Yes | Yes (for frontend i18n) | No |
| `medical_literacy_level` | Yes | No | No |
| `emergency_contact_phone` | Yes (masked: `+91****3210`) | No | No |
| `onboarding_complete` | Yes | Yes | No |

---

## SECTION 6 — Test Strategy

### 6.1 Unit Tests

**Purpose:** Validate individual validator functions in isolation.

| Scope | What to Test | Mocked | Real |
|-------|-------------|--------|------|
| `validate_date_of_birth` | Format, future date, plausible age, leap year | `datetime.date.today()` (frozen) | Validator logic |
| `validate_gender` | Allowed values, case normalization, invalid input | Nothing | Validator logic |
| `validate_preferred_language` | Enum membership, fallback | Nothing | Validator logic |
| `validate_medical_literacy_level` | Enum membership | Nothing | Validator logic |
| `validate_blood_type` | Valid types, invalid input | Nothing | Validator logic |
| `validate_height_cm` / `validate_weight_kg` | Bounds, type errors | Nothing | Validator logic |
| `derive_age` | Age computation, edge cases | `date.today()` (frozen) | Age math |

**Key failure modes:** Off-by-one age on birthday boundary, timezone-dependent date comparisons.
**CI vs nightly:** All unit tests run in CI.

### 6.2 Functional / API Tests

**Purpose:** Verify HTTP contracts — request/response shapes, status codes, error payloads.

| Scope | What to Test | Mocked | Real |
|-------|-------------|--------|------|
| `PUT /api/patients/profile` | Success with mandatory fields, partial update, validation errors | `auth_mod.get_current_user` | FastAPI TestClient, route logic |
| `GET /api/patients/profile` | Returns all fields, derived age, masked phone | `auth_mod.get_current_user` | FastAPI TestClient, route logic |
| Login response | `onboarding_complete` flag in response | Nothing (uses `_users_store` directly) | Auth route logic |
| Onboarding header | `X-Onboarding-Required` present when incomplete | `auth_mod.get_current_user` | Middleware logic |

**Key failure modes:** 422 vs 400 status code confusion, missing fields in response, wrong content-type.
**CI vs nightly:** All functional tests run in CI.

### 6.3 Integration Tests

**Purpose:** Verify cross-module behavior — profile update → audit log, profile update → onboarding flag, profile data → AI pipeline.

| Scope | What to Test | Mocked | Real |
|-------|-------------|--------|------|
| Profile → Audit | Update creates audit entry with correct metadata | DB session | Audit middleware, route |
| Profile → Onboarding | Setting all mandatory fields sets `onboarding_completed_at` | DB session | Route logic |
| Profile → Encryption | Emergency phone encrypted in SQL params | Encryption key | `get_encryption_params` |
| Profile → PHIG | Age/gender available in patient graph | PHIG builder (partial) | Profile retrieval |

**Key failure modes:** Audit not written on partial update, encryption key missing.
**CI vs nightly:** CI for audit/encryption; nightly for PHIG integration.

### 6.4 Security Tests

**Purpose:** Verify access control, data isolation, and compliance.

| Scope | What to Test |
|-------|-------------|
| RBAC | Patient cannot update another patient's profile |
| RBAC | Caregiver with `view` cannot edit profile |
| RBAC | Caregiver with `edit` can update optional fields only |
| Data isolation | Profile GET returns only the authenticated patient's data |
| Encryption | Emergency contact phone not stored as plaintext in mock DB |
| Audit integrity | Profile update cannot bypass audit log |

**Key failure modes:** RBAC check on wrong user_id field, missing RBAC on new endpoint.
**CI vs nightly:** All security tests in CI.

### 6.5 Business Logic Tests

**Purpose:** Verify product rules — onboarding gating, age derivation, literacy impact.

| Scope | What to Test |
|-------|-------------|
| Onboarding gate | Incomplete profile has `onboarding_complete: false` |
| Onboarding idempotence | Completing onboarding twice does not error or duplicate audit |
| Age derivation | Correct age for various DOB/today combinations |
| Language fallback | Unknown language falls back to `en` |
| Literacy impact | `basic` vs `advanced` affects system prompt selection |

**Key failure modes:** Age off-by-one, onboarding flag not set when fields supplied at registration.
**CI vs nightly:** CI.

### 6.6 E2E / Onboarding Journey Tests

**Purpose:** Full user journey — register → login → onboarding prompt → complete profile → access features.

| Scope | What to Test |
|-------|-------------|
| Happy path | Register → login → see onboarding header → complete profile → header gone |
| Partial completion | Submit with only 2 of 4 mandatory fields → still incomplete |
| Legacy user | Login with pre-existing user (no DOB/gender) → onboarding prompted |
| Demo user Ramesh | Ramesh's profile already has all fields → no onboarding prompt |

**Key failure modes:** State leakage between tests (shared `_users_store`), TestClient not propagating headers.
**CI vs nightly:** CI for happy path; nightly for legacy/demo user journeys.

### 6.7 Regression Tests

**Purpose:** Ensure existing functionality is not broken by onboarding changes.

| Scope | What to Test |
|-------|-------------|
| Registration | Existing tests still pass with optional fields unchanged |
| Login | Login response backward-compatible (new fields additive) |
| Patient overview | Dashboard works for users without profile data |
| Medications | Medications endpoint unaffected |
| Reminders | Reminder CRUD unaffected |
| Chat | Chat responds even with incomplete profile |

**Key failure modes:** Registration test expects exact response shape, login test breaks on new field.
**CI vs nightly:** All regression tests in CI.

---

## SECTION 7 — Exact Test Case Inventory

### A. Registration Flow (7 tests)

```
tests/functional/test_api_profile_onboarding.py

class TestRegistrationOnboarding:
    test_register_creates_user_with_onboarding_incomplete
        # POST /api/auth/register with min fields → 200
        # response.user.onboarding_complete == False

    test_register_preserves_preferred_language_when_provided
        # POST /api/auth/register with preferred_language="hi" → 200
        # GET /api/patients/profile → preferred_language == "hi"

    test_register_defaults_preferred_language_to_english
        # POST /api/auth/register without preferred_language → 200
        # stored user has preferred_language == "en"

    test_register_with_all_mandatory_fields_completes_onboarding
        # POST /api/auth/register with dob+gender+language+literacy → 200
        # response.user.onboarding_complete == True

    test_register_audit_event_written
        # POST /api/auth/register → 200
        # audit_log contains REGISTER action with user_id

    test_register_stores_name_via_encryption_params
        # POST /api/auth/register with name="Test" → 200
        # verify get_encryption_params called (mock utils.encryption)
        # verify SQL contains pgp_sym_encrypt placeholder

    test_register_does_not_require_mandatory_onboarding_fields
        # POST /api/auth/register with only name+email+password → 200
        # backward compatibility preserved
```

### B. First Login / Onboarding Completion Flow (12 tests)

```
tests/functional/test_api_profile_onboarding.py

class TestOnboardingCompletion:
    test_login_returns_onboarding_incomplete_for_new_user
        # register → login → response includes onboarding_complete: false

    test_profile_completion_with_all_mandatory_fields_succeeds
        # PUT /api/patients/profile with dob+gender+language+literacy → 200
        # response.onboarding_complete == True

    test_profile_completion_missing_dob_remains_incomplete
        # PUT /api/patients/profile with gender+language+literacy (no dob) → 200
        # response.onboarding_complete == False

    test_profile_completion_missing_gender_remains_incomplete
        # PUT /api/patients/profile with dob+language+literacy (no gender) → 200
        # response.onboarding_complete == False

    test_profile_completion_missing_language_remains_incomplete
        # PUT /api/patients/profile with dob+gender+literacy (no lang) → 200
        # response.onboarding_complete == False

    test_profile_completion_missing_literacy_remains_incomplete
        # PUT /api/patients/profile with dob+gender+language (no literacy) → 200
        # response.onboarding_complete == False

    test_subsequent_updates_do_not_require_all_mandatory_fields
        # complete onboarding → PUT /api/patients/profile with only city → 200
        # onboarding_complete still True

    test_onboarding_completion_is_idempotent
        # complete onboarding → PUT same mandatory fields again → 200
        # no error, onboarding_complete still True

    test_onboarding_completion_writes_audit_event
        # complete onboarding → audit_log contains PROFILE_ONBOARDING_COMPLETE

    test_onboarding_complete_audit_fires_only_once
        # complete onboarding twice → only 1 PROFILE_ONBOARDING_COMPLETE in audit

    test_profile_update_writes_audit_with_field_names
        # PUT /api/patients/profile with city+state → 200
        # audit metadata contains fields_updated: ["city", "state"]

    test_get_profile_returns_onboarding_status
        # GET /api/patients/profile → response includes onboarding_complete: bool
```

### C. Validation Tests (16 tests)

```
tests/unit/test_profile_validators.py

class TestDateOfBirthValidation:
    test_valid_dob_accepted
        # "1958-03-15" → returns date(1958, 3, 15)

    test_future_dob_rejected
        # "2099-01-01" → raises ValueError("cannot be in the future")

    test_implausible_age_rejected
        # "1850-01-01" (age > 120) → raises ValueError("Implausible")

    test_invalid_format_rejected
        # "15/03/1958" → raises ValueError("Invalid date format")

    test_leap_year_dob_accepted
        # "2000-02-29" → valid

    test_today_dob_accepted
        # today's date → valid (age = 0, newborn)

class TestDeriveAge:
    test_age_computed_correctly
        # dob=1958-03-15, today=2026-03-06 → age=67

    test_age_after_birthday
        # dob=1958-03-15, today=2026-03-16 → age=68

    test_age_on_birthday
        # dob=1958-03-15, today=2026-03-15 → age=68

class TestGenderValidation:
    test_valid_genders_accepted
        # "male", "female", "other", "prefer_not_to_say" → all valid

    test_case_insensitive
        # "MALE" → "male"

    test_invalid_gender_rejected
        # "apache" → raises ValueError

class TestLanguageValidation:
    test_valid_languages_accepted
        # "en", "hi", "bn", "ta", "te", "mr", "gu", "kn", "ml" → all valid

    test_invalid_language_rejected
        # "xx" → raises ValueError

class TestLiteracyValidation:
    test_valid_levels_accepted
        # "basic", "intermediate", "advanced" → all valid

    test_invalid_level_rejected
        # "expert" → raises ValueError

class TestPhysicalValidation:
    test_unrealistic_height_rejected
        # 5.0 (too short) → raises ValueError
        # 350.0 (too tall) → raises ValueError

    test_unrealistic_weight_rejected
        # 0.5 (too light) → raises ValueError
        # 600.0 (too heavy) → raises ValueError

class TestBloodTypeValidation:
    test_valid_blood_types_accepted
        # "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-" → all valid

    test_invalid_blood_type_rejected
        # "C+" → raises ValueError

class TestEmergencyPhoneValidation:
    test_valid_e164_phone_accepted
        # "+919876543210" → valid

    test_malformed_phone_rejected
        # "9876543210" (missing +) → raises ValueError
        # "+1" (too short) → raises ValueError
```

### D. Security Tests (8 tests)

```
tests/security/test_profile_rbac.py

class TestProfileRBAC:
    test_patient_cannot_update_other_patient_profile
        # User A auth → PUT /api/patients/profile?patient_id=B → 403

    test_caregiver_view_cannot_edit_profile
        # Caregiver with view permission → PUT /api/patients/profile?patient_id=patient → 403

    test_caregiver_edit_can_update_optional_fields
        # Caregiver with edit permission → PUT optional fields → 200

    test_caregiver_edit_cannot_change_mandatory_fields
        # Caregiver with edit → PUT date_of_birth → 403

    test_unauthenticated_profile_access_rejected
        # No auth header → GET /api/patients/profile → 401

    test_profile_get_returns_only_own_data
        # User A auth → GET /api/patients/profile → returns A's profile, not B's

    test_emergency_phone_encrypted_in_store
        # PUT emergency_contact_phone="+919876543211" → 200
        # GET /api/patients/profile → phone returned masked as "+91****3211"
        # verify raw phone string not present in _users_store values

    test_profile_update_creates_audit_entry
        # PUT /api/patients/profile with city="Mumbai" → 200
        # verify audit_log contains entry with action="PROFILE_UPDATE"
        # and metadata includes "city" in fields_updated
```

### E. Personalization / Business Behavior Tests (10 tests)

```
tests/business_logic/test_profile_personalization.py

class TestLanguagePersonalization:
    test_preferred_language_hi_selects_hindi_translation
        # user with preferred_language="hi" → translator called with target="hi"

    test_preferred_language_en_skips_translation
        # user with preferred_language="en" → translator not called

    test_unknown_language_falls_back_to_english
        # user with preferred_language="xx" (shouldn't happen post-validation)
        # → system treats as "en"

class TestLiteracyPersonalization:
    test_basic_literacy_produces_simple_language
        # medical_literacy_level="basic" → AI prompt includes "plain language"

    test_advanced_literacy_produces_clinical_language
        # medical_literacy_level="advanced" → AI prompt includes "clinical terminology"

class TestAgeDerivation:
    test_age_derived_from_dob_in_profile_response
        # user with dob=1958-03-15, today=2026-03-06 → profile.age == 67

    test_age_updates_without_profile_change
        # same user, different "today" → age changes

class TestDashboardSafety:
    test_patient_overview_includes_derived_age_when_dob_set
        # user with dob=1958-03-15 → GET /api/patients/overview → response includes age

    test_null_optional_fields_do_not_crash_overview
        # patient with no height/weight/blood_type → GET /api/patients/overview → 200
        # response has summary.total_nodes >= 0

    test_null_optional_fields_do_not_crash_orchestrator
        # patient with no height/weight → POST /api/chat/query → 200 (no crash)
```

### F. Migration / Backward Compatibility Tests (6 tests)

```
tests/regression/test_profile_backward_compat.py

class TestBackwardCompatibility:
    test_legacy_user_without_profile_data_returns_200
        # user registered without dob/gender → GET /api/patients/profile → 200
        # response has null fields, onboarding_complete: false

    test_legacy_user_prompted_for_onboarding
        # user without onboarding_completed_at → login response includes
        # onboarding_complete: false

    test_existing_register_contract_unchanged
        # POST /api/auth/register with name+email+password → 200
        # access_token + refresh_token present (no new required fields)

    test_existing_login_contract_backward_compatible
        # POST /api/auth/login → 200
        # access_token + refresh_token present
        # new user field is additive (onboarding_complete)

    test_existing_patient_overview_unaffected
        # GET /api/patients/overview → same shape as before

    test_null_historical_records_remain_readable
        # user with null dob/gender/language → all routes return 200
        # no NoneType errors or crashes
```

### G. Profile CRUD Functional Tests (8 tests)

```
tests/functional/test_api_profile_onboarding.py

class TestProfileCRUD:
    test_get_profile_returns_all_fields
        # GET /api/patients/profile → 200
        # response contains dob, gender, language, literacy, age, onboarding_complete

    test_get_profile_masks_emergency_phone
        # emergency_contact_phone set → GET returns masked "+91****3210"

    test_put_profile_updates_single_field
        # PUT with only city="Mumbai" → 200, city updated

    test_put_profile_updates_multiple_fields
        # PUT with dob+gender+city → 200, all updated

    test_put_profile_invalid_field_returns_400
        # PUT with gender="invalid" → 400

    test_put_profile_returns_updated_profile
        # PUT with dob → 200, response includes age derived from new dob

    test_get_profile_without_auth_returns_401
        # no auth header → GET /api/patients/profile → 401

    test_put_profile_without_auth_returns_401
        # no auth header → PUT /api/patients/profile → 401
```

**Total: 67 test cases**

---

## SECTION 8 — API Contract Proposals

### 8.1 Registration Response (MODIFIED — additive)

**Endpoint:** `POST /api/auth/register`

**Request body:** Unchanged.

**Response body (updated):**
```json
{
    "access_token": "eyJ...",
    "refresh_token": "abc123...",
    "token_type": "bearer",
    "user": {
        "id": "uuid",
        "name": "Ramesh Kumar",
        "email": "ramesh@careorbit.dev",
        "onboarding_complete": false
    }
}
```

**Status codes:** 200 (success), 400 (weak password), 409 (duplicate email), 422 (missing required fields)

**Breaking change:** No. `user` object already exists in register response. `onboarding_complete` is additive.

### 8.2 Login Response (MODIFIED — additive)

**Endpoint:** `POST /api/auth/login`

**Request body:** Unchanged.

**Response body (updated):**
```json
{
    "access_token": "eyJ...",
    "refresh_token": "abc123...",
    "token_type": "bearer",
    "user": {
        "id": "uuid",
        "name": "Ramesh Kumar",
        "email": "ramesh@careorbit.dev",
        "preferred_language": "hi",
        "onboarding_complete": true
    }
}
```

**Status codes:** 200 (success), 401 (invalid credentials), 429 (rate limited)

**Breaking change:** No. `user` object was added in the Ramesh seed data work. `onboarding_complete` and `preferred_language` are additive.

### 8.3 Profile Update (NEW)

**Endpoint:** `PUT /api/patients/profile`

**Request body:**
```json
{
    "date_of_birth": "1958-03-15",
    "gender": "male",
    "preferred_language": "hi",
    "medical_literacy_level": "basic",
    "blood_type": "B+",
    "height_cm": 170.0,
    "weight_kg": 78.0,
    "city": "Durgapur",
    "state": "West Bengal",
    "country": "IN",
    "emergency_contact_name": "Priya Kumar",
    "emergency_contact_phone": "+919876543211"
}
```

All fields optional in body. Omitted fields are not modified.

**Response body:**
```json
{
    "profile": {
        "date_of_birth": "1958-03-15",
        "age": 67,
        "gender": "male",
        "preferred_language": "hi",
        "medical_literacy_level": "basic",
        "blood_type": "B+",
        "height_cm": 170.0,
        "weight_kg": 78.0,
        "city": "Durgapur",
        "state": "West Bengal",
        "country": "IN",
        "emergency_contact_name": "Priya Kumar",
        "emergency_contact_phone": "+91****3211"
    },
    "onboarding_complete": true
}
```

**Status codes:**
- 200: Success (partial or full update)
- 400: Validation error (invalid DOB, gender, etc.)
  ```json
  {"detail": "Invalid date format. Use YYYY-MM-DD"}
  ```
- 401: Not authenticated
- 403: Cannot update this patient's profile (RBAC)

**Breaking change:** No. New endpoint.

### 8.4 Profile Fetch (NEW)

**Endpoint:** `GET /api/patients/profile`

**Query params:** `patient_id` (optional, defaults to current user)

**Response body:**
```json
{
    "profile": {
        "date_of_birth": "1958-03-15",
        "age": 67,
        "gender": "male",
        "preferred_language": "hi",
        "medical_literacy_level": "basic",
        "blood_type": "B+",
        "height_cm": 170.0,
        "weight_kg": 78.0,
        "city": "Durgapur",
        "state": "West Bengal",
        "country": "IN",
        "emergency_contact_name": "Priya Kumar",
        "emergency_contact_phone": "+91****3211"
    },
    "onboarding_complete": true
}
```

**Status codes:** 200 (success), 401 (not authenticated), 403 (RBAC denied)

**Breaking change:** No. New endpoint.

### 8.5 Onboarding Status (OPTIONAL — included in login/profile responses)

Not a separate endpoint. The `onboarding_complete` boolean is included in:
- Login response → `user.onboarding_complete`
- Register response → `user.onboarding_complete`
- Profile GET response → `onboarding_complete`
- Profile PUT response → `onboarding_complete`

Additionally, the `X-Onboarding-Required: true` response header is added by middleware when onboarding is incomplete.

---

## SECTION 9 — Suggested File Layout

### New Test Files

| File | Category | Tests | Purpose |
|------|----------|-------|---------|
| `tests/unit/test_profile_validators.py` | Unit | 16 | Validate all profile field validators in isolation |
| `tests/functional/test_api_profile_onboarding.py` | Functional | 27 | Profile CRUD + onboarding completion API contracts |
| `tests/security/test_profile_rbac.py` | Security | 8 | Profile access control, encryption, audit bypass |
| `tests/business_logic/test_profile_personalization.py` | Business | 10 | Language, literacy, age derivation, dashboard safety |
| `tests/regression/test_profile_backward_compat.py` | Regression | 6 | Backward compatibility with existing API contracts |

### New Source Files

| File | Purpose |
|------|---------|
| `utils/profile_validators.py` | Pure validation functions for all profile fields |
| `api/middleware/onboarding.py` | Lightweight middleware adding `X-Onboarding-Required` header |

### Existing Files to Update

| File | Changes |
|------|---------|
| `api/routes/patients.py` | Add `PUT /api/patients/profile`, `GET /api/patients/profile` routes |
| `api/routes/auth.py` | Add `onboarding_complete` to login/register responses; add `medical_literacy_level`, `onboarding_completed_at` to `_users_store` entries |
| `main.py` | Register onboarding middleware (if implemented as ASGI middleware) |
| `db/seed_demo.py` | Add `medical_literacy_level: "basic"`, `onboarding_completed_at: <timestamp>` to Ramesh's profile |
| `tests/conftest.py` | **DO NOT MODIFY** existing fixtures. New fixtures go in test files or a new `tests/helpers/profile_fixtures.py` |
| `database/schema.sql` | Add `medical_literacy_level` and `onboarding_completed_at` columns to `users`; add `height_cm`, `weight_kg`, `country`, `emergency_contact_name`, `emergency_contact_phone` to `patient_profiles` |

---

## SECTION 10 — Priority and Delivery Plan

### Phase 1: Contracts + Validators (2-3 days)

| Task | Type | Details |
|------|------|---------|
| Create `utils/profile_validators.py` | Dev | All 8 validator functions + `derive_age` |
| Create `tests/unit/test_profile_validators.py` | Test | 16 unit tests — all GREEN before moving on |
| Define `ProfileUpdateRequest` model | Dev | Pydantic model in `api/routes/patients.py` |
| Update `database/schema.sql` | Dev | Add new columns |

**Dependencies:** None.
**Blockers:** None.
**Release risk:** Low — no API changes, no user-facing impact.

### Phase 2: API Behavior (3-4 days)

| Task | Type | Details |
|------|------|---------|
| Implement `PUT /api/patients/profile` | Dev | Route with validation, store update, onboarding check |
| Implement `GET /api/patients/profile` | Dev | Route with RBAC, masked phone, derived age |
| Update login/register responses | Dev | Add `onboarding_complete` field |
| Create `tests/functional/test_api_profile_onboarding.py` | Test | 27 functional tests — all GREEN |
| Create `tests/regression/test_profile_backward_compat.py` | Test | 6 regression tests — verify no breakage |
| Update seed demo data | Dev | Add literacy + onboarding_completed_at for Ramesh |

**Dependencies:** Phase 1 (validators must exist).
**Blockers:** None.
**Release risk:** Medium — new endpoints, but existing routes unchanged.

### Phase 3: Security / Audit / Encryption (2-3 days)

| Task | Type | Details |
|------|------|---------|
| Implement profile RBAC | Dev | Caregiver access restrictions on PUT |
| Implement emergency phone encryption | Dev | `pgp_sym_encrypt` in profile update SQL |
| Implement onboarding middleware | Dev | `X-Onboarding-Required` header |
| Add audit events | Dev | `PROFILE_UPDATE`, `PROFILE_ONBOARDING_COMPLETE` |
| Create `tests/security/test_profile_rbac.py` | Test | 8 security tests — all GREEN |

**Dependencies:** Phase 2 (routes must exist).
**Blockers:** None.
**Release risk:** Medium — RBAC changes could affect caregiver flows if not careful.

### Phase 4: E2E / Business Logic / Regression (2-3 days)

| Task | Type | Details |
|------|------|---------|
| Create `tests/business_logic/test_profile_personalization.py` | Test | 10 business logic tests |
| Create frontend onboarding page | Dev | `/onboarding` page with form for mandatory fields |
| Update frontend to check `onboarding_complete` | Dev | Redirect to `/onboarding` if false |
| Full regression run | Test | Verify all 322 + 67 = 389 tests pass |

**Dependencies:** Phase 3.
**Blockers:** Frontend routing changes.
**Release risk:** Low — no backend contract changes.

### Timeline Summary

| Phase | Duration | Cumulative | Tests Added |
|-------|----------|-----------|-------------|
| Phase 1 | 2-3 days | Days 1-3 | +16 unit |
| Phase 2 | 3-4 days | Days 4-7 | +33 functional/regression |
| Phase 3 | 2-3 days | Days 8-10 | +8 security |
| Phase 4 | 2-3 days | Days 11-13 | +10 business logic |
| **Total** | **10-13 days** | | **+67 tests** |

---

## SECTION 11 — Risks / Ambiguities

### 11.1 Registration vs First-Login Onboarding

**Ambiguity:** The prompt asks to compare both options but the current test suite (`test_register_success_returns_tokens`) registers with only name/email/password. Making DOB mandatory at registration would break this test.

**Resolution:** Option B (first-login onboarding) is recommended. If Option A is preferred despite test breakage, 3 existing tests need updating.

### 11.2 Gender Field Semantics

**Ambiguity:** "Prefer not to say" is listed as an option, but it's unclear how the AI pipeline should handle it. Should it:
- Omit gender from all prompts? (safest)
- Use a generic/neutral assumption? (potentially inaccurate)
- Ask the user during relevant interactions? (UX overhead)

**Resolution:** Omit gender from AI prompts when `prefer_not_to_say`. Use unisex lab reference ranges. Document this behavior.

### 11.3 Medical Literacy Level Strictness

**Ambiguity:** Should `medical_literacy_level` be:
- A hard enum (only 3 values)? → Simpler, deterministic.
- A soft preference that AI interprets flexibly? → More natural, harder to test.

**Resolution:** Hard enum with 3 values. Easier to test deterministically. The AI prompt maps each level to a specific instruction:
- `basic` → "Explain in simple, everyday language. Avoid medical jargon."
- `intermediate` → "Use medical terms but provide brief explanations."
- `advanced` → "Use full clinical terminology and reference ranges."

### 11.4 Emergency Contact — MVP or Optional?

**Ambiguity:** The prompt lists emergency contact as "optional / nice-to-have" but the schema already has `emergency_contact BYTEA` in `patient_profiles`.

**Resolution:** Keep as optional. Do NOT make it a mandatory onboarding field. The existing encrypted column can be reused. Add a separate `emergency_contact_name` field alongside.

### 11.5 Should Onboarding Block Features?

**Ambiguity:** Should an incomplete profile prevent the user from uploading documents, chatting, or viewing medications?

**Resolution:** No hard block. The `X-Onboarding-Required: true` header is advisory. The frontend handles the UX flow. API endpoints remain functional for all users regardless of onboarding status. Rationale:
- Blocking would break existing tests
- Users might want to explore before committing personal data
- Caregivers might add documents before the patient completes onboarding

### 11.6 In-Memory Store Lifetime

**Risk:** All profile data is stored in `_users_store` (a Python dict). Server restarts lose all data. This is a known limitation of the current MVP architecture (no real PostgreSQL).

**Mitigation:** Seed demo data (Ramesh) includes complete profile. Other users lose data on restart. This is acceptable for MVP. Document clearly.

### 11.7 Concurrent Profile Updates

**Risk:** Two simultaneous PUT requests could race. The in-memory store has no locking.

**Mitigation:** Not a concern for MVP (single-user demo). When PostgreSQL is connected, use `UPDATE ... SET ... WHERE user_id = :uid` (atomic row update).

### 11.8 DOB Privacy in India

**Risk:** In India, date of birth combined with name can be a strong identifier (Aadhaar linkage). Some users may be reluctant to share DOB.

**Mitigation:** DOB is stored as plaintext DATE (needed for age derivation) but access-controlled via RBAC. Consider adding a "year of birth only" option in future iterations. For MVP, full DOB is required for clinical accuracy.

---

## SECTION 12 — Final Recommendation

### 1. Recommended Product Path

**Option B: First-login onboarding.** Keep registration lean (name + email + password). Prompt for mandatory fields (DOB, gender, language, literacy) after first login via a dedicated onboarding screen. Advisory header (`X-Onboarding-Required`), no hard API gate.

### 2. Recommended API Path

| Priority | Endpoint | Action |
|----------|----------|--------|
| P0 | `PUT /api/patients/profile` | Core profile update with validation |
| P0 | `GET /api/patients/profile` | Profile retrieval with derived age |
| P1 | Login response update | Add `onboarding_complete` flag |
| P1 | Register response update | Add `onboarding_complete: false` |
| P2 | Onboarding middleware | `X-Onboarding-Required` header |
| P3 | Frontend onboarding page | `/onboarding` with form |

### 3. Recommended Test Rollout Order

| Order | File | Count | Gate |
|-------|------|-------|------|
| 1 | `tests/unit/test_profile_validators.py` | 16 | CI |
| 2 | `tests/functional/test_api_profile_onboarding.py` | 27 | CI |
| 3 | `tests/regression/test_profile_backward_compat.py` | 6 | CI |
| 4 | `tests/security/test_profile_rbac.py` | 8 | CI |
| 5 | `tests/business_logic/test_profile_personalization.py` | 10 | CI |

### 4. Minimum CI-Gating Subset

The following tests MUST pass in CI before any merge:

- All 16 validator unit tests (Phase 1 gate)
- `test_register_does_not_require_mandatory_onboarding_fields` (backward compat)
- `test_existing_register_contract_unchanged` (backward compat)
- `test_existing_login_contract_backward_compatible` (backward compat)
- `test_profile_completion_with_all_mandatory_fields_succeeds` (core flow)
- `test_patient_cannot_update_other_patient_profile` (security)
- `test_unauthenticated_profile_access_rejected` (security)
- All existing 322 passing tests (regression)

### 5. What Should Be Deferred

| Feature | Reason | Defer To |
|---------|--------|----------|
| Emergency contact encryption in real PostgreSQL | No real DB yet | Azure DB connection phase |
| `emergency_contact_name` encryption | Low sensitivity for MVP | Phase 2 security hardening |
| Caregiver notification on profile completion | No email service connected | Azure Email connection phase |
| "Year of birth only" privacy option | Edge case, complicates age derivation | Post-MVP feedback phase |
| Profile photo upload | Not in requirements | Future sprint |
| BMI calculation from height/weight | Nice-to-have derived metric | Post-MVP |
| Onboarding analytics (completion rate, drop-off) | Requires analytics infrastructure | Post-MVP |

---

## Appendix A — Enum Reference

```python
VALID_GENDERS = {"male", "female", "other", "prefer_not_to_say"}
VALID_LANGUAGES = {"en", "hi", "bn", "ta", "te", "mr", "gu", "kn", "ml"}
VALID_LITERACY_LEVELS = {"basic", "intermediate", "advanced"}
VALID_BLOOD_TYPES = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
```

## Appendix B — Age Derivation Reference Implementation

```python
from datetime import date

def derive_age(dob: date, reference_date: date = None) -> int:
    today = reference_date or date.today()
    age = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        age -= 1
    return age
```

This is the correct implementation (not `days / 365.25`) because it handles leap years and month boundaries accurately. `derive_age(date(1958, 3, 15), date(2026, 3, 14))` → 67. `derive_age(date(1958, 3, 15), date(2026, 3, 15))` → 68.
