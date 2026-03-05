class AzureVisionService:
    async def extract_text(self, image_bytes):
        raise NotImplementedError("Azure Vision not configured")

    async def classify_document_type(self, ocr_result):
        raise NotImplementedError("Azure Vision not configured")
