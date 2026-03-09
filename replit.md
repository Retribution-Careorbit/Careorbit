# CareOrbit — Healthcare AI Platform for Indian Patients

## Overview
CareOrbit is an AI-powered healthcare platform specifically designed for Indian patients. Its primary purpose is to simplify healthcare management by offering features such as AI-driven extraction from medical documents (prescriptions, lab reports, medicine strips), drug interaction detection, identification of care gaps, and multi-agent AI chat in both Hindi and English. The platform also generates health summary PDFs, provides medication reminders, and operates on a tiered subscription model (free, premium individual, premium family). A core ambition is to ensure HIPAA-compliant security through PII encryption and an append-only audit trail. The project aims to enhance patient understanding and adherence to medical advice, ultimately improving health outcomes in India.

## User Preferences
I want the agent to prioritize high-level architectural and design decisions over minute implementation details. When proposing changes, focus on how they align with the overall system architecture and user experience. Ensure that any new features or modifications are accompanied by relevant test cases or updates to the existing test suite, particularly for business logic and API endpoints. I prefer iterative development, with clear communication before major changes are made to the codebase.

## System Architecture
The application uses a Python 3.12 FastAPI backend (port 8000) and a React 18 frontend with Vite 5 and an Express proxy (port 5000). State management is handled by Zustand for authentication and TanStack Query v5 for data fetching. The UI is built with Tailwind CSS 3.4, shadcn/ui components, Lucide icons, and Recharts for data visualization. An in-memory session (`InMemorySession`) is used for the database.

Key architectural patterns include:
-   **Module-level patching:** Routes import middleware modules (e.g., `api.middleware.auth`) and call functions via the module alias to facilitate testing.
-   **Service capture at construction:** Orchestrator and DocumentPipeline capture service references during `__init__` to preserve mock references during testing.
-   **`async_session` usage:** `InMemorySession` is used directly via `async_session()` for some operations, while `async with async_session() as session:` is used where context management is required.
-   **Confidence Scoring:** A `ConfidenceCalculator` assigns scores to extracted medical information, with `SOURCE_CEILINGS` defining maximum confidence for different input types (e.g., `prescription_photo=0.85`). Patient confirmations can bypass this calculation.
-   **Multi-Agent AI:** An `orchestrator.py` routes queries to specialized agents like `PreVisitAgent` and `HistoryAgent`.
-   **Document Processing Pipeline:** A state machine (`document_pipeline.py`) classifies and extracts information from uploaded documents using components like `DocumentClassifier`, `PrescriptionExtractor`, and `LabReportExtractor`.
-   **Patient Health Information Graph (PHIG):** The `phig_builder.py` constructs a graph of patient health data.
-   **Orbit Score:** A `OrbitScoreCalculator` computes a patient's overall health score based on weighted components (completeness, avg_confidence, interaction_risk, care_gap_status, adherence_rate).
-   **Onboarding Flow:** New or incomplete profiles are redirected to an onboarding process to gather mandatory patient details, improving the quality of health reports.
-   **CORS Configuration:** Origins are securely configured via environment variables, defaulting to `localhost` and auto-detecting `REPLIT_DEV_DOMAIN`.

## UI/UX Design System
-   **Color Palette (Dark-First Neon):** Primary cyan (#00d9ff), Secondary purple (#7c3aed), Warning orange (#fb923c), Success green (#10b981), Error red (#ef4444). Dark mode backgrounds use deep navy (#0a0e27 / #141b34 family), cards are glassmorphic with backdrop-blur.
-   **Typography:** Inter (body/sans), Poppins (headings), JetBrains Mono (code).
-   **Glassmorphism:** `.glass` and `.glass-strong` CSS classes for card transparency + blur. `.aurora-bg` / `.aurora-bg-strong` for gradient backgrounds.
-   **Animations:** `framer-motion` with `FadeIn`, `ScaleIn`, `SlideIn`, `StaggerContainer`, `PageTransition`, `CountUp`, `HoverCard`. All respect `prefers-reduced-motion`.
-   **Charts:** Recharts library — `HealthMetricsChart` (line/area), `OrbitScoreRadial` (radial gauge), `AdherenceDonut` (pie), `CategoryBreakdownBar` (horizontal bar), `Sparkline` (mini trend).

## Pages & Routes

### Unauthenticated
- `/` — Login (aurora background)
- `/register` — Registration (aurora background)

### Authenticated
- `/` — Dashboard (stat cards, orbit score widget, heart rate chart, quick actions, reminders, appointments, activity timeline)
- `/onboarding` — Profile completion wizard
- `/orbit-score` — Health Score dashboard (radial chart, history, breakdown, achievements/badges)
- `/medications` — Medication list with search, adherence donut, interaction checker dialog, confidence badges, dosage tracker
- `/documents` — Document upload with drag-drop processing
- `/chat` — AI Health Assistant (English/Hindi)
- `/reminders` — Medication reminder CRUD
- `/appointments` — Appointment booking (create form, upcoming/past list, video call mock)
- `/health-insights` — Vital signs tracker (BP, glucose, weight, temperature sparklines + charts), AI insight cards, PDF download
- `/settings` — Profile info, theme toggle, subscription plans
- `/test-cases` — Developer QA dashboard

## API Endpoints

### Auth (`/api/auth`)
- POST `/register`, `/login`, `/refresh`, `/logout`, `/change-password`

### Patients (`/api/patients`)
- GET/PUT `/profile`, GET `/overview`, `/medications`, `/vitals`, `/emergency-contacts`

### Orbit (`/api/orbit`)
- GET `/score`, `/score/history`, `/appointments`, `/narrative`
- POST `/appointments`

### Other
- POST `/api/chat/query`, `/api/documents/upload`, `/api/confirmations/confirm`
- POST `/api/reminders/create`, GET `/list`, DELETE `/{id}`
- GET `/api/subscriptions/current`, `/plans`, POST `/upgrade`
- POST `/api/caregivers/add`, DELETE `/{id}`, GET `/my-patients`, `/my-caregivers`
- GET `/api/summary/generate`, `/api/tests/cases`, `/health`

## Demo Credentials
- Email: `ramesh@careorbit.dev` / Password: `Ramesh123!`
- 68yo male from Durgapur, WB. Conditions: T2DM, HTN, Dyslipidemia. 5 medications, drug interaction (Metformin+Ibuprofen), Stage 3a CKD.

## Test Suite
- **427 passed**, 2 failed (pre-existing OTP), 6 skipped, 1 xfailed, 4 xpassed
- Sidebar nav testids: `nav-*` prefix (nav-dashboard, nav-medications, nav-orbit-score, nav-appointments, nav-health-insights, etc.)
- Sign-out: `button-sign-out-sidebar` (sidebar), `button-sign-out` (settings)
- Theme toggle: `button-theme-toggle` (sidebar), `button-theme` (settings)
- SOS button: `button-sos` (fixed position on all authenticated pages)

## External Dependencies
Azure Vision, Azure OpenAI (GPT-4o), Azure Translator, Azure Language, Azure Blob Storage, Azure Email, Azure AI Search, Azure KeyVault — all currently stubbed. pgcrypto for PII encryption, python-jose for JWT, bcrypt for passwords.
