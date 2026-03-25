import logging
from config import get_settings
from agents.contracts import ValidationResult

logger = logging.getLogger("careorbit.services.search")


class SearchResultValidator:
    ALLOWED_INTERACTION_SEVERITIES = {
        "LOW",
        "MODERATE",
        "ELEVATED",
        "HIGH",
        "CRITICAL",
        "CONTRAINDICATED",
    }

    TRUSTED_SOURCES = {
        "fda",
        "nih",
        "rxnav",
        "drugbank",
        "lexicomp",
        "uptodate",
        "curated_rag",
        "guideline_repository",
    }

    @staticmethod
    def _norm(value) -> str:
        return str(value or "").strip().lower()

    def validate_interaction(self, query_rxnorm1: str, query_rxnorm2: str, result: dict) -> ValidationResult:
        errors: list[str] = []

        q1 = self._norm(query_rxnorm1)
        q2 = self._norm(query_rxnorm2)

        r1 = self._norm(result.get("rxnorm1") or result.get("drug1_rxnorm") or result.get("rxnorm_code_1"))
        r2 = self._norm(result.get("rxnorm2") or result.get("drug2_rxnorm") or result.get("rxnorm_code_2"))
        pair = self._norm(result.get("rxnorm_pair"))

        codes = {c for c in [r1, r2] if c}
        if not ({q1, q2}.issubset(codes) or (q1 in pair and q2 in pair)):
            errors.append("Interaction result is not an exact RxNorm pair match")

        severity = str(result.get("severity") or "").strip().upper()
        if severity and severity not in self.ALLOWED_INTERACTION_SEVERITIES:
            errors.append(f"Unexpected severity value: {severity}")

        source = self._norm(result.get("source"))
        if source and source not in self.TRUSTED_SOURCES:
            errors.append(f"Untrusted interaction source: {source}")

        return ValidationResult(valid=(len(errors) == 0), errors=errors)

    def validate_guideline(self, query_icd10: str, result: dict) -> ValidationResult:
        errors: list[str] = []

        query_code = self._norm(query_icd10)
        result_code = self._norm(result.get("icd10") or result.get("icd10_code") or result.get("condition_icd10"))
        if result_code and result_code != query_code:
            errors.append("Guideline result ICD-10 does not exactly match query")

        source = self._norm(result.get("source") or result.get("guideline_source"))
        if source and source not in self.TRUSTED_SOURCES:
            errors.append(f"Untrusted guideline source: {source}")

        interval = result.get("interval_years")
        if interval is not None:
            try:
                parsed = float(interval)
                if parsed <= 0:
                    errors.append("Guideline interval_years must be > 0")
            except Exception:
                errors.append("Guideline interval_years is not numeric")

        screening = str(result.get("screening") or result.get("screening_name") or "").strip()
        if not screening:
            errors.append("Guideline screening name is missing")

        return ValidationResult(valid=(len(errors) == 0), errors=errors)


class AzureSearchService:
    def __init__(self):
        settings = get_settings()
        self._endpoint = settings.AZURE_SEARCH_ENDPOINT
        self._key = settings.AZURE_SEARCH_KEY
        self._index = settings.AZURE_SEARCH_INDEX
        self._client = None
        self.validator = SearchResultValidator()

    @staticmethod
    def _escape_odata(value: str) -> str:
        return str(value or "").replace("'", "''")

    @staticmethod
    def _normalize_rxnorm(value: str) -> str:
        return str(value or "").strip()

    @staticmethod
    def _normalize_icd10(value: str) -> str:
        return str(value or "").strip().upper()

    @staticmethod
    def _doc_to_interaction(result: dict) -> dict:
        return {
            "rxnorm1": result.get("rxnorm1") or result.get("drug1_rxnorm") or result.get("rxnorm_code_1"),
            "rxnorm2": result.get("rxnorm2") or result.get("drug2_rxnorm") or result.get("rxnorm_code_2"),
            "rxnorm_pair": result.get("rxnorm_pair") or "",
            "drug_pair": result.get("drug_pair", ""),
            "severity": result.get("severity", ""),
            "description": result.get("description", ""),
            "mechanism": result.get("mechanism", ""),
            "recommendation": result.get("recommendation", ""),
            "source": result.get("source", ""),
            "score": result.get("@search.score", 0),
        }

    @staticmethod
    def _doc_to_guideline(result: dict) -> dict:
        return {
            "icd10": result.get("icd10") or result.get("icd10_code") or result.get("condition_icd10"),
            "condition": result.get("condition", ""),
            "screening": result.get("screening") or result.get("screening_name") or "",
            "screening_name": result.get("screening_name") or result.get("screening") or "",
            "recommendation": result.get("recommendation", ""),
            "interval_years": result.get("interval_years"),
            "source": result.get("source", ""),
            "guideline_source": result.get("guideline_source") or result.get("source") or "",
            "score": result.get("@search.score", 0),
        }

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
                interactions.append(self._doc_to_interaction(result))
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
                guidelines.append(self._doc_to_guideline(result))
            return guidelines
        except Exception as e:
            logger.error(f"Guideline search failed: {e}")
            raise

    async def find_interaction_exact(self, rxnorm1: str, rxnorm2: str) -> dict | None:
        client = self._get_client()
        if not client:
            raise NotImplementedError("Azure Search not configured")

        r1 = self._normalize_rxnorm(rxnorm1)
        r2 = self._normalize_rxnorm(rxnorm2)
        if not r1 or not r2:
            return None

        filters = [
            (
                "(rxnorm1 eq '{r1}' and rxnorm2 eq '{r2}') or "
                "(rxnorm1 eq '{r2}' and rxnorm2 eq '{r1}')"
            ).format(r1=self._escape_odata(r1), r2=self._escape_odata(r2)),
            (
                "(drug1_rxnorm eq '{r1}' and drug2_rxnorm eq '{r2}') or "
                "(drug1_rxnorm eq '{r2}' and drug2_rxnorm eq '{r1}')"
            ).format(r1=self._escape_odata(r1), r2=self._escape_odata(r2)),
            (
                "search.ismatch('{r1}', 'rxnorm_pair') and search.ismatch('{r2}', 'rxnorm_pair')"
            ).format(r1=self._escape_odata(r1), r2=self._escape_odata(r2)),
        ]

        for query_filter in filters:
            try:
                results = client.search(
                    search_text="*",
                    filter=query_filter,
                    top=1,
                    select=[
                        "rxnorm1",
                        "rxnorm2",
                        "drug1_rxnorm",
                        "drug2_rxnorm",
                        "rxnorm_pair",
                        "drug_pair",
                        "severity",
                        "description",
                        "mechanism",
                        "recommendation",
                        "source",
                    ],
                )
                for result in results:
                    doc = self._doc_to_interaction(result)
                    validation = self.validator.validate_interaction(r1, r2, doc)
                    if validation.valid:
                        return doc
            except Exception as e:
                logger.info(f"Exact interaction search filter failed: {e}")
                continue

        return None

    async def find_guidelines_exact(self, icd10_code: str) -> list[dict]:
        client = self._get_client()
        if not client:
            raise NotImplementedError("Azure Search not configured")

        icd10 = self._normalize_icd10(icd10_code)
        if not icd10:
            return []

        filters = [
            "icd10 eq '{code}'".format(code=self._escape_odata(icd10)),
            "icd10_code eq '{code}'".format(code=self._escape_odata(icd10)),
            "condition_icd10 eq '{code}'".format(code=self._escape_odata(icd10)),
        ]

        matched: list[dict] = []
        for query_filter in filters:
            try:
                results = client.search(
                    search_text="*",
                    filter=query_filter,
                    top=10,
                    select=[
                        "icd10",
                        "icd10_code",
                        "condition_icd10",
                        "condition",
                        "screening",
                        "screening_name",
                        "recommendation",
                        "interval_years",
                        "source",
                        "guideline_source",
                    ],
                )
                for result in results:
                    doc = self._doc_to_guideline(result)
                    validation = self.validator.validate_guideline(icd10, doc)
                    if validation.valid:
                        matched.append(doc)
            except Exception as e:
                logger.info(f"Exact guideline search filter failed: {e}")
                continue

        deduped: dict[tuple, dict] = {}
        for item in matched:
            key = (
                str(item.get("icd10") or "").upper(),
                str(item.get("screening_name") or item.get("screening") or "").strip().lower(),
            )
            if key not in deduped:
                deduped[key] = item

        return list(deduped.values())
