import logging
import uuid
from config import get_settings

logger = logging.getLogger("careorbit.services.blob")


class AzureBlobService:
    def __init__(self):
        settings = get_settings()
        self._connection_string = settings.AZURE_BLOB_CONNECTION_STRING
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not self._connection_string:
            return None
        try:
            from azure.storage.blob import BlobServiceClient
            self._client = BlobServiceClient.from_connection_string(self._connection_string)
            return self._client
        except Exception as e:
            logger.warning(f"Failed to initialize Blob client: {e}")
            return None

    async def upload_document(self, data, name):
        client = self._get_client()
        if not client:
            raise NotImplementedError("Azure Blob not configured")

        try:
            container_name = "patient-documents"
            container_client = client.get_container_client(container_name)
            try:
                container_client.get_container_properties()
            except Exception:
                container_client.create_container()

            blob_name = f"{uuid.uuid4()}/{name}"
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob(data, overwrite=True)

            url = blob_client.url
            logger.info(f"Document uploaded to {url}")
            return url
        except Exception as e:
            logger.error(f"Blob upload failed: {e}")
            raise

    async def upload_health_summary_pdf(self, data, name):
        client = self._get_client()
        if not client:
            raise NotImplementedError("Azure Blob not configured")

        try:
            container_name = "health-exports"
            container_client = client.get_container_client(container_name)
            try:
                container_client.get_container_properties()
            except Exception:
                container_client.create_container()

            blob_name = f"exports/{uuid.uuid4()}/{name}"
            blob_client = container_client.get_blob_client(blob_name)
            from azure.storage.blob import ContentSettings
            blob_client.upload_blob(data, overwrite=True, content_settings=ContentSettings(
                content_type="application/pdf"
            ))

            url = blob_client.url
            logger.info(f"Health summary PDF uploaded to {url}")
            return url
        except Exception as e:
            logger.error(f"Health summary PDF upload failed: {e}")
            raise
