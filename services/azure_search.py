import logging
from config import get_settings

logger = logging.getLogger("careorbit.services.search")


class AzureSearchService:
    def __init__(self):
        settings = get_settings()
        self._endpoint = settings.AZURE_SEARCH_ENDPOINT
        self._key = settings.AZURE_SEARCH_KEY
        self._index = settings.AZURE_SEARCH_INDEX
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not self._endpoint or not self._key:
            return None
        try:
            from azure.search.documents import SearchClient
            from azure.core.credentials import AzureKeyCredential
            self._client = SearchClient(
                endpoint=self._endpoint,
                index_name=self._index,
                credential=AzureKeyCredential(self._key),
            )
            return self._client
        except Exception as e:
            logger.warning(f"Failed to initialize Azure Search client: {e}")
            return None

    async def search_drug_interactions(self, drug_name):
        client = self._get_client()
        if not client:
            raise NotImplementedError("Azure Search not configured")

        try:
            results = client.search(
                search_text=f"drug interaction {drug_name}",
                top=10,
                select=["drug_pair", "severity", "description", "mechanism"],
            )
            interactions = []
            for result in results:
                interactions.append({
                    "drug_pair": result.get("drug_pair", ""),
                    "severity": result.get("severity", ""),
                    "description": result.get("description", ""),
                    "mechanism": result.get("mechanism", ""),
                    "score": result.get("@search.score", 0),
                })
            return interactions
        except Exception as e:
            logger.error(f"Drug interaction search failed: {e}")
            raise

    async def search_guidelines(self, condition):
        client = self._get_client()
        if not client:
            raise NotImplementedError("Azure Search not configured")

        try:
            results = client.search(
                search_text=f"clinical guideline {condition}",
                top=5,
                select=["condition", "screening", "recommendation", "source"],
            )
            guidelines = []
            for result in results:
                guidelines.append({
                    "condition": result.get("condition", ""),
                    "screening": result.get("screening", ""),
                    "recommendation": result.get("recommendation", ""),
                    "source": result.get("source", ""),
                    "score": result.get("@search.score", 0),
                })
            return guidelines
        except Exception as e:
            logger.error(f"Guideline search failed: {e}")
            raise
