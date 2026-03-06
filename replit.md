# CareOrbit — Healthcare AI Platform for Indian Patients

## Overview
CareOrbit is an AI-powered healthcare platform specifically designed for Indian patients. Its primary purpose is to simplify healthcare management by offering features such as AI-driven extraction from medical documents (prescriptions, lab reports, medicine strips), drug interaction detection, identification of care gaps, and multi-agent AI chat in both Hindi and English. The platform also generates health summary PDFs, provides medication reminders, and operates on a tiered subscription model (free, premium individual, premium family). A core ambition is to ensure HIPAA-compliant security through PII encryption and an append-only audit trail. The project aims to enhance patient understanding and adherence to medical advice, ultimately improving health outcomes in India.

## User Preferences
I want the agent to prioritize high-level architectural and design decisions over minute implementation details. When proposing changes, focus on how they align with the overall system architecture and user experience. Ensure that any new features or modifications are accompanied by relevant test cases or updates to the existing test suite, particularly for business logic and API endpoints. I prefer iterative development, with clear communication before major changes are made to the codebase.

## System Architecture
The application uses a Python 3.12 FastAPI backend (port 8000) and a React 18 frontend with Vite 5 and an Express proxy (port 5000). State management is handled by Zustand for authentication and TanStack Query v5 for data fetching. The UI is built with Tailwind CSS 3.4, shadcn/ui components, and Lucide icons. An in-memory session (`InMemorySession`) is used for the database.

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
-   **UI/UX Design:** The application features a premium healthcare aesthetic with a brand-specific color palette (Primary: #FF385C, Secondary: #00A699), Inter and Poppins fonts, enhanced shadows, and softer border-radii. `framer-motion` is used for animations, including `FadeIn`, `ScaleIn`, `SlideIn`, `StaggerContainer`, and `PageTransition` for a smooth user experience. All animations respect `prefers-reduced-motion`.
-   **Test Suite:** 427 passing tests (2 pre-existing OTP failures, 6 skipped). E2e test files contain both Playwright test plan dictionaries (for UI testing via runTest) AND executable pytest backend-verification methods. Sidebar nav testids use `nav-*` prefix (e.g., `nav-dashboard`, `nav-medications`). Sign-out button testid is `button-sign-out` (both sidebar and settings). Theme toggle is `button-theme-toggle` (sidebar) and `button-theme` (settings).
-   **CORS Configuration:** Origins are securely configured via environment variables, defaulting to `localhost` and auto-detecting `REPLIT_DEV_DOMAIN`.

## External Dependencies
The system is designed to integrate with various Azure services, which are currently stubbed out:
-   **Azure Vision:** For AI-driven image analysis (e.g., prescription/lab report/medicine strip photo upload).
-   **Azure OpenAI:** For multi-agent AI chat (GPT-4o).
-   **Azure Translator:** For language translation capabilities.
-   **Azure Language:** For natural language processing tasks.
-   **Azure Blob Storage:** For storing uploaded documents.
-   **Azure Email:** For sending notifications, such as medication reminders.
-   **Azure AI Search:** For RAG-based care gap identification.
-   **Azure KeyVault:** For secure management of keys and secrets.
-   **`pgcrypto`:** For PII encryption.
-   **`python-jose`:** For JWT token handling.
-   **`bcrypt`:** For password hashing.