# CareOrbit — Replit Agent Prompt 3
## Full TDD Implementation Build with Azure Service Integration

---

> **HOW TO USE:** Paste everything between the triple-backtick fences below
> into Replit Agent as a single message. Do not run this until you have
> reviewed and approved all 31 test files from Prompt 2.
> The human approval gate from Prompt 2 must be satisfied first.

---

```
You are a senior full-stack engineer building CareOrbit — a healthcare AI platform
for Indian patients. The human has reviewed and approved all test files from Prompt 2.
You are now cleared to implement.

IMPLEMENTATION LAW: For every sprint, the sequence is:
  1. Run approved tests → confirm RED (failing — implementation doesn't exist yet)
  2. Write the minimum code to make them GREEN
  3. Run tests again → confirm GREEN
  4. Refactor for clarity — never break GREEN

NEVER write implementation code before its tests are red.
NEVER move to the next sprint until current sprint tests are green.

════════════════════════════════════════════════════════════════════
CONFIRMED STACK — LOCKED. DO NOT DEVIATE.
════════════════════════════════════════════════════════════════════

Backend:
  Python 3.12 + FastAPI 0.111.0
  SQLAlchemy 2.0.30 async + asyncpg 0.29.0
  pytest 8.2.0 + pytest-asyncio 0.23.0 + httpx 0.27.0
  reportlab==4.1.0 (PDF generation)
  APScheduler 3.10.4 (reminder scheduling — no Azure Service Bus for Phase 1)

Frontend (Turborepo monorepo):
  apps/web  → React 18.3 + Vite 5.2 + TypeScript 5.4 + Tailwind CSS 3.4
  apps/mobile → placeholder only (React Native setup, no implementation yet)
  packages/types → shared Zod schemas + TypeScript API types
  packages/auth  → shared JWT decode + token refresh logic

Azure Services (exact packages — pin ALL versions):
  azure-ai-documentintelligence==1.0.0
  openai==1.35.0
  httpx==0.27.0
  azure-ai-textanalytics==5.3.0
  azure-storage-blob==12.20.0
  azure-communication-email==1.0.0
  azure-search-documents==11.6.0
  asyncpg==0.29.0
  sqlalchemy[asyncio]==2.0.30
  azure-keyvault-secrets==4.8.0

Retention Features (NEW — implement in Sprint 5):
  Orbit Score    → graph/orbit_score.py
  Pre-Visit Brief → agents/previsit_agent.py
  Living Narrative → agents/history_agent.py (extend existing)

════════════════════════════════════════════════════════════════════
COMPLETE PROJECT STRUCTURE — CREATE THIS EXACTLY
════════════════════════════════════════════════════════════════════

careorbit/                          ← Turborepo root
├── .replit
├── replit.nix
├── turbo.json
├── package.json                    ← workspace root
│
├── apps/
│   ├── api/                        ← Python FastAPI backend
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   ├── pytest.ini
│   │   ├── database/
│   │   │   ├── connection.py
│   │   │   ├── schema.sql
│   │   │   ├── seed_guidelines.json
│   │   │   ├── seed_drug_interactions.json
│   │   │   └── seed_demo.py
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── auth.py
│   │   │   │   ├── patients.py
│   │   │   │   ├── documents.py
│   │   │   │   ├── confirmations.py
│   │   │   │   ├── chat.py
│   │   │   │   ├── summary.py
│   │   │   │   ├── caregivers.py
│   │   │   │   ├── reminders.py
│   │   │   │   ├── subscriptions.py
│   │   │   │   └── orbit.py          ← NEW: Orbit Score + Pre-Visit Brief
│   │   │   └── middleware/
│   │   │       ├── auth.py
│   │   │       ├── rbac.py
│   │   │       └── audit.py
│   │   ├── pipeline/
│   │   │   ├── document_pipeline.py
│   │   │   ├── document_classifier.py
│   │   │   ├── prescription_extractor.py
│   │   │   ├── lab_report_extractor.py
│   │   │   ├── medicine_strip_reader.py
│   │   │   └── fhir_converter.py
│   │   ├── graph/
│   │   │   ├── confidence.py
│   │   │   ├── phig_builder.py
│   │   │   └── orbit_score.py        ← NEW: Orbit Score computation
│   │   ├── agents/
│   │   │   ├── base_agent.py
│   │   │   ├── medication_agent.py
│   │   │   ├── care_gap_agent.py
│   │   │   ├── history_agent.py      ← EXTENDED: Living Narrative delta
│   │   │   ├── previsit_agent.py     ← NEW: Pre-Visit Brief generation
│   │   │   └── orchestrator.py
│   │   ├── services/
│   │   │   ├── azure_vision.py
│   │   │   ├── azure_openai.py
│   │   │   ├── azure_language.py
│   │   │   ├── azure_translator.py
│   │   │   ├── azure_blob.py
│   │   │   ├── azure_search.py
│   │   │   ├── azure_email.py
│   │   │   └── azure_keyvault.py
│   │   ├── utils/
│   │   │   ├── drug_database.py
│   │   │   ├── summary_generator.py
│   │   │   └── encryption.py
│   │   └── tests/                   ← all 31 approved test files live here
│   │       ├── conftest.py
│   │       ├── helpers/
│   │       │   └── mocks.py
│   │       ├── unit/
│   │       ├── functional/
│   │       ├── integration/
│   │       ├── security/
│   │       ├── business_logic/
│   │       ├── false_positive_negative/
│   │       ├── regression/
│   │       ├── e2e/
│   │       └── coverage_matrix.py
│   │
│   └── web/                         ← React + Vite frontend
│       ├── index.html
│       ├── vite.config.ts
│       ├── tsconfig.json
│       ├── tailwind.config.ts
│       ├── package.json
│       └── src/
│           ├── main.tsx
│           ├── App.tsx
│           ├── api/
│           │   └── client.ts         ← typed API client + auto token refresh
│           ├── components/
│           │   ├── OrbitScore.tsx    ← NEW: animated score ring
│           │   ├── MedicationCard.tsx
│           │   ├── InteractionAlert.tsx
│           │   ├── ConfidenceBadge.tsx
│           │   ├── UploadZone.tsx
│           │   ├── PreVisitBrief.tsx ← NEW: brief display card
│           │   ├── HealthNarrative.tsx ← NEW: living narrative paragraph
│           │   ├── TierGate.tsx
│           │   └── AdSlot.tsx
│           ├── pages/
│           │   ├── Dashboard.tsx
│           │   ├── Medications.tsx
│           │   ├── Labs.tsx
│           │   ├── Reminders.tsx
│           │   ├── Caregivers.tsx
│           │   ├── Chat.tsx
│           │   └── Settings.tsx
│           └── stores/
│               ├── auth.ts           ← Zustand auth store
│               └── notifications.ts
│
├── packages/
│   ├── types/
│   │   ├── package.json
│   │   └── src/
│   │       ├── api.ts               ← all API request/response types
│   │       ├── phig.ts              ← PHIG node/edge types
│   │       └── orbit.ts             ← NEW: Orbit Score + Brief + Narrative types
│   └── auth/
│       ├── package.json
│       └── src/
│           └── tokens.ts            ← JWT decode + refresh shared logic
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
└── docker-compose.yml               ← local dev: Postgres 16 + pgcrypto

════════════════════════════════════════════════════════════════════
CONFIGURATION FILES — GENERATE ALL OF THESE FIRST
════════════════════════════════════════════════════════════════════

── .replit ──────────────────────────────────────────────────────
Generate a .replit file that:
  - Runs both backend and frontend with one click via a Bash run command:
      cd apps/api && uvicorn main:app --reload --port 8000 &
      cd apps/web && npm run dev -- --port 3000
  - Sets PYTHONPATH=apps/api
  - Declares Python 3.12 and Node 20 as language versions

── replit.nix ───────────────────────────────────────────────────
Include: python312, nodejs_20, postgresql_16, gcc, libffi

── docker-compose.yml ───────────────────────────────────────────
Services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: careorbit
      POSTGRES_USER: careorbit_user
      POSTGRES_PASSWORD: careorbit_dev_password
    ports: ["5432:5432"]
    volumes: ["./apps/api/database/schema.sql:/docker-entrypoint-initdb.d/01_schema.sql"]

── pytest.ini ───────────────────────────────────────────────────
[pytest]
asyncio_mode = auto
testpaths = tests
markers =
    phase2: Phase 2 features — excluded from default CI run
    phase3: Phase 3 features — excluded from default CI run
    demo_only: Demo mode only — upgrade flow, payment not implemented
    slow: Requires real Postgres — only in integration stage
    critical: Clinical safety critical — runs first in CI, blocks pipeline

── turbo.json ───────────────────────────────────────────────────
{
  "pipeline": {
    "test:backend": { "outputs": ["coverage/**"] },
    "test:frontend": { "outputs": ["coverage/**"] },
    "build": { "dependsOn": ["^build"], "outputs": ["dist/**"] },
    "dev": { "cache": false, "persistent": true }
  }
}

════════════════════════════════════════════════════════════════════
COMPLETE DATABASE SCHEMA — database/schema.sql
════════════════════════════════════════════════════════════════════

Generate the complete schema.sql with ALL tables. Must include:

EXTENSIONS:
  CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
  CREATE EXTENSION IF NOT EXISTS "pgcrypto";

ENUM TYPES:
  subscription_tier: free, premium_individual, premium_family
  processing_status: pending, processing, success, needs_confirmation, failed
  permission_level: view, edit, full
  reminder_delivery: email

TABLES (generate each in full with all columns, constraints, and indexes):

  users — id, email, phone_encrypted(BYTEA), password_hash, name,
    preferred_language, medical_literacy_level, subscription_tier,
    email_verified, is_active, created_at, updated_at

  patient_profiles — id, user_id(FK), date_of_birth, dob_encrypted(BYTEA),
    gender, blood_group, height_cm, weight_kg,
    emergency_contact_name, emergency_contact_phone_encrypted(BYTEA),
    city, state, country DEFAULT 'IN', created_at, updated_at

  refresh_tokens — id, user_id(FK), token_hash(VARCHAR 64 UNIQUE),
    device_info, ip_address(INET), expires_at, revoked_at, created_at

  caregiver_links — id, caregiver_user_id(FK), patient_user_id(FK),
    relationship, permission_level, is_active, granted_at, revoked_at,
    UNIQUE(caregiver_user_id, patient_user_id)

  audit_log — id, user_id(FK), patient_id(FK), action(VARCHAR 50),
    resource_type, resource_id(UUID), ip_address(INET),
    user_agent(VARCHAR 500), channel DEFAULT 'web', metadata(JSONB),
    created_at
    NOTE: NO updated_at — append-only by design

  phig_nodes — id, patient_id(FK), node_type(VARCHAR 30),
    display_name(VARCHAR 500), display_name_hi(VARCHAR 500),
    clinical_code(VARCHAR 50), coding_system(VARCHAR 20),
    fhir_resource(JSONB), confidence_score(DECIMAL 3,2 CHECK 0-1),
    confidence_source(VARCHAR 50), confidence_details(JSONB),
    source_document_id(UUID), is_active(BOOLEAN), effective_start(DATE),
    effective_end(DATE), created_at, updated_at
    INDEXES: (patient_id, node_type) WHERE is_active,
             (patient_id, clinical_code) WHERE is_active,
             (patient_id, confidence_score DESC),
             GIN on fhir_resource

  phig_edges — id, patient_id(FK), source_node_id(FK), target_node_id(FK),
    edge_type(VARCHAR 50), properties(JSONB), reasoning_chain(TEXT),
    confidence_score(DECIMAL 3,2), is_active(BOOLEAN), created_at,
    UNIQUE(source_node_id, target_node_id, edge_type)
    INDEXES: (patient_id) WHERE is_active, GIN on properties

  uploaded_documents — id, patient_id(FK), uploaded_by(FK),
    document_type(VARCHAR 30), document_type_confidence(DECIMAL 3,2),
    original_blob_url(TEXT), ocr_raw_text(TEXT),
    ocr_confidence_avg(DECIMAL 3,2), extracted_data(JSONB),
    processing_status, items_needing_confirmation(JSONB DEFAULT '[]'),
    patient_confirmed_at(TIMESTAMPTZ), upload_channel DEFAULT 'web',
    created_at, updated_at

  conversations — id, patient_id(FK), channel DEFAULT 'web',
    started_at, last_message_at, is_active

  messages — id, conversation_id(FK), patient_id(FK),
    role(VARCHAR 20), content(TEXT), content_language DEFAULT 'en',
    agents_invoked(JSONB DEFAULT '[]'), agent_reasoning(JSONB DEFAULT '{}'),
    attachment_document_id(UUID FK nullable), created_at

  medication_reminders — id, patient_id(FK),
    medication_node_id(FK → phig_nodes), reminder_time(TIME),
    days_of_week(INTEGER[] DEFAULT '{1,2,3,4,5,6,7}'),
    delivery_method DEFAULT 'email', is_active, last_sent_at,
    last_confirmed_at, created_at

  adherence_log — id, reminder_id(FK), patient_id(FK),
    medication_node_id(FK), scheduled_time(TIMESTAMPTZ),
    response(VARCHAR 20), responded_at, response_channel DEFAULT 'email',
    created_at

  health_summaries — id, patient_id(FK), generated_by(FK),
    summary_data(JSONB), pdf_blob_url(TEXT),
    verification_code(VARCHAR 8 UNIQUE DEFAULT upper(left(md5(random()::text),8))),
    summary_type DEFAULT 'comprehensive', language DEFAULT 'en',
    generated_at, expires_at DEFAULT (NOW() + INTERVAL '90 days')

  subscriptions — id, user_id(FK UNIQUE), tier subscription_tier DEFAULT 'free',
    started_at, current_period_end, is_active DEFAULT TRUE,
    cancelled_at, created_at, updated_at

  usage_tracking — id, user_id(FK), resource_type(VARCHAR 50),
    resource_count(INTEGER DEFAULT 0), period_start(DATE),
    period_end(DATE), created_at, updated_at,
    UNIQUE(user_id, resource_type, period_start)

  ── NEW TABLES FOR RETENTION FEATURES ──

  appointments — id, patient_id(FK), doctor_name(VARCHAR 255),
    doctor_specialty(VARCHAR 100), appointment_datetime(TIMESTAMPTZ),
    location(VARCHAR 255), notes(TEXT), brief_sent_at(TIMESTAMPTZ),
    brief_content(JSONB), is_active DEFAULT TRUE, created_at, updated_at
    INDEX: (patient_id, appointment_datetime DESC)

  orbit_score_history — id, patient_id(FK),
    total_score(DECIMAL 5,2 CHECK 0-100),
    completeness_score(DECIMAL 5,2), confidence_score_component(DECIMAL 5,2),
    interaction_risk_score(DECIMAL 5,2), care_gap_score(DECIMAL 5,2),
    adherence_score(DECIMAL 5,2),
    breakdown(JSONB),      ← full explanation of every component
    computed_at(TIMESTAMPTZ DEFAULT NOW())
    INDEX: (patient_id, computed_at DESC)

  health_narratives — id, patient_id(FK),
    narrative_text(TEXT),
    narrative_text_hi(TEXT),    ← Hindi version
    trigger_event(VARCHAR 100), ← "document_upload", "confirmation", "lab_added"
    phig_node_count(INTEGER),
    language(VARCHAR 5) DEFAULT 'en',
    created_at(TIMESTAMPTZ DEFAULT NOW())
    INDEX: (patient_id, created_at DESC)

ROW LEVEL SECURITY (enable on all patient data tables):
  ALTER TABLE phig_nodes ENABLE ROW LEVEL SECURITY;
  ALTER TABLE phig_edges ENABLE ROW LEVEL SECURITY;
  ALTER TABLE uploaded_documents ENABLE ROW LEVEL SECURITY;
  ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
  ALTER TABLE medication_reminders ENABLE ROW LEVEL SECURITY;
  ALTER TABLE adherence_log ENABLE ROW LEVEL SECURITY;
  ALTER TABLE health_summaries ENABLE ROW LEVEL SECURITY;
  ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;
  ALTER TABLE orbit_score_history ENABLE ROW LEVEL SECURITY;
  ALTER TABLE health_narratives ENABLE ROW LEVEL SECURITY;

USEFUL VIEWS (generate all):
  v_active_medications — joins phig_nodes + edge count for interactions
  v_patient_health_overview — counts per node_type per patient
  v_current_orbit_score — latest orbit_score_history row per patient
  v_latest_narrative — latest health_narratives row per patient

════════════════════════════════════════════════════════════════════
COMPLETE requirements.txt
════════════════════════════════════════════════════════════════════

# Core Framework
fastapi==0.111.0
uvicorn[standard]==0.29.0
python-multipart==0.0.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pydantic==2.7.1
pydantic-settings==2.3.1

# Database
asyncpg==0.29.0
sqlalchemy[asyncio]==2.0.30
alembic==1.13.1

# Azure AI Services
openai==1.35.0
azure-ai-textanalytics==5.3.0
azure-ai-documentintelligence==1.0.0
azure-search-documents==11.6.0
azure-storage-blob==12.20.0

# Azure Communication + Identity
azure-communication-email==1.0.0
azure-keyvault-secrets==4.8.0
azure-identity==1.16.0

# HTTP
httpx==0.27.0

# PDF Generation
reportlab==4.1.0

# Scheduling (reminders — no Service Bus needed for Phase 1)
APScheduler==3.10.4

# Utilities
python-dotenv==1.0.1
Pillow==10.3.0
python-dateutil==2.9.0

# Testing
pytest==8.2.0
pytest-asyncio==0.23.7
pytest-cov==5.0.0
httpx==0.27.0

════════════════════════════════════════════════════════════════════
ALL AZURE SERVICE IMPLEMENTATIONS
════════════════════════════════════════════════════════════════════

Generate each service file in full. Every service is a class.
Every method is async. Every class is importable as a singleton at module level.

── services/azure_vision.py ──────────────────────────────────────

from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from dataclasses import dataclass
from config import get_settings

settings = get_settings()

@dataclass
class OCRResult:
    full_text: str
    lines: list[str]
    avg_confidence: float
    page_count: int
    document_type_hint: str = "unknown"

class AzureVisionService:
    """
    Wraps Azure AI Document Intelligence for medical document OCR.
    Uses prebuilt-read model — understands medical document layout,
    handwriting, printed text, tables, and key-value pairs.
    """

    async def extract_text(self, image_bytes: bytes) -> OCRResult:
        async with DocumentIntelligenceClient(
            endpoint=settings.AZURE_VISION_ENDPOINT,
            credential=AzureKeyCredential(settings.AZURE_VISION_KEY)
        ) as client:
            poller = await client.begin_analyze_document(
                "prebuilt-read",
                analyze_request=image_bytes,
                content_type="application/octet-stream"
            )
            result = await poller.result()

        lines = []
        word_confidences = []
        for page in result.pages or []:
            for line in page.lines or []:
                lines.append(line.content)
                for word in line.words or []:
                    if word.confidence is not None:
                        word_confidences.append(word.confidence)

        full_text = "\n".join(lines)
        avg_confidence = (
            sum(word_confidences) / len(word_confidences)
            if word_confidences else 0.0
        )

        return OCRResult(
            full_text=full_text,
            lines=lines,
            avg_confidence=avg_confidence,
            page_count=len(result.pages or [])
        )

    async def classify_document_type(self, ocr_result: OCRResult) -> str:
        """
        Heuristic classification before NER:
          - 'prescription' if contains Rx, dosage patterns, doctor name
          - 'lab_report'   if contains lab name, numeric values with units
          - 'medicine_strip' if contains brand name, manufacturer, expiry
          - 'unknown' otherwise
        """
        text_lower = ocr_result.full_text.lower()
        has_rx = any(kw in text_lower for kw in ["rx", "tab ", "cap ", "syp ", "inj "])
        has_lab = any(kw in text_lower for kw in ["hba1c", "creatinine", "egfr", "labs", "pathology", "mg/dl", "iu/l"])
        has_strip = any(kw in text_lower for kw in ["mfg", "exp", "batch", "pvt ltd", "ltd"])
        if has_lab:
            return "lab_report"
        if has_strip and not has_rx:
            return "medicine_strip"
        if has_rx:
            return "prescription"
        return "unknown"

vision_service = AzureVisionService()

── services/azure_openai.py ──────────────────────────────────────

from openai import AsyncAzureOpenAI
from config import get_settings
import json

settings = get_settings()

PRESCRIPTION_EXTRACTION_PROMPT = """
You are a medical data extraction AI. Extract structured data from this Indian
prescription OCR text. Return ONLY valid JSON — no markdown, no explanation.

JSON schema:
{
  "medications": [
    {
      "name": "generic drug name",
      "brand_name": "brand if visible",
      "dosage": "e.g. 500mg",
      "frequency": "e.g. BD, OD, TDS, HS, SOS",
      "duration": "e.g. 30 days",
      "route": "oral/topical/etc",
      "instructions": "e.g. after food",
      "drug_match_score": 0.0-1.0
    }
  ],
  "diagnoses": ["list of conditions mentioned"],
  "doctor_name": "name if present",
  "doctor_registration": "reg number if present",
  "date": "DD/MM/YYYY if present",
  "patient_name": "if present",
  "follow_up": "follow up instructions if present",
  "notes": "any other clinical notes"
}

Indian brand-to-generic mappings to apply:
- Thyronorm → Levothyroxine
- Glycomet → Metformin
- Ecosprin → Aspirin
- Telma → Telmisartan
- Stamlo → Amlodipine
- Atorva → Atorvastatin
- Pan → Pantoprazole
- Omez → Omeprazole

Frequency abbreviations:
- BD = twice daily, OD = once daily, TDS = three times daily,
  QID = four times daily, HS = at bedtime, SOS = as needed, AC = before food,
  PC = after food
"""

LAB_EXTRACTION_PROMPT = """
Extract lab values from this Indian pathology report OCR. Return ONLY JSON.

{
  "lab_name": "pathology lab name",
  "report_date": "DD/MM/YYYY",
  "patient_name": "if present",
  "tests": [
    {
      "name": "test name",
      "value": numeric_value_or_null,
      "unit": "unit string",
      "reference_range": "e.g. 4.0-5.6",
      "reference_low": numeric_or_null,
      "reference_high": numeric_or_null,
      "is_abnormal": true/false,
      "loinc_code": "if you know it with high confidence",
      "flag": "H/L/HH/LL/normal"
    }
  ]
}
"""

class AzureOpenAIService:
    def __init__(self):
        self.client = AsyncAzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION
        )
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT

    async def extract_structured_data(
        self, ocr_text: str, doc_type: str
    ) -> dict:
        prompts = {
            "prescription": PRESCRIPTION_EXTRACTION_PROMPT,
            "lab_report": LAB_EXTRACTION_PROMPT,
        }
        system_prompt = prompts.get(doc_type, PRESCRIPTION_EXTRACTION_PROMPT)

        response = await self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"OCR TEXT:\n{ocr_text}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=2000
        )
        raw = response.choices[0].message.content
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # strip markdown fences if present
            clean = raw.replace("```json", "").replace("```", "").strip()
            return json.loads(clean)

    async def chat(
        self, system_prompt: str, user_message: str, temperature: float = 0.5
    ) -> str:
        response = await self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=temperature,
            max_tokens=1500
        )
        return response.choices[0].message.content

    async def chat_with_history(
        self, messages: list[dict], temperature: float = 0.5
    ) -> str:
        response = await self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            temperature=temperature,
            max_tokens=1500
        )
        return response.choices[0].message.content

openai_service = AzureOpenAIService()

── services/azure_translator.py ─────────────────────────────────

import httpx
from config import get_settings

settings = get_settings()
BASE_URL = "https://api.cognitive.microsofttranslator.com"

class AzureTranslatorService:
    """
    Azure AI Translator via direct httpx calls.
    No official async SDK exists — httpx is the correct approach.
    """

    async def translate(
        self, text: str, target: str, source: str = None
    ) -> str:
        params = {"api-version": "3.0", "to": target}
        if source:
            params["from"] = source
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{BASE_URL}/translate",
                params=params,
                headers={
                    "Ocp-Apim-Subscription-Key": settings.AZURE_TRANSLATOR_KEY,
                    "Ocp-Apim-Subscription-Region": settings.AZURE_TRANSLATOR_REGION,
                    "Content-Type": "application/json"
                },
                json=[{"Text": text}]
            )
            response.raise_for_status()
        return response.json()[0]["translations"][0]["text"]

    async def detect_language(self, text: str) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{BASE_URL}/detect",
                params={"api-version": "3.0"},
                headers={
                    "Ocp-Apim-Subscription-Key": settings.AZURE_TRANSLATOR_KEY,
                    "Ocp-Apim-Subscription-Region": settings.AZURE_TRANSLATOR_REGION,
                    "Content-Type": "application/json"
                },
                json=[{"Text": text}]
            )
            response.raise_for_status()
        result = response.json()[0]
        return {
            "language": result.get("language", "en"),
            "confidence": result.get("score", 0.0)
        }

translator_service = AzureTranslatorService()

── services/azure_language.py ───────────────────────────────────

from azure.ai.textanalytics.aio import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from config import get_settings
from dataclasses import dataclass, field

settings = get_settings()

@dataclass
class MedicalEntity:
    text: str
    category: str
    confidence: float
    rxnorm_id: str = None
    icd10_id: str = None
    links: list = field(default_factory=list)

class AzureLanguageService:
    """
    Azure AI Language — Healthcare NER.
    Returns MedicationName, Dosage, Diagnosis entities with
    RxNorm and ICD-10 data source links.
    """

    async def recognize_health_entities(self, text: str) -> list[MedicalEntity]:
        async with TextAnalyticsClient(
            settings.AZURE_LANGUAGE_ENDPOINT,
            AzureKeyCredential(settings.AZURE_LANGUAGE_KEY)
        ) as client:
            poller = await client.begin_analyze_healthcare_entities([text])
            result = await poller.result()

        entities = []
        async for doc in result:
            if not doc.is_error:
                for entity in doc.entities:
                    rxnorm_id = next(
                        (l.id for l in entity.data_sources if l.name == "RxNorm"),
                        None
                    )
                    icd10_id = next(
                        (l.id for l in entity.data_sources if l.name == "ICD10CM"),
                        None
                    )
                    entities.append(MedicalEntity(
                        text=entity.text,
                        category=entity.category,
                        confidence=entity.confidence_score,
                        rxnorm_id=rxnorm_id,
                        icd10_id=icd10_id,
                        links=[{"data_source": l.name, "id": l.id}
                               for l in entity.data_sources]
                    ))
        return entities

language_service = AzureLanguageService()

── services/azure_search.py ─────────────────────────────────────

from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from config import get_settings
from dataclasses import dataclass

settings = get_settings()

@dataclass
class DrugInteraction:
    drug_pair: str
    severity: str
    description: str
    clinical_action: str
    severity_modifiers: dict

@dataclass
class ClinicalGuideline:
    condition: str
    screening: str
    frequency: str
    source: str
    evidence_grade: str
    applicable_codes: list[str]

class AzureSearchService:
    """
    Azure AI Search — hybrid keyword + vector RAG for:
      1. Drug interaction knowledge base (10K+ drug pairs with severity modifiers)
      2. Clinical guidelines index (ADA, USPSTF, ACC/AHA)
    """

    async def search_drug_interactions(
        self, drug_a: str, drug_b: str
    ) -> list[DrugInteraction]:
        async with SearchClient(
            settings.AZURE_SEARCH_ENDPOINT,
            "drug-interactions",
            AzureKeyCredential(settings.AZURE_SEARCH_KEY)
        ) as client:
            results = await client.search(
                search_text=f"{drug_a} {drug_b} interaction",
                filter=None,
                top=5,
                include_total_count=False
            )
            interactions = []
            async for result in results:
                if result.get("@search.score", 0) > 0.5:
                    interactions.append(DrugInteraction(
                        drug_pair=result.get("drug_pair", f"{drug_a} + {drug_b}"),
                        severity=result.get("severity", "Unknown"),
                        description=result.get("description", ""),
                        clinical_action=result.get("clinical_action", ""),
                        severity_modifiers=result.get("severity_modifiers", {})
                    ))
            return interactions

    async def search_guidelines(
        self, conditions: list[str], patient_age: int = None
    ) -> list[ClinicalGuideline]:
        query = " ".join(conditions)
        async with SearchClient(
            settings.AZURE_SEARCH_ENDPOINT,
            "clinical-guidelines",
            AzureKeyCredential(settings.AZURE_SEARCH_KEY)
        ) as client:
            results = await client.search(
                search_text=query,
                top=10
            )
            guidelines = []
            async for result in results:
                if result.get("@search.score", 0) > 0.4:
                    guidelines.append(ClinicalGuideline(
                        condition=result.get("condition", ""),
                        screening=result.get("screening_type", ""),
                        frequency=result.get("frequency", ""),
                        source=result.get("source", ""),
                        evidence_grade=result.get("evidence_grade", ""),
                        applicable_codes=result.get("applicable_codes", [])
                    ))
            return guidelines

search_service = AzureSearchService()

── services/azure_blob.py ───────────────────────────────────────

from azure.storage.blob.aio import BlobServiceClient
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from config import get_settings
from datetime import datetime, timedelta, timezone

settings = get_settings()

class AzureBlobService:
    async def upload_document(
        self, image_bytes: bytes, patient_id: str,
        doc_id: str, ext: str = "jpg"
    ) -> str:
        blob_name = f"{patient_id}/{doc_id}.{ext}"
        async with BlobServiceClient.from_connection_string(
            settings.AZURE_STORAGE_CONNECTION_STRING
        ) as client:
            container = client.get_container_client("prescription-uploads")
            await container.upload_blob(blob_name, image_bytes, overwrite=True)
            sas = generate_blob_sas(
                account_name=settings.AZURE_STORAGE_ACCOUNT_NAME,
                container_name="prescription-uploads",
                blob_name=blob_name,
                account_key=settings.AZURE_STORAGE_KEY,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.now(timezone.utc) + timedelta(hours=1)
            )
            return (
                f"https://{settings.AZURE_STORAGE_ACCOUNT_NAME}"
                f".blob.core.windows.net/prescription-uploads/{blob_name}?{sas}"
            )

    async def upload_health_summary_pdf(
        self, pdf_bytes: bytes, patient_id: str, summary_id: str
    ) -> str:
        blob_name = f"{patient_id}/{summary_id}.pdf"
        async with BlobServiceClient.from_connection_string(
            settings.AZURE_STORAGE_CONNECTION_STRING
        ) as client:
            container = client.get_container_client("health-summaries")
            await container.upload_blob(blob_name, pdf_bytes, overwrite=True)
            sas = generate_blob_sas(
                account_name=settings.AZURE_STORAGE_ACCOUNT_NAME,
                container_name="health-summaries",
                blob_name=blob_name,
                account_key=settings.AZURE_STORAGE_KEY,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.now(timezone.utc) + timedelta(hours=24)
            )
            return (
                f"https://{settings.AZURE_STORAGE_ACCOUNT_NAME}"
                f".blob.core.windows.net/health-summaries/{blob_name}?{sas}"
            )

blob_service = AzureBlobService()

── services/azure_email.py ──────────────────────────────────────

from azure.communication.email import EmailClient
from config import get_settings

settings = get_settings()

REMINDER_HTML = """
<html><body style="font-family: Arial, sans-serif; padding: 20px;">
<div style="max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; padding: 24px;">
  <h2 style="color: #1B2A4A;">💊 CareOrbit Medication Reminder</h2>
  <p>Hello <strong>{patient_name}</strong>,</p>
  <p>This is your reminder to take:</p>
  <div style="background: #EAF4F4; padding: 16px; border-radius: 6px; margin: 16px 0;">
    <strong style="font-size: 18px; color: #0D7A7A;">{medication_name}</strong><br>
    <span style="color: #555;">{dosage} — {time_label}</span>
  </div>
  <p style="color: #555; font-size: 14px;">
    <a href="{taken_url}" style="background: #0D7A7A; color: white; padding: 10px 20px;
       border-radius: 4px; text-decoration: none; margin-right: 10px;">✓ Taken</a>
    <a href="{skipped_url}" style="background: #ccc; color: #333; padding: 10px 20px;
       border-radius: 4px; text-decoration: none;">✗ Skipped</a>
  </p>
  <p style="color: #888; font-size: 12px; margin-top: 20px;">
    CareOrbit — Your Intelligent Care Coordinator<br>
    <a href="{unsubscribe_url}">Manage reminders</a>
  </p>
</div></body></html>
"""

class AzureEmailService:
    def __init__(self):
        self.client = EmailClient.from_connection_string(
            settings.AZURE_COMM_CONNECTION_STRING
        )
        self.sender = settings.AZURE_COMM_SENDER_EMAIL

    async def send_medication_reminder(
        self, to_email: str, patient_name: str,
        medication_name: str, dosage: str, time_label: str,
        reminder_id: str
    ) -> bool:
        base_url = settings.APP_BASE_URL
        message = {
            "senderAddress": self.sender,
            "recipients": {"to": [{"address": to_email}]},
            "content": {
                "subject": f"CareOrbit: Take {medication_name} — {time_label}",
                "html": REMINDER_HTML.format(
                    patient_name=patient_name,
                    medication_name=medication_name,
                    dosage=dosage,
                    time_label=time_label,
                    taken_url=f"{base_url}/reminders/{reminder_id}/taken",
                    skipped_url=f"{base_url}/reminders/{reminder_id}/skipped",
                    unsubscribe_url=f"{base_url}/settings/reminders"
                )
            }
        }
        poller = self.client.begin_send(message)
        result = poller.result()
        return result.status == "Succeeded"

    async def send_interaction_alert(
        self, to_email: str, patient_name: str,
        drug_a: str, drug_b: str, severity: str, action: str
    ) -> bool:
        severity_colors = {
            "HIGH": "#c0392b", "ELEVATED": "#e74c3c",
            "Moderate": "#e67e22", "Low": "#27ae60"
        }
        color = severity_colors.get(severity, "#e67e22")
        html = f"""
        <html><body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; padding: 24px;
                    border: 2px solid {color}; border-radius: 8px;">
          <h2 style="color: {color};">⚠️ Drug Interaction Alert</h2>
          <p>Hello <strong>{patient_name}</strong>,</p>
          <p>A potential interaction was detected between your medications:</p>
          <div style="background: #fff3f3; padding: 16px; border-radius: 6px;">
            <strong>{drug_a}</strong> + <strong>{drug_b}</strong><br>
            <span style="color: {color}; font-weight: bold;">Severity: {severity}</span>
          </div>
          <p><strong>Recommended action:</strong> {action}</p>
          <p style="color: #555;">Please discuss this with your doctor before making
          any changes to your medications.</p>
        </div></body></html>
        """
        message = {
            "senderAddress": self.sender,
            "recipients": {"to": [{"address": to_email}]},
            "content": {
                "subject": f"⚠️ CareOrbit Drug Interaction Alert: {severity} Severity",
                "html": html
            }
        }
        poller = self.client.begin_send(message)
        result = poller.result()
        return result.status == "Succeeded"

    async def send_upload_result(
        self, to_email: str, patient_name: str,
        doc_type: str, nodes_created: int, has_alerts: bool
    ) -> bool:
        alert_line = (
            "<p style='color: #e74c3c;'>⚠️ Drug interaction alerts detected. "
            "View them in your CareOrbit dashboard.</p>"
            if has_alerts else ""
        )
        html = f"""
        <html><body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; padding: 24px;
                    border: 1px solid #e0e0e0; border-radius: 8px;">
          <h2 style="color: #1B2A4A;">✅ Document Processed</h2>
          <p>Hello <strong>{patient_name}</strong>,</p>
          <p>Your <strong>{doc_type.replace('_', ' ')}</strong> has been processed.</p>
          <p><strong>{nodes_created}</strong> health data
          {"item was" if nodes_created == 1 else "items were"} added to your profile.</p>
          {alert_line}
          <p><a href="{settings.APP_BASE_URL}/dashboard"
                style="background: #0D7A7A; color: white; padding: 10px 20px;
                       border-radius: 4px; text-decoration: none;">
            View Your Dashboard</a></p>
        </div></body></html>
        """
        message = {
            "senderAddress": self.sender,
            "recipients": {"to": [{"address": to_email}]},
            "content": {
                "subject": "CareOrbit: Your health data has been updated",
                "html": html
            }
        }
        poller = self.client.begin_send(message)
        result = poller.result()
        return result.status == "Succeeded"

    async def send_previsit_brief(
        self, to_email: str, patient_name: str,
        doctor_name: str, appointment_dt: str,
        brief_content: dict
    ) -> bool:
        tell_items = "".join(
            f"<li>{item}</li>" for item in brief_content.get("tell_doctor", [])
        )
        ask_items = "".join(
            f"<li>{item}</li>" for item in brief_content.get("ask_doctor", [])
        )
        unknown_items = "".join(
            f"<li>{item}</li>" for item in brief_content.get("doctor_may_not_know", [])
        )
        html = f"""
        <html><body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; padding: 24px;
                    border: 1px solid #1B2A4A; border-radius: 8px;">
          <h2 style="color: #1B2A4A;">📋 Pre-Visit Brief — {doctor_name}</h2>
          <p>Hello <strong>{patient_name}</strong>, your appointment is on
             <strong>{appointment_dt}</strong>.</p>
          <h3 style="color: #0D7A7A;">Tell your doctor:</h3>
          <ul>{tell_items}</ul>
          <h3 style="color: #0D7A7A;">Ask your doctor:</h3>
          <ul>{ask_items}</ul>
          <h3 style="color: #C47B00;">Your doctor may not know:</h3>
          <ul>{unknown_items}</ul>
          <p style="color: #555; font-size: 14px; margin-top: 20px;">
            Bring your one-page health summary. Print it or show it on your phone.</p>
          <p><a href="{settings.APP_BASE_URL}/summary/generate"
                style="background: #1B2A4A; color: white; padding: 10px 20px;
                       border-radius: 4px; text-decoration: none;">
            Generate Health Summary PDF</a></p>
        </div></body></html>
        """
        message = {
            "senderAddress": self.sender,
            "recipients": {"to": [{"address": to_email}]},
            "content": {
                "subject": f"CareOrbit: Pre-Visit Brief for {doctor_name} — {appointment_dt}",
                "html": html
            }
        }
        poller = self.client.begin_send(message)
        result = poller.result()
        return result.status == "Succeeded"

email_service = AzureEmailService()

════════════════════════════════════════════════════════════════════
NEW RETENTION FEATURE IMPLEMENTATIONS
════════════════════════════════════════════════════════════════════

── graph/orbit_score.py ─────────────────────────────────────────

Implement the OrbitScoreCalculator class with these exact weights and logic:

WEIGHTS = {
    "completeness":       0.25,
    "avg_confidence":     0.20,
    "interaction_risk":   0.25,
    "care_gap_status":    0.20,
    "adherence_rate":     0.10,
}

class OrbitScoreResult:
    total_score: float          (0-100, 2 decimal places)
    completeness_score: float   (0-100 before weighting)
    confidence_component: float
    interaction_risk_score: float
    care_gap_score: float
    adherence_score: float
    breakdown: dict             (full explanation per component)
    delta: float                (change from previous score — None if first)

async def compute_orbit_score(patient_id: str, db_session) -> OrbitScoreResult:

  COMPLETENESS (0-100):
    Query phig_nodes for patient — count by node_type
    expected_types = ["medication", "condition", "lab_value"]
    present_types = node_types that have >= 1 active node
    base = (len(present_types) / len(expected_types)) * 100
    bonus: +10 if care_gap nodes exist, +5 if provider nodes exist
    cap at 100

  AVERAGE CONFIDENCE (0-100):
    Query medication nodes only (most safety-critical)
    avg = mean(confidence_score) * 100
    If no medication nodes: score = 0

  INTERACTION RISK (0-100, INVERTED — lower risk = higher score):
    Query phig_edges WHERE edge_type = 'interacts_with' AND is_active = TRUE
    penalty per interaction by severity:
      ELEVATED/HIGH → -25 per interaction
      Moderate      → -15 per interaction
      Low           → -5 per interaction
    start from 100, apply penalties, floor at 0
    Resolved interactions (acknowledged in properties) → half penalty

  CARE GAP STATUS (0-100):
    Query phig_nodes WHERE node_type = 'care_gap' AND is_active = TRUE
    open_gaps = nodes without resolved_at in fhir_resource
    If 0 open gaps: 100
    Each open gap: -20, floor at 0

  ADHERENCE RATE (0-100):
    Query adherence_log for last 30 days
    adherence_pct = (taken count / (taken + skipped + no_response)) * 100
    If no reminders set: 75 (neutral — not penalised, not rewarded)

  TOTAL = weighted sum of all five components (0-100)

  Save to orbit_score_history table

  Compute delta vs previous score from orbit_score_history

  Return OrbitScoreResult with full breakdown dict explaining each component

── agents/previsit_agent.py ─────────────────────────────────────

Implement PreVisitAgent class:

PREVISIT_PROMPT = """
You are CareOrbit's pre-visit intelligence system.
Analyse a patient's health graph and generate a structured pre-visit brief
for their upcoming appointment with {doctor_name} ({doctor_specialty}).

Patient context (from PHIG):
{patient_context}

Generate a JSON object:
{{
  "tell_doctor": [
    "List of 2-4 specific facts the doctor needs to know that may have changed"
  ],
  "ask_doctor": [
    "List of 2-4 specific questions the patient should ask"
  ],
  "doctor_may_not_know": [
    "List of 2-3 medications or conditions from OTHER doctors this doctor hasn't seen"
  ],
  "bring_to_appointment": [
    "Practical items to bring — always include health summary PDF"
  ],
  "urgency_flags": [
    "Any critical items requiring immediate discussion — drug interactions, declining labs"
  ]
}}

Rules:
- Be specific to this patient, not generic
- Reference actual medication names, actual lab values
- Cross-provider gaps: identify medications prescribed by doctors OTHER than {doctor_name}
- Clinical urgency: if there is an ELEVATED drug interaction, it must appear in urgency_flags
- Language: clear, warm, non-alarming, 8th grade reading level
"""

async def generate_previsit_brief(
    patient_id: str,
    appointment_id: str,
    db_session
) -> dict:
    Query the appointment from appointments table
    Query full patient PHIG:
      - All active medication nodes with prescriber info from fhir_resource
      - All active condition nodes
      - All active lab_value nodes (most recent per test type)
      - All active phig_edges WHERE edge_type = 'interacts_with'
      - All active care_gap nodes

    Build patient_context string:
      medications section: name, dosage, confidence, prescriber doctor name
      conditions section: name, ICD-10 code
      recent labs section: name, value, unit, reference, is_abnormal
      interactions section: drug pairs + severity
      overdue screenings section: guideline + how overdue

    Identify cross-provider medications:
      Group medications by fhir_resource['informationSource']['display']
      Medications NOT from the appointment's doctor_name → "doctor_may_not_know"

    Call openai_service.chat() with PREVISIT_PROMPT
    Parse JSON response
    Save brief_content to appointments table (brief_content column)
    Update appointments.brief_sent_at = NOW()
    Return brief dict

── agents/history_agent.py (EXTENDED for Living Narrative) ──────

Add generate_living_narrative() method to the existing HistoryAgent class:

NARRATIVE_PROMPT = """
You are CareOrbit's health narrative writer. Write a single paragraph (4-6 sentences)
that tells this patient's health story in warm, plain language (8th grade reading level).

Patient data from the PHIG:
{patient_context}

Trigger event for this update: {trigger_event}

Rules:
- Open with how long they have been managing their primary condition(s)
- Mention their care coordination across multiple doctors if applicable
- Highlight the most significant trend (improving or worsening)
- If a new drug interaction was just detected, it MUST be in the narrative
- End with the single most important thing to discuss at their next appointment
- Do NOT list medications — weave them into the story naturally
- Be warm and supportive, never clinical or alarming
- Never use the word 'patient' — use their name or 'you'

Write the paragraph in {language}. Return ONLY the paragraph text, no JSON wrapper.
"""

async def generate_living_narrative(
    patient_id: str,
    patient_name: str,
    trigger_event: str,   ("document_upload" | "confirmation" | "lab_added" | "interaction_detected")
    language: str = "en",
    db_session = None
) -> str:
    Build full patient context from PHIG (same approach as previsit_agent)
    Include trend data: eGFR trajectory, HbA1c trajectory, weight trajectory
    
    Call openai_service.chat() with NARRATIVE_PROMPT
    
    Save to health_narratives table:
      narrative_text = english version
      narrative_text_hi = if language == 'hi', the response; else None
      trigger_event = trigger_event param
      phig_node_count = count of active phig_nodes
    
    Return narrative text string

── api/routes/orbit.py ──────────────────────────────────────────

Implement four endpoints:

GET /api/orbit/score?patient_id=...
  RBAC: view permission
  Returns: current Orbit Score from v_current_orbit_score view
    {
      "total_score": 74.3,
      "delta": +2.1,        (change since last computation)
      "breakdown": {
        "completeness": {"score": 80, "weight": 0.25, "explanation": "3/3 node types present"},
        "avg_confidence": {"score": 85, "weight": 0.20, "explanation": "4 medications, mean confidence 0.85"},
        "interaction_risk": {"score": 50, "weight": 0.25, "explanation": "1 ELEVATED interaction open"},
        "care_gap_status": {"score": 60, "weight": 0.20, "explanation": "2 overdue screenings"},
        "adherence_rate": {"score": 90, "weight": 0.10, "explanation": "18/20 doses taken this month"}
      },
      "computed_at": "ISO timestamp",
      "premium_required_for_breakdown": false   (true if user is free tier)
    }
  Free tier: return total_score only, breakdown = null, premium_required_for_breakdown = true
  Premium tier: return full breakdown

GET /api/orbit/score/history?patient_id=...&days=30
  Returns: list of {total_score, computed_at} for chart rendering
  Limit: last 90 rows

POST /api/orbit/appointments
  Body: {doctor_name, doctor_specialty, appointment_datetime, location, notes}
  Creates appointment record
  If appointment is within 48 hours AND brief not yet sent:
    Generate brief immediately via previsit_agent.generate_previsit_brief()
    Send brief email via email_service.send_previsit_brief()
  Returns: {appointment_id, brief_scheduled: true/false}

GET /api/orbit/narrative?patient_id=...&language=en
  Returns: latest health_narratives row for patient
    {
      "narrative": "Ramesh, you have been managing...",
      "trigger_event": "document_upload",
      "updated_at": "ISO timestamp",
      "version_count": 7,
      "previous_narrative": null   (null for free tier, previous text for premium)
    }
  Free tier: current narrative only, previous_narrative = null
  Premium tier: include previous_narrative for change tracking

════════════════════════════════════════════════════════════════════
SPRINT-BY-SPRINT TDD IMPLEMENTATION SEQUENCE
════════════════════════════════════════════════════════════════════

Execute each sprint in full before starting the next.
The RED → GREEN → REFACTOR cycle is not optional.

─────────────────────────────────────────────────────────────────
SPRINT 1 — INFRASTRUCTURE + AUTH (Week 1)
─────────────────────────────────────────────────────────────────
Azure introduced: PostgreSQL (pgcrypto), Key Vault

Step 1 (RED):
  Run: pytest tests/unit/test_auth_tokens.py tests/unit/test_encryption.py
  Expected: all FAIL (modules don't exist)

Step 2 (CODE): Implement in order:
  utils/encryption.py
    encrypt_sql(value) → returns value unchanged (placeholder for pgp_sym_encrypt)
    get_encryption_params() → {"encryption_key": settings.ENCRYPTION_KEY}

  api/middleware/auth.py
    hash_password(password: str) → str  (bcrypt, $2b$ prefix)
    verify_password(plain, hashed) → bool
    create_access_token(user_id: str) → str
      payload: sub=user_id, type="access", exp=now+15min, iat=now
    create_refresh_token(user_id, ip_address, device_info) → str
      generate secrets.token_urlsafe(64)
      store SHA-256 hash in refresh_tokens table
      return raw token
    verify_refresh_token(raw_token) → dict
    revoke_refresh_token(raw_token)
    revoke_all_user_tokens(user_id)
    get_current_user(credentials) → dict

Step 3 (GREEN): pytest tests/unit/test_auth_tokens.py tests/unit/test_encryption.py

Step 4 (RED): Run: pytest tests/functional/test_api_auth.py

Step 5 (CODE): Implement api/routes/auth.py
  POST /api/auth/register:
    Validate: email unique (SELECT with pgp_sym_decrypt), password strength
    Hash password with bcrypt
    INSERT users with pgp_sym_encrypt for phone_number
    INSERT patient_profiles
    INSERT subscriptions (free tier default)
    Create access_token + refresh_token
    Log audit: REGISTER
    Return {access_token, refresh_token, user: {id, name, email, tier}}
    NO OTP in Phase 1

  POST /api/auth/login:
    SELECT user by email (decrypt and compare)
    verify_password()
    Update last_login
    Create tokens
    Log audit: LOGIN
    Return tokens

  POST /api/auth/refresh:
    Accept: json body {refresh_token: "..."}  NOT cookies
    verify_refresh_token()
    Revoke old token (rotation)
    Create new access_token + refresh_token
    Return new tokens

  POST /api/auth/logout:
    Accept: json body {refresh_token: "..."}  NOT cookies
    revoke_refresh_token()
    Log audit: LOGOUT
    Return {status: "logged_out"}

Step 6 (GREEN): pytest tests/functional/test_api_auth.py

Step 7 (RED): Run security tests
  pytest tests/security/test_refresh_token_security.py
         tests/security/test_audit_trail.py
         tests/security/test_audit_append_only.py -m "not slow"

Step 8 (CODE):
  api/middleware/audit.py — log_audit() function (append-only INSERT)
  api/middleware/rbac.py — verify_patient_access() function
  DB permissions: REVOKE UPDATE, DELETE ON audit_log FROM careorbit_user
                  GRANT INSERT, SELECT ON audit_log TO careorbit_user

Step 9 (GREEN): All Sprint 1 tests green

─────────────────────────────────────────────────────────────────
SPRINT 2 — DOCUMENT PIPELINE (Week 2)
─────────────────────────────────────────────────────────────────
Azure introduced: Document Intelligence, Language (NER), Blob Storage

Step 1 (RED): pytest tests/unit/test_confidence_scoring.py
              pytest tests/unit/test_drug_database.py

Step 2 (CODE):
  graph/confidence.py — ConfidenceCalculator with SOURCE_CEILINGS:
    prescription_photo:   0.85
    lab_report_photo:     0.80
    medicine_strip_photo: 0.75
    patient_text_input:   0.60
    (patient_confirmed and patient_corrected bypass calculator — score=0.85 hardcoded)

    calculate_medication_confidence(source_type, ocr_confidence, drug_match_score,
      dosage_parsed, date_found, patient_confirmed) → ConfidenceResult
      raw = source_ceiling × ocr_confidence × drug_match_score
            × (1.05 if dosage_parsed else 0.90) × (1.02 if date_found else 0.95)
      Apply ceiling: min(raw, SOURCE_CEILINGS[source_type])
      floor at 0.0

  utils/drug_database.py — DrugDatabase with:
    RXNORM_CODES dict (all 10 confirmed drugs from conftest)
    BRAND_TO_GENERIC dict (Thyronorm→Levothyroxine, Glycomet→Metformin, etc.)
    FREQUENCY_MAP dict (BD→"twice daily", OD→"once daily", etc.)
    fuzzy_match(name) → MatchResult with matched_name, rxnorm_code, confidence
      Use difflib.SequenceMatcher for edit distance

Step 3 (GREEN): Unit tests green

Step 4 (RED): pytest tests/integration/test_document_state_machine.py
              pytest tests/functional/test_api_documents.py
              pytest tests/functional/test_api_documents_boundaries.py

Step 5 (CODE):
  services/azure_vision.py (from template above)
  services/azure_language.py (from template above)
  services/azure_blob.py (from template above)
  pipeline/fhir_converter.py — medication_to_fhir(), lab_to_fhir()
  pipeline/prescription_extractor.py
  pipeline/lab_report_extractor.py
  pipeline/medicine_strip_reader.py
  pipeline/document_classifier.py
  graph/phig_builder.py:
    add_node() → INSERT phig_nodes, return node dict
    add_edge() → INSERT phig_edges
    get_node() → SELECT by id
    update_node_confidence()
    check_interactions_for_node() → query search_service, apply severity modifiers
    evaluate_care_gaps() → query search_service for guidelines, compare to PHIG nodes
    get_medication_subgraph()
    get_full_patient_graph()

  pipeline/document_pipeline.py:
    process_document() MUST always return terminal status
    (success | needs_confirmation | failed — NEVER "processing" as final)
    On success: trigger generate_living_narrative() with trigger="document_upload"
    On success: trigger orbit score recomputation
    On success: call email_service.send_upload_result()

  api/routes/documents.py:
    POST /api/documents/upload
    Allowed: image/jpeg, image/png, image/webp, image/heic
    Max size: 10MB (check before reading bytes)
    Feature gate: enforce_document_limit(user_id)
    Return: document_id, document_type, status, nodes_created (count),
            interaction_alerts, care_gap_alerts, confirmation_needed,
            processing_time_ms, error

Step 6 (GREEN): All Sprint 2 tests green

─────────────────────────────────────────────────────────────────
SPRINT 3 — INTERACTION ENGINE + CARE GAPS (Week 3)
─────────────────────────────────────────────────────────────────
Azure introduced: Azure AI Search (hybrid RAG)

Step 1 (RED):
  pytest tests/false_positive_negative/ (BOTH wiring AND algorithm tests)
  pytest tests/functional/test_api_confirmations.py

Step 2 (CODE):
  services/azure_search.py (from template above)
  Extend graph/phig_builder.py:
    check_interactions_for_node(): call search_service.search_drug_interactions()
      Apply severity_modifiers:
        If patient creatinine > 1.3 OR eGFR < 60:
          Moderate interaction → ELEVATED
        If patient age > 65:
          Add "+1 severity note" to interaction properties
      Write interaction edges to phig_edges
      Return list of interaction alerts

    evaluate_care_gaps(): call search_service.search_guidelines()
      Compare returned guidelines against phig_nodes
      If no matching node for required screening: create care_gap node
      Return list of care gap alerts

  api/routes/confirmations.py:
    POST /api/confirmations/confirm:
      confirmed=True → set confidence_score=0.85, confidence_source="patient_confirmed"
      corrected_name → run drug_db.fuzzy_match(), update node, score=0.85
      nonexistent node → return 200 + {"error": "Node not found"}
        (NOT raise HTTPException(404) — route uses return not raise)
      Trigger orbit score recomputation
      Trigger narrative update with trigger="confirmation"

Step 3 (GREEN): All Sprint 3 tests green

─────────────────────────────────────────────────────────────────
SPRINT 4 — AI CHAT + ORCHESTRATOR (Week 4)
─────────────────────────────────────────────────────────────────
Azure introduced: Azure OpenAI GPT-4o, Azure AI Translator

Step 1 (RED): pytest tests/integration/test_orchestrator.py

Step 2 (CODE):
  services/azure_openai.py (from template above)
  services/azure_translator.py (from template above)
  agents/base_agent.py — AgentResponse dataclass
  agents/medication_agent.py — analyze(patient_id, message) → AgentResponse
  agents/care_gap_agent.py
  agents/history_agent.py — including generate_living_narrative() extension
  agents/orchestrator.py:
    MEDICATION_KEYWORDS, CARE_GAP_KEYWORDS, HISTORY_KEYWORDS (exact lists from MVP)
    process_query():
      Detect language if auto
      Translate if language != 'en'
      Route agents via _route_agents()
      Run agents in parallel: await asyncio.gather(*tasks)
      Synthesise via GPT-4o
      Translate response back if needed
      Return OrchestratorResponse

  api/routes/chat.py:
    POST /api/chat/query
    RBAC: view permission for caregivers
    Log audit: CHAT_QUERY with agents_used + language

Step 3 (GREEN): All Sprint 4 tests green

─────────────────────────────────────────────────────────────────
SPRINT 5 — SUMMARIES + REMINDERS + ORBIT SCORE + SUBSCRIPTIONS (Week 5)
─────────────────────────────────────────────────────────────────
Azure introduced: Azure Communication Services (Email)

Step 1 (RED):
  pytest tests/functional/test_api_summary.py
  pytest tests/functional/test_api_reminders.py
  pytest tests/functional/test_api_subscriptions.py
  pytest tests/business_logic/test_tier_config.py

Step 2 (CODE):
  utils/summary_generator.py:
    generate_pdf(patient_data: dict) → bytes
    Uses reportlab to produce a single-page PDF:
      Header: patient name, generated date, verification code
      Section 1: Active medications with confidence badges (🟢🟡🟠🔴)
      Section 2: Drug interaction alerts in red box
      Section 3: Overdue screenings
      Section 4: Recent abnormal lab values
      Footer: "Generated by CareOrbit — powered by Microsoft Azure"
    Returns raw PDF bytes (starts with %PDF magic bytes)

  services/azure_email.py (from template above)
  graph/orbit_score.py (from specification above)
  agents/previsit_agent.py (from specification above)

  api/routes/summary.py:
    GET /api/summary/generate  (NOT POST)
    When total_nodes == 0: return HTTP 200 + {"error": "No health data..."}
    When total_nodes > 0: StreamingResponse(PDF bytes)
      content-type: application/pdf
      content-disposition: attachment; filename="CareOrbit_Summary_{date}.pdf"

  api/routes/reminders.py:
    POST /api/reminders/create: requires edit permission
      Body: {medication_node_id, reminder_time: "HH:MM", days_of_week: [int]}
      Returns: {reminder_id, ...}
    GET /api/reminders/list: returns list
    DELETE /api/reminders/{reminder_id}: 404 if not found, 200 if deleted

  APScheduler setup in main.py:
    Scheduler checks medication_reminders every minute
    For each due reminder: send email via email_service.send_medication_reminder()
    Log to adherence_log with response="no_response" initially

  API middleware for feature gates:
    api/middleware/feature_gate.py:
      TIER_LIMITS dict (free, premium_individual, premium_family)
        free: docs_per_month=100, summaries_per_month=5, max_caregivers=2,
              data_retention_months=24, family_dashboard=False, shows_ads=True
        premium_individual: docs_per_month=None, summaries_per_month=None,
              max_caregivers=10, data_retention_months=None, shows_ads=False
        premium_family: max_family_members=3, family_dashboard=True, shows_ads=False
      enforce_document_limit(user_id) → raises HTTPException(429) if at limit
      check_feature_allowed(user_id, feature) → bool
      get_tier_limits(tier) → dict (unknown tier → returns free tier config)

  api/routes/subscriptions.py:
    NOTE: subscriptions.router IS registered in main.py (confirmed in v0.3.0)
    GET /api/subscriptions/current → {tier, features: {shows_ads, limits...}}
    GET /api/subscriptions/plans → {plans: [{tier, price_monthly_cents, features}]}
      free: 0 cents, premium_individual: 799 cents, premium_family: 1999 cents

  api/routes/orbit.py (from specification above):
    GET /api/orbit/score
    GET /api/orbit/score/history
    POST /api/orbit/appointments
    GET /api/orbit/narrative

Step 3 (GREEN): All Sprint 5 tests green

─────────────────────────────────────────────────────────────────
SPRINT 6 — FRONTEND + CAREGIVERS + E2E (Week 6)
─────────────────────────────────────────────────────────────────

Step 1 (RED):
  pytest tests/functional/test_api_caregivers.py
  pytest tests/security/test_cross_patient_rbac.py
  pytest tests/security/test_rbac_enforcement.py
  pytest tests/security/test_rbac_permission_levels.py
  pytest tests/security/test_rate_limiting.py
  pytest tests/security/test_password_change_revocation.py

Step 2 (CODE):
  api/routes/caregivers.py:
    POST /api/caregivers/add:
      Valid relationships: son, daughter, spouse, parent, sibling, friend, nurse
      Valid permissions: view, edit, full
      Response: {status: "added", caregiver_name, permission_level}
      NO link_id in response
      Feature gate: enforce_caregiver_limit (raises 429 when limit reached)
    DELETE /api/caregivers/{user_id}: idempotent → always 200 {status: "revoked"}
    GET /api/caregivers/: returns list

  Rate limiting in api/middleware/auth.py:
    Track failed login attempts per email in memory (or Redis if available)
    After 5 failures: return 429 on all attempts (correct and incorrect)

  POST /api/auth/change-password:
    Verify current password
    Hash new password
    Call revoke_all_user_tokens(user_id) — invalidate ALL refresh tokens
    Return {status: "password_changed"}

Step 3 (GREEN): All security tests green

Step 4 (RED): pytest tests/e2e/test_patient_journey_ramesh.py

Step 5 (CODE): Frontend — apps/web/

  api/client.ts:
    Typed fetch wrapper with auto token refresh on 401
    All API response types imported from packages/types

  pages/Dashboard.tsx:
    Top section: OrbitScore component (animated ring + score number)
    Second row: HealthNarrative component (living narrative paragraph)
    Third row: interaction alerts (red), care gap alerts (amber)
    Fourth row: medication cards with confidence badges
    Free tier: AdSlot components at top and between sections

  components/OrbitScore.tsx:
    Animated circular progress ring (SVG)
    Score number in centre with delta indicator (↑ +2.1 in green, ↓ -3.4 in red)
    Free tier: shows score number only, "See Breakdown" button → upgrade prompt
    Premium tier: shows full breakdown breakdown accordion
    Colour: 0-40 red, 41-70 amber, 71-100 green

  components/HealthNarrative.tsx:
    Paragraph text with "Updated {relative time}" footer
    Premium: "View previous version" expand link
    On click: fetch /api/orbit/narrative

  components/PreVisitBrief.tsx:
    Card with appointment details
    Sections: Tell doctor / Ask doctor / May not know
    "Send to email" button → POST /api/orbit/appointments/{id}/resend-brief
    Shown 48 hours before appointment date

  components/InteractionAlert.tsx:
    Red/amber bordered card
    Drug pair displayed prominently
    Severity badge: HIGH (red), ELEVATED (red), Moderate (amber), Low (green)
    "Learn more" expands clinical action text

  components/ConfidenceBadge.tsx:
    🟢 Verified (≥0.85) | 🟡 Confirmed (≥0.65) | 🟠 Reported (≥0.40) | 🔴 Uncertain (<0.40)

  components/UploadZone.tsx:
    Drag-and-drop + click-to-upload
    Accepted: image/jpeg, image/png, image/webp, image/heic
    Max 10MB (validate client-side before POST)
    Shows processing spinner, then result card with nodes_created count

Step 6 (GREEN): pytest tests/e2e/test_patient_journey_ramesh.py

Step 7: Full test run
  pytest -m "not phase2 and not phase3 and not demo_only" --cov=. --cov-report=term
  Target: >= 875 tests collected, 0 failures, >= 80% coverage

════════════════════════════════════════════════════════════════════
CI/CD PIPELINE — .github/workflows/ci.yml
════════════════════════════════════════════════════════════════════

Generate the complete ci.yml with these exact stages in order:

name: CareOrbit CI

on:
  push: { branches: [main, develop] }
  pull_request: { branches: [main] }

jobs:

  ── STAGE 1: SAFETY (runs first, blocks everything on failure) ──
  safety:
    name: "Clinical Safety Tests"
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env: { POSTGRES_DB: careorbit_test, POSTGRES_USER: test, POSTGRES_PASSWORD: test }
        ports: ["5432:5432"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r apps/api/requirements.txt
      - name: Run clinical safety tests
        run: |
          cd apps/api
          pytest tests/false_positive_negative/ -m critical -v --tb=short
          pytest tests/security/test_cross_patient_rbac.py -v --tb=short
          pytest tests/security/test_audit_append_only.py -v --tb=short
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/careorbit_test
          JWT_SECRET: test-secret-for-ci-only
          ENCRYPTION_KEY: test-encryption-key-32chars!
          # Azure services mocked — no real credentials needed in safety stage

  ── STAGE 2: UNIT (depends on safety) ──
  unit:
    name: "Unit Tests"
    needs: safety
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r apps/api/requirements.txt
      - name: Run unit tests
        run: |
          cd apps/api
          pytest tests/unit/ -v --tb=short -x --cov=. --cov-report=xml
          # -x = fail fast on first failure
      - name: Coverage gate
        run: |
          cd apps/api
          python -c "
          import xml.etree.ElementTree as ET
          tree = ET.parse('coverage.xml')
          rate = float(tree.getroot().attrib['line-rate']) * 100
          print(f'Coverage: {rate:.1f}%')
          assert rate >= 90, f'Unit coverage {rate:.1f}% below 90% gate'
          "

  ── STAGE 3: INTEGRATION (depends on unit) ──
  integration:
    name: "Integration Tests"
    needs: unit
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env: { POSTGRES_DB: careorbit_test, POSTGRES_USER: test, POSTGRES_PASSWORD: test }
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r apps/api/requirements.txt
      - name: Apply schema
        run: psql postgresql://test:test@localhost:5432/careorbit_test < apps/api/database/schema.sql
      - name: Run integration + security tests
        run: |
          cd apps/api
          pytest tests/integration/ tests/security/ -v --tb=short -m "not phase2 and not phase3"
      - name: Coverage gate
        run: coverage >= 80% on integration code paths

  ── STAGE 4: FUNCTIONAL (depends on integration) ──
  functional:
    name: "Functional + Business Logic Tests"
    needs: integration
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r apps/api/requirements.txt
      - name: Run functional tests
        run: |
          cd apps/api
          pytest tests/functional/ tests/business_logic/ tests/regression/ \
            -v --tb=short -m "not phase2 and not phase3 and not demo_only"

  ── STAGE 5: FRONTEND BUILD (depends on functional) ──
  frontend:
    name: "Frontend Build + Lint"
    needs: functional
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: cd apps/web && npm run build
      - run: cd apps/web && npm run lint

  ── STAGE 6: E2E (main branch only, depends on frontend) ──
  e2e:
    name: "Ramesh E2E Journey"
    needs: frontend
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env: { POSTGRES_DB: careorbit_test, POSTGRES_USER: test, POSTGRES_PASSWORD: test }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: pip install -r apps/api/requirements.txt
      - run: npm ci
      - name: Apply schema + seed demo data
        run: |
          psql postgresql://test:test@localhost:5432/careorbit_test < apps/api/database/schema.sql
          cd apps/api && python database/seed_demo.py
      - name: Start API
        run: cd apps/api && uvicorn main:app --port 8000 &
      - name: Start frontend
        run: cd apps/web && npm run preview --port 3000 &
      - name: Run E2E tests
        run: cd apps/api && pytest tests/e2e/ -v --tb=long
      - name: Upload test report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: e2e-report
          path: apps/api/tests/e2e/results/

  ── STAGE 7: DEPLOY (main + all stages pass) ──
  deploy:
    name: "Deploy to Azure"
    needs: [e2e]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy API to Azure Container Apps
        run: |
          az containerapp update \
            --name careorbit-api \
            --resource-group careorbit-mvp \
            --image ghcr.io/${{ github.repository }}/api:${{ github.sha }}
      - name: Deploy frontend to Azure Static Web Apps
        uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
          repo_token: ${{ secrets.GITHUB_TOKEN }}
          action: "upload"
          app_location: "apps/web"
          output_location: "dist"
      - name: Smoke test production
        run: |
          sleep 30
          curl -f https://careorbit-api.azurecontainerapps.io/health
          curl -f https://careorbit.azurestaticapps.net/

════════════════════════════════════════════════════════════════════
FINAL DELIVERY CHECKLIST — VERIFY BEFORE DECLARING COMPLETE
════════════════════════════════════════════════════════════════════

Run this checklist in full before closing the implementation:

□ pytest --co -q | wc -l → must show >= 875 test items
□ pytest -m "not phase2 and not phase3 and not demo_only" → 0 failures, 0 errors
□ pytest --cov=. --cov-report=term-missing | grep TOTAL → >= 80%
□ No test file contains the string "if response.status_code" or "if mock.called"
□ No test file contains "def test_" followed only by "pass" on next non-blank line
□ grep -r "include_router.*subscriptions" tests/ → 0 results (no router hack)
□ grep -r "0\.05" tests/ → 0 results (hallucinated floor deleted)
□ grep "patient_confirmed" tests/conftest.py → appears in PHASE1_SOURCES list
□ grep "P0" tests/coverage_matrix.py | grep -c "P0-" → output == 17
□ Reminder delete test: grep "assert create.status_code" → found (hard assert)
□ Interaction split: grep "WIRING TEST\|ALGORITHM TEST" tests/false_positive_negative/ → found both
□ Encryption test: grep "call_count >= 2" tests/unit/test_encryption.py → found
□ Orbit Score: GET /api/orbit/score → 200, total_score is float 0-100
□ Pre-Visit Brief: POST /api/orbit/appointments → 201, brief_scheduled in response
□ Living Narrative: GET /api/orbit/narrative → 200, narrative is non-empty string
□ Summary: response.content[:4] == b"%PDF" → True
□ Health endpoint: GET /health → 200, status=="healthy", no auth required
□ Frontend: npm run build in apps/web → 0 errors
□ docker compose up → Postgres starts, schema applies, seed_demo.py runs without errors
□ README.md exists with: local setup, Azure provisioning guide, env vars reference,
  how to run each CI stage locally, Orbit Score explanation for judges

FINAL LINE TO OUTPUT WHEN COMPLETE:
"CareOrbit implementation complete. All 875+ tests passing.
Orbit Score, Pre-Visit Brief, and Living Narrative implemented and tested.
Azure stack: 9 services integrated. CI pipeline: 7 stages configured.
Ready for Imagine Cup demo."
```
