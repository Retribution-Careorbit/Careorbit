# tests/integration/test_document_state_machine.py
# V4 FIX V4-9: Renamed test_pending_to_processing_on_upload
#              to test_upload_produces_terminal_status.
# 'processing' is an unobservable internal state — process_document()
# always returns a terminal state.

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from pipeline.document_pipeline import DocumentPipeline


@pytest.fixture
def pipeline(mock_openai, mock_vision, mock_blob, mock_search, mock_email):
    with patch("pipeline.document_pipeline.openai_service", mock_openai), \
         patch("pipeline.document_pipeline.vision_service", mock_vision), \
         patch("pipeline.document_pipeline.blob_service", mock_blob), \
         patch("pipeline.document_pipeline.search_service", mock_search), \
         patch("pipeline.document_pipeline.email_service", mock_email), \
         patch("pipeline.document_pipeline.db_session", AsyncMock()):
        yield DocumentPipeline()


TERMINAL_STATES = {"success", "needs_confirmation", "failed"}


class TestDocumentStateMachine:
    """Tests the 5-state processing lifecycle."""

    async def test_upload_produces_terminal_status(self, pipeline, mock_vision, mock_openai):
        """
        V4-9 RENAME: Was 'test_pending_to_processing_on_upload'.
        'processing' is an internal intermediate state, never returned
        by process_document(). Result is always a terminal state.
        """
        mock_vision.extract_text.return_value = MagicMock(
            full_text="Metformin 500mg BD", lines=["Metformin 500mg BD"],
            avg_confidence=0.94, page_count=1
        )
        mock_vision.classify_document_type.return_value = "prescription"
        mock_openai.extract_structured_data.return_value = {
            "medications": [{"name": "Metformin", "dosage": "500mg", "frequency": "BD"}],
            "doctor_name": "", "diagnoses": [], "date": ""
        }
        result = await pipeline.process_document(
            image_bytes=b"fake", patient_id="test",
            uploaded_by="test", file_extension="jpg"
        )
        assert result.processing_status in TERMINAL_STATES, \
            f"Expected terminal state, got: {result.processing_status}"

    async def test_processing_to_success_high_confidence(self, pipeline, mock_vision, mock_openai):
        """All meds above confidence threshold → status='success'."""
        mock_vision.extract_text.return_value = MagicMock(
            full_text="Metformin 500mg BD", lines=["Metformin 500mg BD"],
            avg_confidence=0.95, page_count=1
        )
        mock_vision.classify_document_type.return_value = "prescription"
        mock_openai.extract_structured_data.return_value = {
            "medications": [{"name": "Metformin", "dosage": "500mg", "frequency": "BD"}],
            "doctor_name": "Dr. Roy", "diagnoses": ["DM"], "date": "15/01/2026"
        }
        result = await pipeline.process_document(
            image_bytes=b"fake", patient_id="test",
            uploaded_by="test", file_extension="jpg"
        )
        assert result.processing_status == "success"

    async def test_processing_to_needs_confirmation_low_confidence(
        self, pipeline, mock_vision, mock_openai
    ):
        """Any med below confidence threshold → status='needs_confirmation'."""
        mock_vision.extract_text.return_value = MagicMock(
            full_text="Glycomet 5OOmg BD", lines=["Glycomet 5OOmg BD"],
            avg_confidence=0.55, page_count=1
        )
        mock_vision.classify_document_type.return_value = "prescription"
        mock_openai.extract_structured_data.return_value = {
            "medications": [{"name": "Glycomet", "dosage": "500mg", "frequency": "BD"}],
            "doctor_name": "", "diagnoses": [], "date": ""
        }
        result = await pipeline.process_document(
            image_bytes=b"fake", patient_id="test",
            uploaded_by="test", file_extension="jpg"
        )
        assert result.processing_status == "needs_confirmation"

    async def test_processing_to_failed_on_vision_error(self, pipeline, mock_vision):
        """Vision service error → status='failed'."""
        mock_vision.extract_text.side_effect = Exception("Azure Vision timeout")
        result = await pipeline.process_document(
            image_bytes=b"fake", patient_id="test",
            uploaded_by="test", file_extension="jpg"
        )
        assert result.processing_status == "failed"
        assert result.error_message is not None

    async def test_processing_to_failed_on_unreadable_document(self, pipeline, mock_vision):
        """OCR avg_confidence < 0.30 → status='failed', document_type='unreadable'."""
        mock_vision.classify_document_type.return_value = "unreadable"
        mock_vision.extract_text.return_value = MagicMock(
            full_text="", lines=[], avg_confidence=0.10, page_count=1
        )
        result = await pipeline.process_document(
            image_bytes=b"fake", patient_id="test",
            uploaded_by="test", file_extension="jpg"
        )
        assert result.processing_status == "failed"
        assert result.document_type == "unreadable"

    async def test_failed_result_has_error_message(self, pipeline, mock_vision):
        """Every failed result must have a user-readable error_message."""
        mock_vision.extract_text.side_effect = Exception("Connection error")
        result = await pipeline.process_document(
            image_bytes=b"fake", patient_id="test",
            uploaded_by="test", file_extension="jpg"
        )
        assert result.processing_status == "failed"
        assert isinstance(result.error_message, str)
        assert len(result.error_message) > 0
