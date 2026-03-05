from services.azure_openai import AzureOpenAIService
from services.azure_search import AzureSearchService
from services.azure_translator import AzureTranslatorService
from db.session import async_session as db_session

openai_service = AzureOpenAIService()
search_service = AzureSearchService()
translator_service = AzureTranslatorService()


class OrchestratorResponse:
    def __init__(self, **kwargs):
        self.message = kwargs.get("message", "")
        self.language = kwargs.get("language", "en")
        self.agents_used = kwargs.get("agents_used", [])
        self.alerts = kwargs.get("alerts", [])
        self.care_gaps = kwargs.get("care_gaps", [])
        self.recommendations = kwargs.get("recommendations", [])
        self.confidence = kwargs.get("confidence", 0.0)


class Orchestrator:
    MEDICATION_KEYWORDS = ["medication", "medicine", "drug", "prescription", "dosage", "tablet", "pill"]
    CARE_GAP_KEYWORDS = ["screening", "checkup", "care gap", "preventive", "immunization", "vaccination"]
    HISTORY_KEYWORDS = ["history", "overview", "summary", "record", "past"]

    def __init__(self):
        import sys
        mod = sys.modules[__name__]
        self._openai = mod.openai_service
        self._search = mod.search_service
        self._translator = mod.translator_service

    async def process_query(self, patient_id: str, message: str, language: str = "en") -> OrchestratorResponse:
        query = message
        if language and language != "en":
            query = await self._translator.translate(message, "en", source=language)

        agents_used = self._route_to_agents(query)

        guidelines = await self._search.search_guidelines(query)
        interactions = await self._search.search_drug_interactions(query)

        ai_response = await self._openai.chat([
            {"role": "system", "content": "You are CareOrbit health assistant."},
            {"role": "user", "content": query}
        ])

        response_text = ai_response if isinstance(ai_response, str) else str(ai_response)
        response_text = f"Based on your health data: {response_text}"

        if language and language != "en":
            response_text = await self._translator.translate(response_text, language)

        return OrchestratorResponse(
            message=response_text,
            language=language,
            agents_used=agents_used,
            alerts=interactions if isinstance(interactions, list) else [],
            care_gaps=guidelines if isinstance(guidelines, list) else [],
            confidence=0.80,
        )

    def _route_to_agents(self, query: str) -> list:
        query_lower = query.lower()
        agents = []

        if any(kw in query_lower for kw in self.MEDICATION_KEYWORDS):
            agents.append("medication_agent")
        if any(kw in query_lower for kw in self.CARE_GAP_KEYWORDS):
            agents.append("care_gap_agent")
        if any(kw in query_lower for kw in self.HISTORY_KEYWORDS):
            agents.extend(["medication_agent", "care_gap_agent", "history_agent"])

        if not agents:
            agents = ["medication_agent", "care_gap_agent", "history_agent"]

        return list(dict.fromkeys(agents))


orchestrator = Orchestrator()
