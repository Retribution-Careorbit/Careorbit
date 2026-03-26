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

## UI/UX Design System (Bloomberg-Health-SaaS Redesign)
-   **Typography:** DM Sans (body/headings, `font-sans`), Space Mono (numbers/scores/timestamps/monospace, `font-mono`).
-   **Color Tokens (CSS Custom Properties):**
    - Backgrounds: `--bg-base`, `--bg-surface`, `--bg-elevated`, `--bg-card`, `--bg-hover`
    - Borders: `--border-subtle`, `--border-default`, `--border-strong`
    - Text: `--text-primary`, `--text-secondary`, `--text-muted`
    - Accents: `--accent-cyan` (#00D4FF), `--accent-violet` (#7C3AED), `--accent-amber` (#F59E0B), `--accent-emerald` (#10B981), `--accent-rose` (#F43F5E) — each with `-dim` variant at 12% opacity
    - Glows: `--glow-cyan`, `--glow-violet`
-   **Dark Theme (primary):** bg-base `#0A0C10`, bg-surface `#0F1117`, bg-elevated `#161B25`, bg-card `#1A2030`
-   **Light Theme:** bg-base `#F0F2F7`, bg-surface `#FFFFFF`, bg-card `#FFFFFF`
-   **Design System CSS Classes:**
    - `.page-card`: bg-card, 16px radius, subtle border, hover border+shadow transition. Used for all content cards across pages.
    - `.page-card-header`: flex row with 36px icon container + title text, bottom border separator. Used inside `.page-card` elements.
    - `.page-title-bar`: page-level title area with gradient accent line (cyan→violet→transparent `::after` pseudo-element). Contains h1 + subtitle p. Used on all inner pages.
    - `.header-bar`: 60px height, gradient bg (surface→base), 1px bottom border, backdrop blur. Used in Layout component.
    - `.sidebar-header-gradient`: subtle cyan gradient in sidebar header area.
    - `.login-panel`: dark aurora gradient background with animated floating shapes. Used on login/register left panel.
    - `.login-floating-shape`: animated floating circles for login/register branding panel.
-   **StatCard System:** CSS class `.stat-card` + `data-accent="cyan|violet|amber|emerald"` for radial gradient corner + top border + hover glow
-   **Login/Register:** Interaction-focused split-screen layout. Left: dark branded panel with floating particle animation, hoverable feature cards with color-mix backgrounds (Shield/Activity/FileText icons), CareOrbit branding with cyan glow. Right: card form with animated focus underline (cyan 2px) on inputs, real-time email validation checkmark, password strength meter (3-bar red/yellow/green), show/hide password toggle, remember me checkbox, gradient submit button (cyan→violet with hover scale), Google/Apple social login buttons. Mobile: card-only layout with inline branding.
-   **Top Navbar (Desktop):** Sticky 60px `.topnav` with glass blur, CareOrbit logo + horizontal nav links (Dashboard, Medications, Documents, Orbit Score) + "More" dropdown (AI Chat, Appointments, Health Insights, Reminders, Test Cases, Settings) + search pill + notification bell + theme toggle + user avatar/logout. Active state: cyan text with cyan-tinted background.
-   **Mobile Bottom Nav:** Fixed 64px `.mobile-bottom-nav` at bottom with 5 tabs: Home, Meds, Docs, Score, Settings. Cyan active state. Hidden on md+ screens.
-   **Mobile Menu Sheet:** Slide-in drawer from right (hamburger menu button on mobile) with all navigation routes, theme toggle, and sign out. Accessible with `role="dialog"` and keyboard support.
-   **SOS Button:** Positioned at `bottom: 80px` to clear mobile bottom nav, `right: 20px`
-   **Dashboard:** Hero greeting card with gradient background (cyan+violet), Sparkles icon label, stat cards grid, orbit score mini-widget, heart rate chart, quick actions, reminders, appointments, activity timeline — all using `.page-card` + `.page-card-header`
-   **OrbitScoreBadge:** `InlineOrbitScore` component shown inline in nav links and mobile header. Mini ring + score number, color-coded (rose/amber/cyan/emerald). Full `OrbitScoreBadge` still available as standalone widget.
-   **Animations:** `framer-motion` with `FadeIn`, `ScaleIn`, `SlideIn`, `StaggerContainer`, `PageTransition`, `CountUp`, `HoverCard`. All respect `prefers-reduced-motion`. CSS: `.page-content` fadeSlideIn, `.stat-card` hover lift, `.animate-floater-entrance`, `.animate-border-pulse`
-   **Charts:** Recharts library — `HealthMetricsChart` (line/area), `OrbitScoreRadial` (radial gauge), `AdherenceDonut` (pie), `CategoryBreakdownBar` (horizontal bar), `Sparkline` (mini trend). All charts use `useId()` for unique SVG gradient IDs.

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

## Deployment Infrastructure (Implemented)
- **Config (T002):** `config.py` loads secrets from Azure Key Vault (via `AZURE_KEYVAULT_URI` env var) with fallback to env vars. Maps all 17 PRD secrets via `_KEYVAULT_SECRET_MAP`.
- **Azure Services (T003):** All 7 service wrappers (`azure_openai.py`, `azure_vision.py`, `azure_language.py`, `azure_search.py`, `azure_translator.py`, `azure_email.py`, `azure_blob.py`) now use real Azure SDKs with lazy client initialization and graceful degradation (raise NotImplementedError when credentials not present).
- **Database (T004):** `db/session.py` now supports async PostgreSQL via SQLAlchemy async engine (`AsyncPgSession`) with connection pooling, SSL for Azure PG. Falls back to `InMemorySession` when no PostgreSQL URL configured. Alembic initialized for migrations.
- **Security (T005):** `SecurityHeadersMiddleware` adds HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy to all responses. DPDP compliance endpoints: `DELETE /api/auth/delete-account`, `GET /api/auth/export-data`. Enhanced `/health` endpoint returns `environment` and `database` status. Production JSON logging via `python-json-logger`.
- **CI/CD (T001):** `.github/workflows/deploy.yml` with multi-environment deployment (dev/release/production with staging slot swap). `client/staticwebapp.config.json` for Azure SWA. CI workflow updated to exclude `deployment` marker tests.

## Test Suite
- **522 passed**, 3 skipped, 1 xfailed — full test suite intact
- **136 deployment infra tests** across 6 files: `test_config_keyvault.py`, `test_azure_services_real.py`, `test_database_production.py`, `test_api_health_production.py`, `test_security_headers.py`, `test_deploy_readiness.py`
- Sidebar nav testids: `nav-*` prefix (nav-dashboard, nav-medications, nav-orbit-score, nav-appointments, nav-health-insights, etc.)
- Sign-out: `button-sign-out-sidebar` (sidebar), `button-sign-out` (settings)
- Theme toggle: `button-theme-toggle` (sidebar), `button-theme` (settings)
- SOS button: `button-sos` (fixed position on all authenticated pages)

## External Dependencies
Azure Vision, Azure OpenAI (GPT-4o), Azure Translator, Azure Language, Azure Blob Storage, Azure Email, Azure AI Search, Azure KeyVault — real SDK wrappers implemented with graceful degradation. pgcrypto for PII encryption, python-jose for JWT, bcrypt for passwords. SQLAlchemy async + asyncpg for PostgreSQL. Alembic for migrations.
