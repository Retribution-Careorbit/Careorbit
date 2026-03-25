import logging
import uuid
from datetime import datetime, timedelta, timezone
from config import get_settings

logger = logging.getLogger("careorbit.services.blob")


class AzureBlobService:
    def __init__(self):
        settings = get_settings()
        self._connection_string = settings.AZURE_BLOB_CONNECTION_STRING
        self._client = None
        self._conn_parts = self._parse_connection_string(self._connection_string)

    @staticmethod
    def _parse_connection_string(connection_string: str | None) -> dict[str, str]:
        if not connection_string:
            return {}
        parts: dict[str, str] = {}
        for chunk in str(connection_string).split(";"):
            if "=" not in chunk:
                continue
            key, value = chunk.split("=", 1)
            parts[key.strip()] = value.strip()
        return parts

    @staticmethod
    def _container_for_document_type(document_type: str | None) -> str:
        doc_type = str(document_type or "").strip().lower()
        if doc_type == "lab_report":
            return "lab-reports"
        if doc_type == "prescription":
            return "prescriptions"
        return "prescriptions"

    @staticmethod
    def _sanitize_segment(value: str) -> str:
        cleaned = "".join(ch if ch.isalnum() else "_" for ch in str(value or "").strip())
        return cleaned.strip("_").lower() or "document"

    def _build_blob_name(self, *, patient_id: str, filename: str) -> str:
        patient_segment = self._sanitize_segment(patient_id)
        if "." in filename:
            stem, ext = filename.rsplit(".", 1)
            stem_segment = self._sanitize_segment(stem)
            ext_segment = self._sanitize_segment(ext)
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            return f"{patient_segment}_{stem_segment}_{ts}_{uuid.uuid4().hex[:8]}.{ext_segment}"
        stem_segment = self._sanitize_segment(filename)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"{patient_segment}_{stem_segment}_{ts}_{uuid.uuid4().hex[:8]}"

    def _build_read_url(self, container_name: str, blob_name: str, blob_client) -> str:
        account_name = self._conn_parts.get("AccountName")
        account_key = self._conn_parts.get("AccountKey")
        if not account_name or not account_key:
            return blob_client.url

        try:
            from azure.storage.blob import BlobSasPermissions, generate_blob_sas

            sas = generate_blob_sas(
                account_name=account_name,
                account_key=account_key,
                container_name=container_name,
                blob_name=blob_name,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.now(timezone.utc) + timedelta(hours=2),
            )
            if sas:
                return f"{blob_client.url}?{sas}"
        except Exception as exc:
            logger.warning("Failed to generate blob SAS URL, falling back to direct URL: %s", exc)
        return blob_client.url

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

    async def upload_document(self, data, name, document_type: str = "prescription", patient_id: str = "patient"):
        client = self._get_client()
        if not client:
            raise NotImplementedError("Azure Blob not configured")

        try:
            container_name = self._container_for_document_type(document_type)
            container_client = client.get_container_client(container_name)
            try:
                container_client.get_container_properties()
            except Exception:
                container_client.create_container()

            blob_name = self._build_blob_name(patient_id=patient_id, filename=name)
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob(data, overwrite=True)

            url = self._build_read_url(container_name=container_name, blob_name=blob_name, blob_client=blob_client)
            logger.info("Document uploaded to container=%s blob=%s", container_name, blob_name)
            return url
        except Exception as e:
            logger.error(f"Blob upload failed: {e}")
            raise

    async def upload_health_summary_pdf(self, data, name):
        client = self._get_client()
        if not client:
            raise NotImplementedError("Azure Blob not configured")

        try:
            container_name = "exports"
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
