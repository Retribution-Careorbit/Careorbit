import pytest

COVERAGE_MATRIX = {
    "P0-01: Prescription Photo Upload + AI Extraction": {
        "unit": ["test_confidence_scoring.py", "test_drug_database.py"],
        "integration": ["test_document_state_machine.py"],
        "functional": ["test_api_documents.py", "test_api_documents_boundaries.py"],
        "e2e": ["test_patient_journey_ramesh.py::test_step2_upload_prescription"],
    },
    "P0-02: Medicine Strip Photo Recognition": {
        "unit": ["test_drug_database.py::TestFuzzyMatching"],
        "integration": ["test_document_state_machine.py"],
    },
    "P0-03: Lab Report Photo Extraction": {
        "unit": ["test_confidence_scoring.py::TestLabConfidence"],
        "integration": ["test_document_state_machine.py"],
        "e2e": ["test_patient_journey_ramesh.py::test_step4_upload_lab_report"],
    },
    "P0-04: PHIG Construction + FHIR R4": {
        "integration": ["test_document_state_machine.py"],
        "e2e": ["test_patient_journey_ramesh.py"],
    },
    "P0-05: Deterministic Confidence Scoring": {
        "unit": ["test_confidence_scoring.py"],
        "regression": ["test_lab_trend_edge_cases.py"],
    },
    "P0-06: Medication Agent (Drug Interactions + Severity)": {
        "integration": ["test_orchestrator.py"],
        "false_positive": ["test_interaction_false_positives.py"],
        "false_negative": ["test_interaction_false_negatives.py"],
        "e2e": ["test_patient_journey_ramesh.py::test_step3_upload_ibuprofen_triggers_interaction"],
    },
    "P0-07: Care Gap Agent (RAG-Based)": {
        "integration": ["test_orchestrator.py"],
        "false_positive": ["test_interaction_false_positives.py"],
        "false_negative": ["test_interaction_false_negatives.py"],
        "e2e": ["test_patient_journey_ramesh.py::test_step6_care_gaps"],
    },
    "P0-08: Orchestrator (Multi-Agent Routing)": {
        "integration": ["test_orchestrator.py"],
        "e2e": ["test_patient_journey_ramesh.py::test_step8_chat_english",
                "test_patient_journey_ramesh.py::test_step8b_chat_hindi"],
    },
    "P0-09: Health Summary PDF Generation": {
        "functional": ["test_api_summary.py"],
        "e2e": ["test_patient_journey_ramesh.py::test_step7_generate_summary_pdf"],
    },
    "P0-10: Healthcare-Grade Auth": {
        "unit": ["test_auth_tokens.py", "test_encryption.py"],
        "functional": ["test_api_auth.py"],
        "security": ["test_rbac_enforcement.py", "test_rate_limiting.py",
                     "test_refresh_token_security.py", "test_audit_trail.py",
                     "test_cross_patient_rbac.py",
                     "test_password_change_revocation.py",
                     "test_audit_append_only.py",
                     "test_rbac_permission_levels.py"],
    },
    "P0-11: Patient Confirmation Flow": {
        "functional": ["test_api_confirmations.py"],
        "integration": ["test_document_state_machine.py"],
    },
    "P0-12: Hindi + English Support": {
        "integration": ["test_orchestrator.py::test_hindi_query_invokes_translator"],
        "e2e": ["test_patient_journey_ramesh.py::test_step8b_chat_hindi"],
    },
    "P0-13: Email Medication Reminders": {
        "functional": ["test_api_reminders.py"],
        "integration": ["test_api_reminders.py::TestReminderEmailIntegration"],
    },
    "P0-14: Web Dashboard + Tier System (Config)": {
        "business_logic": ["test_tier_config.py"],
        "functional": ["test_api_health.py", "test_api_subscriptions.py"],
    },
    "P0-15: History Agent (Promoted from P1 in v0.3.0)": {
        "integration": ["test_orchestrator.py"],
        "e2e": ["test_patient_journey_ramesh.py"],
    },
    "P0-16: Lab Value Trend Visualization (Promoted from P1 in v0.3.0)": {
        "regression": ["test_lab_trend_edge_cases.py"],
        "e2e": ["test_patient_journey_ramesh.py"],
    },
    "P0-17: Medication Adherence Tracking (Promoted from P1 in v0.3.0)": {
        "functional": ["test_api_reminders.py"],
        "e2e": ["test_patient_journey_ramesh.py"],
    },
    "P1-01: Family Caregiver Dashboard View": {
        "functional": ["test_api_caregivers.py"],
        "security": ["test_rbac_permission_levels.py", "test_cross_patient_rbac.py"],
    },
}


class TestCoverageCompleteness:

    @pytest.mark.parametrize("feature,tests", COVERAGE_MATRIX.items())
    def test_feature_has_multiple_test_types(self, feature, tests):
        assert len(tests) >= 2, \
            f"Feature '{feature}' has only {len(tests)} test category/ies"

    def test_all_17_p0_features_covered(self):
        p0_features = [k for k in COVERAGE_MATRIX if k.startswith("P0")]
        assert len(p0_features) == 17, \
            f"Expected 17 P0 features (14 original + 3 promoted), " \
            f"found {len(p0_features)}: {p0_features}"

    def test_p1_count_after_promotions(self):
        p1_features = [k for k in COVERAGE_MATRIX if k.startswith("P1")]
        assert len(p1_features) == 1, \
            f"Expected 1 P1 feature, found {len(p1_features)}: {p1_features}"

    def test_safety_features_have_false_positive_and_false_negative_tests(self):
        for prefix in ("P0-06", "P0-07"):
            features = [k for k in COVERAGE_MATRIX if k.startswith(prefix)]
            for feature in features:
                tests = COVERAGE_MATRIX[feature]
                assert "false_positive" in tests, \
                    f"{feature} missing false_positive tests (safety-critical)"
                assert "false_negative" in tests, \
                    f"{feature} missing false_negative tests (safety-critical)"

    def test_p0_10_auth_has_security_test_suite(self):
        auth = COVERAGE_MATRIX.get("P0-10: Healthcare-Grade Auth", {})
        security_tests = auth.get("security", [])
        assert len(security_tests) >= 5, \
            "Auth (P0-10) must have at least 5 security test files"
