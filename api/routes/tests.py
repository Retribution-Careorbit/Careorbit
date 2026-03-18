import ast
import os
from fastapi import APIRouter
from db.seed_demo import RAMESH_LABS, RAMESH_VITALS, RAMESH_INTERACTIONS, RAMESH_REMINDERS

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
    labs = {lab.get("name"): lab for lab in RAMESH_LABS}
    latest_bp = [v for v in RAMESH_VITALS if v.get("type") == "blood_pressure"]
    latest_bp_entry = latest_bp[-1] if latest_bp else None
    latest_glucose = [v for v in RAMESH_VITALS if v.get("type") == "glucose"]
    latest_glucose_entry = latest_glucose[-1] if latest_glucose else None

    scenarios = []

    hba1c = labs.get("HbA1c")
    if hba1c and hba1c.get("ref_high") is not None and float(hba1c["value"]) > float(hba1c["ref_high"]):
        scenarios.append({
            "case_id": "scenario-hba1c-threshold",
            "title": "HbA1c Above Clinical Threshold",
            "potential_outcome": "Escalate diabetes intervention and tighten adherence monitoring.",
            "limit_flag": "warning",
            "threshold": f"HbA1c {hba1c['value']}{hba1c.get('unit', '')} > {hba1c['ref_high']}{hba1c.get('unit', '')}",
        })

    egfr = labs.get("eGFR")
    if egfr and egfr.get("ref_low") is not None and float(egfr["value"]) < float(egfr["ref_low"]):
        scenarios.append({
            "case_id": "scenario-egfr-renal-risk",
            "title": "Renal Reserve Reduction",
            "potential_outcome": "Flag nephrology review and medication safety check.",
            "limit_flag": "critical",
            "threshold": f"eGFR {egfr['value']}{egfr.get('unit', '')} < {egfr['ref_low']}{egfr.get('unit', '')}",
        })

    creatinine = labs.get("Creatinine")
    if creatinine and creatinine.get("ref_high") is not None and float(creatinine["value"]) > float(creatinine["ref_high"]):
        scenarios.append({
            "case_id": "scenario-creatinine-rise",
            "title": "Creatinine Above Range",
            "potential_outcome": "Increase kidney safety monitoring and evaluate nephrotoxic exposures.",
            "limit_flag": "warning",
            "threshold": f"Creatinine {creatinine['value']}{creatinine.get('unit', '')} > {creatinine['ref_high']}{creatinine.get('unit', '')}",
        })

    if latest_bp_entry and float(latest_bp_entry.get("systolic", 0)) >= 140:
        scenarios.append({
            "case_id": "scenario-systolic-elevation",
            "title": "Systolic BP Persistently High",
            "potential_outcome": "Prompt antihypertensive adherence and physician dosage reassessment.",
            "limit_flag": "warning",
            "threshold": f"Systolic {latest_bp_entry.get('systolic')} mmHg >= 140 mmHg",
        })

    if latest_glucose_entry and float(latest_glucose_entry.get("fasting", 0)) >= 140:
        scenarios.append({
            "case_id": "scenario-fasting-glucose-high",
            "title": "Fasting Glucose Above Target",
            "potential_outcome": "Add diet-control alert and repeat fasting panel planning.",
            "limit_flag": "monitor",
            "threshold": f"Fasting glucose {latest_glucose_entry.get('fasting')} mg/dL >= 140 mg/dL",
        })

    if any((ix.get("severity") or "").upper() in {"ELEVATED", "HIGH"} for ix in RAMESH_INTERACTIONS):
        scenarios.append({
            "case_id": "scenario-interaction-escalation",
            "title": "High Interaction Burden",
            "potential_outcome": "Require medication substitution discussion to reduce interaction risk.",
            "limit_flag": "critical",
            "threshold": "At least one interaction severity is ELEVATED/HIGH",
        })

    adherence_rate = 0.0
    taken = 0
    missed = 0
    for reminder in RAMESH_REMINDERS:
        taken += int(reminder.get("total_taken", 0) or 0)
        missed += int(reminder.get("total_missed", 0) or 0)
    if (taken + missed) > 0:
        adherence_rate = taken / (taken + missed)
    if adherence_rate < 0.85:
        scenarios.append({
            "case_id": "scenario-adherence-soft-failure",
            "title": "Adherence Below Reliability Band",
            "potential_outcome": "Reduce confidence of projected orbit gains until adherence improves.",
            "limit_flag": "warning",
            "threshold": f"Adherence {adherence_rate:.2f} < 0.85",
        })

    severity_rank = {"critical": 3, "warning": 2, "monitor": 1}
    scenarios.sort(key=lambda s: severity_rank.get(s.get("limit_flag", "monitor"), 0), reverse=True)

    counts: dict[str, int] = {}
    for scenario in scenarios:
        flag = scenario.get("limit_flag", "other")
        counts[flag] = counts.get(flag, 0) + 1

    return {
        "scenarios": scenarios,
        "summary": {
            "total": len(scenarios),
            "by_limit_flag": counts,
        },
    }
