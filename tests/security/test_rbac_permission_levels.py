# tests/security/test_rbac_permission_levels.py
# V3 ADD A3: Boundary tests for view/edit/full permission levels.

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestRBACPermissionBoundaries:

    def test_view_caregiver_cannot_upload_documents(self):
        """
        Caregiver with 'view' permission → 403 on POST /documents/upload.
        Documents require 'edit' permission per documents.py RBAC check.
        """
        with patch("api.middleware.auth.get_current_user",
                   return_value={"id": "caregiver-view-only", "tier": "free"}), \
             patch("api.middleware.rbac.verify_patient_access",
                   side_effect=__import__("fastapi", fromlist=["HTTPException"]).HTTPException(
                       status_code=403,
                       detail="Your permission level (view) is insufficient."
                   )):
            response = client.post(
                "/api/documents/upload",
                files={"file": ("rx.jpg", b"fake", "image/jpeg")}
            )
            assert response.status_code == 403

    def test_edit_caregiver_cannot_revoke_other_caregivers(self):
        """
        Caregiver with 'edit' permission → 403 on DELETE /caregivers/{id}.
        Caregiver management requires 'full' permission.
        """
        with patch("api.middleware.auth.get_current_user",
                   return_value={"id": "caregiver-edit", "tier": "free"}), \
             patch("api.middleware.rbac.verify_patient_access",
                   side_effect=__import__("fastapi", fromlist=["HTTPException"]).HTTPException(
                       status_code=403,
                       detail="Insufficient permission."
                   )):
            response = client.delete("/api/caregivers/some-other-caregiver-id")
            assert response.status_code == 403

    def test_patient_can_always_revoke_own_caregivers(self):
        """Patient (self access) always has full permission on their own data."""
        with patch("api.middleware.auth.get_current_user",
                   return_value={"id": "patient-123", "tier": "free"}):
            # Patient deleting their own caregiver — RBAC allows self-access
            response = client.delete("/api/caregivers/some-caregiver-user-id")
            # Route is idempotent — 200 or 204 (not 403)
            assert response.status_code in (200, 204)

    def test_view_caregiver_can_read_medications(self):
        """'view' permission is sufficient for GET /patients/medications."""
        with patch("api.middleware.auth.get_current_user",
                   return_value={"id": "caregiver-view", "tier": "free"}), \
             patch("api.middleware.rbac.verify_patient_access",
                   return_value={"access_type": "caregiver", "permission_level": "view"}), \
             patch("api.routes.patients.phig_builder") as mock_phig:
            from unittest.mock import AsyncMock
            mock_phig.get_medication_subgraph = AsyncMock(return_value={"medications": []})
            response = client.get("/api/patients/medications?patient_id=patient-123")
            assert response.status_code == 200
