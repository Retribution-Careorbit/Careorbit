"""
E2E UI Test Plans — All Pages Visual Polish
============================================
These test plans are designed to be run via Playwright (runTest).
Each test case documents the steps, selectors, and expected outcomes
for visual polish across all CareOrbit pages.

Test Coverage:
- TC-VIS-001: Medications page — cards with confidence badges
- TC-VIS-002: Medications page — interaction alerts
- TC-VIS-003: Medications page — hover effects and animations
- TC-VIS-004: Documents page — upload zone styling
- TC-VIS-005: Documents page — processing spinner
- TC-VIS-006: Chat page — message bubbles layout
- TC-VIS-007: Chat page — typing indicator and language toggle
- TC-VIS-008: Reminders page — card layout and create dialog
- TC-VIS-009: Settings page — plan cards and theme toggle
- TC-VIS-010: Login/Register pages — entrance animations and branding
- TC-VIS-011: All pages — consistent animation patterns
- TC-VIS-012: All pages — dark mode consistency
- TC-VIS-013: All pages — mobile responsiveness
- TC-VIS-014: Design system — premium color palette applied
- TC-VIS-015: Design system — typography (Inter/Poppins fonts)
"""


PAGES_VISUAL_TEST_PLANS = {
    "TC-VIS-001": {
        "name": "Medications page — cards with confidence badges",
        "steps": [
            "[New Context] Login as Ramesh",
            "[Browser] Navigate to /medications",
            "[Verify] Medication cards are visible (Metformin, Amlodipine, etc.)",
            "[Verify] Each card has a confidence badge with color coding:",
            "  - VERIFIED = green badge",
            "  - HIGH = blue badge",
            "  - MODERATE = yellow/amber badge",
            "  - LOW = red badge",
            "[Verify] Cards show medication name, dosage, and frequency",
            "[Verify] Cards have fade-in animation on load (staggered)",
        ],
    },
    "TC-VIS-002": {
        "name": "Medications page — interaction alerts",
        "steps": [
            "[Browser] On /medications page (Ramesh has drug interaction)",
            "[Verify] Interaction alert is visible for Metformin + Ibuprofen",
            "[Verify] Alert has destructive/warning styling (red border or background)",
            "[Verify] Alert text mentions 'renal' concern",
            "[Verify] AlertTriangle icon is present",
        ],
    },
    "TC-VIS-003": {
        "name": "Medications page — hover effects and animations",
        "steps": [
            "[Browser] On /medications page",
            "[Browser] Hover over a medication card",
            "[Verify] Card lifts slightly (translateY -2 to -4px)",
            "[Verify] Shadow increases on hover",
            "[Verify] Transition is smooth (200-300ms)",
            "[Verify] Cards have gradient accent or colored border per confidence level",
        ],
    },
    "TC-VIS-004": {
        "name": "Documents page — upload zone styling",
        "steps": [
            "[Browser] Navigate to /documents",
            "[Verify] Upload zone is visible with dashed border",
            "[Verify] Upload zone has icon (FileText or Upload)",
            "[Verify] Text says 'Drag and drop' or 'Click to upload'",
            "[Verify] Upload zone has hover state (border color changes)",
            "[Verify] Upload zone has drag-over state (background highlight)",
        ],
    },
    "TC-VIS-005": {
        "name": "Documents page — processing spinner",
        "steps": [
            "[Browser] On /documents page",
            "[Browser] Upload a file",
            "[Verify] Spinner/loading indicator appears while processing",
            "[Verify] Spinner has smooth rotation animation",
            "[Verify] Processing status text updates",
            "[Verify] On completion, result card appears with fade-in",
        ],
    },
    "TC-VIS-006": {
        "name": "Chat page — message bubbles layout",
        "steps": [
            "[Browser] Navigate to /chat",
            "[Verify] Chat container is visible with input area at bottom",
            "[Browser] Type a message and send",
            "[Verify] User message appears as right-aligned bubble with primary color",
            "[Verify] AI response appears as left-aligned bubble with muted color",
            "[Verify] Messages have smooth entrance animation (slide in)",
            "[Verify] Chat auto-scrolls to latest message",
        ],
    },
    "TC-VIS-007": {
        "name": "Chat page — typing indicator and language toggle",
        "steps": [
            "[Browser] On /chat page",
            "[Browser] Send a message",
            "[Verify] Typing indicator appears while AI is processing",
            "[Verify] Typing indicator has animated dots or spinner",
            "[Verify] Language toggle button is visible (English/Hindi)",
            "[Browser] Click language toggle",
            "[Verify] Toggle state changes (button text/icon updates)",
        ],
    },
    "TC-VIS-008": {
        "name": "Reminders page — card layout and create dialog",
        "steps": [
            "[Browser] Navigate to /reminders",
            "[Verify] Page title 'Reminders' is visible",
            "[Verify] 'New Reminder' button is visible",
            "[Browser] Click 'New Reminder' button",
            "[Verify] Create dialog/modal opens with smooth animation",
            "[Verify] Dialog has form fields: medication, time, days",
            "[Verify] Day badges (Mon-Sun) are interactive",
            "[Browser] Close dialog",
            "[Verify] Dialog closes with smooth animation",
        ],
    },
    "TC-VIS-009": {
        "name": "Settings page — plan cards and theme toggle",
        "steps": [
            "[Browser] Navigate to /settings",
            "[Verify] [data-testid='text-settings-title'] shows 'Settings'",
            "[Verify] Profile card shows user email [data-testid='text-profile-email']",
            "[Verify] Subscription plan cards are visible",
            "[Verify] Current plan has 'Current' badge and highlighted border",
            "[Verify] Theme toggle [data-testid='button-theme'] is visible",
            "[Browser] Click theme toggle",
            "[Verify] Theme changes with smooth transition",
            "[Verify] Sign out button [data-testid='button-sign-out'] at bottom",
        ],
        "selectors": {
            "title": "text-settings-title",
            "email": "text-profile-email",
            "theme": "button-theme",
            "sign_out": "button-sign-out",
        },
    },
    "TC-VIS-010": {
        "name": "Login/Register pages — entrance animations and branding",
        "steps": [
            "[New Context] Create unauthenticated browser context",
            "[Browser] Navigate to / (login page)",
            "[Verify] CareOrbit logo (Heart icon) is visible",
            "[Verify] Login card has fade-in entrance animation",
            "[Verify] Form fields are styled with consistent padding/borders",
            "[Verify] 'Sign In' button uses primary brand color",
            "[Browser] Navigate to /register",
            "[Verify] Register card has similar entrance animation",
            "[Verify] Branding is consistent with login page",
        ],
    },
    "TC-VIS-011": {
        "name": "All pages — consistent animation patterns",
        "steps": [
            "[Browser] Navigate through each page in sequence",
            "[Verify] Every page has fade-in entrance animation on route change",
            "[Verify] Cards/lists have stagger animation (items appear one by one)",
            "[Verify] Animation timing is consistent (200-300ms per element)",
            "[Verify] No janky or skipped animations",
            "[Verify] Animations feel smooth at 60fps",
        ],
        "pages_to_check": ["/", "/medications", "/documents", "/chat", "/reminders", "/settings"],
    },
    "TC-VIS-012": {
        "name": "All pages — dark mode consistency",
        "steps": [
            "[Browser] Toggle to dark mode",
            "[Browser] Navigate to each page",
            "[Verify] Background is dark (#0A0A0A or similar)",
            "[Verify] Card backgrounds are slightly lighter (#1A1A1A or #2A2A2A)",
            "[Verify] Text is light and readable (white/light gray)",
            "[Verify] Primary brand color (pink/red) remains consistent",
            "[Verify] No elements have white backgrounds in dark mode",
            "[Verify] All borders/dividers adapt to dark theme",
            "[Verify] Icons are visible against dark backgrounds",
        ],
        "pages_to_check": ["/", "/medications", "/documents", "/chat", "/reminders", "/settings"],
    },
    "TC-VIS-013": {
        "name": "All pages — mobile responsiveness",
        "viewport": {"width": 400, "height": 720},
        "steps": [
            "[Browser] Set viewport to 400x720",
            "[Browser] Navigate to each page",
            "[Verify] Content fills viewport without horizontal scroll",
            "[Verify] Text is readable (no overflow/truncation of critical info)",
            "[Verify] Buttons and interactive elements are at least 44px tall",
            "[Verify] Forms are usable (inputs are full-width on mobile)",
            "[Verify] Sidebar is collapsed with hamburger trigger",
            "[Verify] Cards stack vertically in single column",
        ],
        "pages_to_check": ["/", "/medications", "/documents", "/chat", "/reminders", "/settings"],
    },
    "TC-VIS-014": {
        "name": "Design system — premium color palette applied",
        "steps": [
            "[Browser] Navigate to dashboard",
            "[Verify] Primary color is #FF385C (vibrant pink/red) on buttons and accents",
            "[Verify] Secondary/teal color #00A699 used for medical/health elements",
            "[Verify] Background is clean white (#FFFFFF) or light gray (#F7F7F7)",
            "[Verify] Text colors are #1A1A1A (primary) and #717171 (secondary)",
            "[Verify] Cards have subtle shadows and soft border-radius (12-16px)",
            "[Browser] Toggle to dark mode",
            "[Verify] Background is near-black (#0A0A0A)",
            "[Verify] Cards are #2A2A2A with subtle borders",
            "[Verify] Primary accent color remains vibrant",
        ],
    },
    "TC-VIS-015": {
        "name": "Design system — typography (Inter/Poppins fonts)",
        "steps": [
            "[Browser] Navigate to dashboard",
            "[Verify] Body text uses 'Inter' font family",
            "[Verify] Headings use 'Poppins' font family",
            "[Verify] Font sizes follow hierarchy:",
            "  - Page title: ~2rem (32px)",
            "  - Card titles: ~1.25rem (20px)",
            "  - Body text: 1rem (16px)",
            "  - Small/muted text: 0.875rem (14px)",
            "[Verify] Font weights: headings bold (600-700), body regular (400)",
            "[Verify] Line heights are comfortable (1.5 for body text)",
        ],
    },
}
