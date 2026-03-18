import ast
import os
from fastapi import APIRouter
from db.seed_demo import RAMESH_TEST_SCENARIOS

router = APIRouter(prefix="/api/tests", tags=["tests"])

NEW_TEST_FILES = {
    "test_orbit_score.py",
    "test_previsit_agent.py",
    "test_living_narrative.py",
    "test_api_orbit.py",
    "test_azure_services.py",
    "test_pipeline_extractors.py",
    "test_fhir_converter.py",
    "test_orbit_integration.py",
    "test_reminder_scheduler.py",
    "test_orbit_journey.py",
    "test_orbit_rbac.py",
    "test_orbit_weights.py",
}

FEATURE_MAP = {
    "test_orbit_score": "Orbit Score Engine",
    "test_previsit_agent": "Pre-Visit Brief",
    "test_living_narrative": "Living Narrative",
    "test_api_orbit": "Orbit API Endpoints",
    "test_azure_services": "Azure Service Wrappers",
    "test_pipeline_extractors": "Pipeline Extractors",
    "test_fhir_converter": "FHIR Conversion",
    "test_orbit_integration": "Orbit Integration Flow",
    "test_reminder_scheduler": "Reminder Scheduler",
    "test_orbit_journey": "Orbit E2E Journey",
    "test_orbit_rbac": "Orbit RBAC Security",
    "test_orbit_weights": "Orbit Weight Validation",
    "test_confidence_scoring": "Confidence Scoring",
    "test_drug_database": "Drug Database",
    "test_auth_tokens": "Auth Tokens",
    "test_encryption": "Encryption",
    "test_document_state_machine": "Document Pipeline",
    "test_orchestrator": "Multi-Agent Orchestrator",
    "test_api_auth": "Auth API",
    "test_api_caregivers": "Caregivers API",
    "test_api_confirmations": "Confirmations API",
    "test_api_documents_boundaries": "Document Upload Boundaries",
    "test_api_documents": "Document Upload API",
    "test_api_health": "Health Check API",
    "test_api_otp": "OTP Verification",
    "test_api_reminders": "Reminders API",
    "test_api_subscriptions": "Subscriptions API",
    "test_api_summary": "Summary PDF API",
    "test_patient_journey_ramesh": "Patient E2E Journey",
    "test_interaction_false_negatives": "Interaction False Negatives",
    "test_interaction_false_positives": "Interaction False Positives",
    "test_rbac_enforcement": "RBAC Enforcement",
    "test_cross_patient_rbac": "Cross-Patient RBAC",
    "test_rate_limiting": "Rate Limiting",
    "test_refresh_token_security": "Refresh Token Security",
    "test_audit_trail": "Audit Trail",
    "test_audit_append_only": "Audit Append-Only",
    "test_password_change_revocation": "Password Change Revocation",
    "test_rbac_permission_levels": "RBAC Permission Levels",
    "test_lab_trend_edge_cases": "Lab Trend Edge Cases",
    "test_tier_config": "Tier Configuration",
    "coverage_matrix": "Coverage Matrix Validation",
}


def _extract_tests_from_file(filepath: str) -> list[str]:
    try:
        with open(filepath, "r") as f:
            source = f.read()
        tree = ast.parse(source)
    except (SyntaxError, FileNotFoundError):
        return []

    test_names = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                test_names.append(node.name)
    return test_names


def _get_category(dir_name: str) -> str:
    category_map = {
        "unit": "unit",
        "functional": "functional",
        "integration": "integration",
        "e2e": "e2e",
        "security": "security",
        "business_logic": "business_logic",
        "regression": "regression",
        "false_positive_negative": "false_positive_negative",
    }
    return category_map.get(dir_name, "other")


@router.get("/cases")
async def get_test_cases():
    tests_root = os.path.join(os.path.dirname(__file__), "..", "..", "tests")
    tests_root = os.path.normpath(tests_root)
    test_cases = []

    for dirpath, _, filenames in os.walk(tests_root):
        for filename in sorted(filenames):
            if not filename.endswith(".py"):
                continue
            if not filename.startswith("test_") and filename != "coverage_matrix.py":
                continue

            filepath = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(filepath, os.path.join(tests_root, ".."))
            dir_name = os.path.basename(dirpath)
            category = _get_category(dir_name)
            stem = filename.replace(".py", "")
            feature = FEATURE_MAP.get(stem, stem.replace("test_", "").replace("_", " ").title())
            is_new = filename in NEW_TEST_FILES

            func_names = _extract_tests_from_file(filepath)
            for func_name in func_names:
                test_cases.append({
                    "name": func_name,
                    "file_path": rel_path,
                    "category": category,
                    "feature_area": feature,
                    "is_new": is_new,
                })

    by_category: dict[str, int] = {}
    new_count = 0
    existing_count = 0
    for tc in test_cases:
        by_category[tc["category"]] = by_category.get(tc["category"], 0) + 1
        if tc["is_new"]:
            new_count += 1
        else:
            existing_count += 1

    return {
        "tests": test_cases,
        "summary": {
            "total": len(test_cases),
            "new_count": new_count,
            "existing_count": existing_count,
            "by_category": by_category,
        },
    }


@router.get("/scenarios")
async def get_test_scenarios():
    counts: dict[str, int] = {}
    for scenario in RAMESH_TEST_SCENARIOS:
        flag = scenario.get("limit_flag", "other")
        counts[flag] = counts.get(flag, 0) + 1

    return {
        "scenarios": RAMESH_TEST_SCENARIOS,
        "summary": {
            "total": len(RAMESH_TEST_SCENARIOS),
            "by_limit_flag": counts,
        },
    }
