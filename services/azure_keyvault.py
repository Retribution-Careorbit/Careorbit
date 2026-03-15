import logging
from config import get_settings
import os

logger = logging.getLogger("careorbit.services.keyvault")


class AzureKeyVaultService:
    def __init__(self):
        self._uri = os.environ.get("AZURE_KEYVAULT_URI", "")
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not self._uri:
            return None
        try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.secrets import SecretClient
            credential = DefaultAzureCredential()
            self._client = SecretClient(vault_url=self._uri, credential=credential)
            return self._client
        except Exception as e:
            logger.warning(f"Failed to initialize Key Vault client: {e}")
            return None

    async def get_secret(self, name):
        client = self._get_client()
        if not client:
            raise NotImplementedError("Azure Key Vault not configured")

        try:
            secret = client.get_secret(name)
            return secret.value
        except Exception as e:
            logger.error(f"Failed to get secret {name}: {e}")
            raise
