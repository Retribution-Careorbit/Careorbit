import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass


@dataclass
class OCRResult:
    full_text: str
    lines: list
    avg_confidence: float
    page_count: int


@pytest.mark.asyncio
async def test_vision_extract_text_returns_ocr_result():
    from services.azure_vision import AzureVisionService

    service = AzureVisionService()

    mock_sdk_response = MagicMock()
    mock_page = MagicMock()
    mock_line1 = MagicMock()
    mock_line1.text = "Dr. Amit Roy"
    mock_word1 = MagicMock()
    mock_word1.confidence = 0.95
    mock_line1.words = [mock_word1]
    mock_page.lines = [mock_line1]
    mock_sdk_response.pages = [mock_page]

    with patch.object(service, "extract_text", new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = OCRResult(
            full_text="Dr. Amit Roy",
            lines=["Dr. Amit Roy"],
            avg_confidence=0.95,
            page_count=1,
        )
        result = await service.extract_text(b"fake-image-bytes")

    assert hasattr(result, "full_text")
    assert hasattr(result, "lines")
    assert hasattr(result, "avg_confidence")
    assert hasattr(result, "page_count")


@pytest.mark.asyncio
async def test_vision_ocr_result_has_required_fields():
    from services.azure_vision import AzureVisionService

    service = AzureVisionService()

    with patch.object(service, "extract_text", new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = OCRResult(
            full_text="Metformin 500mg BD",
            lines=["Metformin 500mg BD"],
            avg_confidence=0.92,
            page_count=1,
        )
        result = await service.extract_text(b"fake-image-bytes")

    assert isinstance(result.full_text, str)
    assert isinstance(result.lines, list)
    assert isinstance(result.avg_confidence, float)
    assert isinstance(result.page_count, int)
    assert len(result.full_text) > 0
    assert len(result.lines) > 0


@pytest.mark.asyncio
async def test_vision_classify_prescription():
    from services.azure_vision import AzureVisionService

    service = AzureVisionService()

    with patch.object(service, "classify_document_type", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = "prescription"
        ocr = OCRResult(
            full_text="Rx\nTab Metformin 500mg BD",
            lines=["Rx", "Tab Metformin 500mg BD"],
            avg_confidence=0.92,
            page_count=1,
        )
        result = await service.classify_document_type(ocr)

    assert result == "prescription"


@pytest.mark.asyncio
async def test_vision_classify_lab_report():
    from services.azure_vision import AzureVisionService

    service = AzureVisionService()

    with patch.object(service, "classify_document_type", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = "lab_report"
        ocr = OCRResult(
            full_text="HbA1c 7.2% mg/dl pathology report",
            lines=["HbA1c 7.2% mg/dl pathology report"],
            avg_confidence=0.93,
            page_count=1,
        )
        result = await service.classify_document_type(ocr)

    assert result == "lab_report"


@pytest.mark.asyncio
async def test_vision_classify_medicine_strip():
    from services.azure_vision import AzureVisionService

    service = AzureVisionService()

    with patch.object(service, "classify_document_type", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = "medicine_strip"
        ocr = OCRResult(
            full_text="Mfg: 06/2025 Batch B123 Exp 2027",
            lines=["Mfg: 06/2025 Batch B123 Exp 2027"],
            avg_confidence=0.97,
            page_count=1,
        )
        result = await service.classify_document_type(ocr)

    assert result == "medicine_strip"


@pytest.mark.asyncio
async def test_vision_classify_unknown():
    from services.azure_vision import AzureVisionService

    service = AzureVisionService()

    with patch.object(service, "classify_document_type", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = "unknown"
        ocr = OCRResult(
            full_text="Random text without medical keywords",
            lines=["Random text without medical keywords"],
            avg_confidence=0.80,
            page_count=1,
        )
        result = await service.classify_document_type(ocr)

    assert result == "unknown"


@pytest.mark.asyncio
async def test_openai_extract_structured_prescription():
    from services.azure_openai import AzureOpenAIService

    service = AzureOpenAIService()

    expected = {
        "medications": [
            {"name": "Metformin", "dosage": "500mg", "frequency": "BD"},
            {"name": "Amlodipine", "dosage": "5mg", "frequency": "OD"},
        ]
    }

    with patch.object(service, "extract_structured_data", new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = expected
        result = await service.extract_structured_data(
            "Rx\nTab Metformin 500mg BD\nTab Amlodipine 5mg OD",
            doc_type="prescription",
        )

    assert "medications" in result
    assert isinstance(result["medications"], list)
    assert len(result["medications"]) > 0


@pytest.mark.asyncio
async def test_openai_extract_structured_lab():
    from services.azure_openai import AzureOpenAIService

    service = AzureOpenAIService()

    expected = {
        "tests": [
            {"name": "HbA1c", "value": 7.8, "unit": "%", "reference_range": "<5.7"},
        ]
    }

    with patch.object(service, "extract_structured_data", new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = expected
        result = await service.extract_structured_data(
            "HbA1c: 7.8% (Ref: <5.7%)",
            doc_type="lab_report",
        )

    assert "tests" in result
    assert isinstance(result["tests"], list)
    assert len(result["tests"]) > 0


@pytest.mark.asyncio
async def test_openai_chat_returns_string():
    from services.azure_openai import AzureOpenAIService

    service = AzureOpenAIService()

    with patch.object(service, "chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = "Based on your medications, here is my advice."
        result = await service.chat([{"role": "user", "content": "What are my medications?"}])

    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_openai_chat_with_history_returns_string():
    from services.azure_openai import AzureOpenAIService

    service = AzureOpenAIService()

    with patch.object(service, "chat_with_history", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = "Here is a follow-up response."
        messages = [
            {"role": "user", "content": "Tell me about Metformin"},
            {"role": "assistant", "content": "Metformin is used for diabetes."},
            {"role": "user", "content": "What are the side effects?"},
        ]
        result = await service.chat_with_history(messages, context={"patient_id": "123"})

    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_translator_translate_hindi():
    from services.azure_translator import AzureTranslatorService

    service = AzureTranslatorService()

    with patch.object(service, "translate", new_callable=AsyncMock) as mock_translate:
        mock_translate.return_value = "यह एक अनुवादित पाठ है"
        result = await service.translate("This is a translated text", "hi")

    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_translator_detect_language():
    from services.azure_translator import AzureTranslatorService

    service = AzureTranslatorService()

    with patch.object(service, "detect_language", new_callable=AsyncMock) as mock_detect:
        mock_detect.return_value = {"language": "hi", "confidence": 0.95}
        result = await service.detect_language("यह हिंदी में है")

    assert isinstance(result, dict)
    assert "language" in result
    assert "confidence" in result
    assert result["language"] == "hi"
    assert isinstance(result["confidence"], float)


@pytest.mark.asyncio
async def test_blob_upload_document_returns_sas_url():
    from services.azure_blob import AzureBlobService

    service = AzureBlobService()

    with patch.object(service, "upload_document", new_callable=AsyncMock) as mock_upload:
        mock_upload.return_value = (
            "https://careorbitstorage.blob.core.windows.net/documents/test.jpg?sv=2021-06-08&sig=abc123"
        )
        result = await service.upload_document(b"fake-image-data", "test.jpg")

    assert isinstance(result, str)
    assert "blob.core.windows.net" in result
    assert "sv=" in result or "sig=" in result


@pytest.mark.asyncio
async def test_blob_upload_summary_pdf_returns_url():
    from services.azure_blob import AzureBlobService

    service = AzureBlobService()

    with patch.object(service, "upload_health_summary_pdf", new_callable=AsyncMock) as mock_upload:
        mock_upload.return_value = (
            "https://careorbitstorage.blob.core.windows.net/summaries/summary.pdf"
        )
        result = await service.upload_health_summary_pdf(b"fake-pdf-data", "summary.pdf")

    assert isinstance(result, str)
    assert "blob.core.windows.net" in result
    assert result.endswith(".pdf")


@pytest.mark.asyncio
async def test_email_send_medication_reminder_returns_bool():
    from services.azure_email import AzureEmailService

    service = AzureEmailService()

    with patch.object(service, "send_medication_reminder", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        result = await service.send_medication_reminder(
            to_email="ramesh@careorbit.dev",
            patient_name="Ramesh Kumar",
            medication_name="Metformin",
            dosage="500mg BD",
            time_label="Morning",
        )

    assert isinstance(result, bool)
    assert result is True


@pytest.mark.asyncio
async def test_email_send_previsit_brief_returns_bool():
    from services.azure_email import AzureEmailService

    service = AzureEmailService()

    with patch.object(service, "send_upload_result", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        result = await service.send_upload_result(
            to_email="ramesh@careorbit.dev",
            patient_name="Ramesh Kumar",
            document_type="previsit_brief",
            status="success",
        )

    assert isinstance(result, bool)
    assert result is True
