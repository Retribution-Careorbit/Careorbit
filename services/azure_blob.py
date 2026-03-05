class AzureBlobService:
    async def upload_document(self, data, name):
        raise NotImplementedError("Azure Blob not configured")

    async def upload_health_summary_pdf(self, data, name):
        raise NotImplementedError("Azure Blob not configured")
