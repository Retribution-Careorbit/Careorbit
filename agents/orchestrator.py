import logging
import re
import asyncio
from dataclasses import asdict, is_dataclass

from config import get_settings
from services.azure_openai import AzureOpenAIService
from services.azure_search import AzureSearchService
from services.azure_translator import AzureTranslatorService
from graph.phig_builder import phig_builder
from agents.medication_agent import MedicationAgent
from agents.care_gap_agent import CareGapAgent
from agents.history_agent import GraphHistoryAgent
from db.session import async_session as db_session

openai_service = AzureOpenAIService()
search_service = AzureSearchService()
translator_service = AzureTranslatorService()
logger = logging.getLogger("careorbit.agents.orchestrator")


class OrchestratorResponse:
    def __init__(self, **kwargs):
        self.message = kwargs.get("message", "")
        self.language = kwargs.get("language", "en")
        self.agents_used = kwargs.get("agents_used", [])
        self.alerts = kwargs.get("alerts", [])
        self.care_gaps = kwargs.get("care_gaps", [])
        self.recommendations = kwargs.get("recommendations", [])
        self.confidence = kwargs.get("confidence", 0.0)


class AzureDependencyUnavailable(Exception):
    def __init__(self, failures: list[dict]):
        super().__init__("Azure dependencies unavailable")
        self.failures = failures


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
        self._settings = get_settings()

    async def _translate_best_effort(self, text: str, target_lang: str, source_lang: str = None) -> str:
        if not text:
            return text
        try:
            if source_lang:
                return await self._translator.translate(text, target_lang, source=source_lang)
            return await self._translator.translate(text, target_lang)
        except Exception as exc:
            logger.info(f"Translator unavailable; returning original text: {exc}")
            return text

    def _raise_if_strict_failures(self, failures: list[dict]):
        if failures and self._settings.CHAT_STRICT_AZURE_DEPENDENCIES:
            raise AzureDependencyUnavailable(failures)

    @staticmethod
    def _dedupe_interactions(interactions: list) -> list:
        if not isinstance(interactions, list):
            return []

        seen = set()
        unique = []
        for ix in interactions:
            if not isinstance(ix, dict):
                continue
            key = (
                (ix.get("drug_pair") or "").strip().lower(),
                (ix.get("severity") or "").strip().lower(),
                (ix.get("description") or "").strip().lower(),
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(ix)
        return unique

    async def _collect_phig_context(self, patient_id: str) -> dict:
        try:
            graph = await phig_builder.get_full_patient_graph(patient_id)
        except Exception as exc:
            logger.warning(f"Failed to fetch PHIG graph for {patient_id}: {exc}")
            graph = {}

        medications = graph.get("medications", []) if isinstance(graph, dict) else []
        conditions = graph.get("conditions", []) if isinstance(graph, dict) else []
        labs = graph.get("labs", []) if isinstance(graph, dict) else []
        care_gaps = graph.get("care_gaps", []) if isinstance(graph, dict) else []

        interactions = graph.get("interactions", []) if isinstance(graph, dict) else []
        if not interactions and medications:
            for med in medications:
                for ix in med.get("interactions", []) or []:
                    if isinstance(ix, dict):
                        interactions.append(ix)

        return {
            "summary": graph.get("summary", {}) if isinstance(graph, dict) else {},
            "medications": medications if isinstance(medications, list) else [],
            "conditions": conditions if isinstance(conditions, list) else [],
            "labs": labs if isinstance(labs, list) else [],
            "care_gaps": care_gaps if isinstance(care_gaps, list) else [],
            "interactions": self._dedupe_interactions(interactions),
        }

    @staticmethod
    def _result_to_dict(value):
        if is_dataclass(value):
            return asdict(value)
        if isinstance(value, dict):
            return value
        return {"value": value}

    async def _run_selected_agents(self, patient_id: str, agents_used: list[str], language: str) -> dict:
        jobs = []
        labels = []

        if "medication_agent" in agents_used:
            labels.append("medication_agent")
            jobs.append(
                MedicationAgent(
                    patient_id=patient_id,
                    requesting_user_id=patient_id,
                    search_client=self._search,
                ).run()
            )

        if "care_gap_agent" in agents_used:
            labels.append("care_gap_agent")
            jobs.append(
                CareGapAgent(
                    patient_id=patient_id,
                    requesting_user_id=patient_id,
                    search_client=self._search,
                ).run()
            )

        if "history_agent" in agents_used:
            labels.append("history_agent")
            jobs.append(
                GraphHistoryAgent(
                    openai_client=self._openai,
                    translator=self._translator,
                ).run(patient_id=patient_id, language=language or "en")
            )

        if not jobs:
            return {
                "interactions": [],
                "care_gaps": [],
                "history": None,
                "failures": [],
            }

        results = await asyncio.gather(*jobs, return_exceptions=True)

        interactions = []
        care_gaps = []
        history = None
        failures = []

        for idx, result in enumerate(results):
            label = labels[idx]
            if isinstance(result, Exception):
                failures.append({"agent": label, "reason": str(result)})
                continue

            if label == "medication_agent":
                for item in result or []:
                    data = self._result_to_dict(item)
                    interactions.append(
                        {
                            "drug_pair": f"{data.get('drug1_name', '')} + {data.get('drug2_name', '')}".strip(" +"),
                            "severity": data.get("escalated_severity") or data.get("base_severity") or "",
                            "description": data.get("description") or "",
                            "recommendation": data.get("recommendation") or "",
                            "source": data.get("source") or "curated_rag",
                            "metadata": data.get("metadata") or {},
                        }
                    )

            elif label == "care_gap_agent":
                for item in result or []:
                    data = self._result_to_dict(item)
                    care_gaps.append(
                        {
                            "condition": data.get("condition") or "",
                            "screening": data.get("screening") or "",
                            "name": data.get("screening") or "Care gap",
                            "overdue_years": data.get("overdue_years") or 0,
                            "guideline": data.get("guideline") or "",
                            "recommendation": data.get("recommendation") or "",
                            "metadata": data.get("metadata") or {},
                        }
                    )

            elif label == "history_agent":
                history = self._result_to_dict(result)

        return {
            "interactions": interactions,
            "care_gaps": care_gaps,
            "history": history,
            "failures": failures,
        }

    def _build_grounded_text(self, query: str, phig: dict) -> str:
        query_lower = (query or "").lower()
        medications = phig.get("medications", [])
        conditions = phig.get("conditions", [])
        labs = phig.get("labs", [])
        interactions = phig.get("interactions", [])
        care_gaps = phig.get("care_gaps", [])

        med_lines = []
        for med in medications:
            name = med.get("name", "Unknown")
            dose = med.get("dosage") or ""
            freq = med.get("frequency") or ""
            med_lines.append(f"{name} ({dose}, {freq})")

        if any(k in query_lower for k in ["medication", "medicine", "drug", "tablet", "pill", "prescription"]):
            if med_lines:
                return "Current medications from your PHIG profile: " + "; ".join(med_lines) + "."
            return "No medications are currently present in your PHIG profile."

        if any(k in query_lower for k in ["interaction", "interactions"]):
            if interactions:
                items = []
                for ix in interactions:
                    pair = ix.get("drug_pair") or "Unknown pair"
                    severity = ix.get("severity") or "unknown severity"
                    items.append(f"{pair} ({severity})")
                return "Medication interaction alerts from your PHIG profile: " + "; ".join(items) + "."
            return "No medication interaction alerts are currently present in your PHIG profile."

        if any(k in query_lower for k in ["screening", "care gap", "checkup", "preventive", "immunization", "vaccination"]):
            if care_gaps:
                names = [cg.get("name", "Unnamed care gap") for cg in care_gaps]
                return "Open care gaps from your PHIG profile: " + ", ".join(names) + "."
            return "No open care gaps are currently present in your PHIG profile."

        if any(k in query_lower for k in ["history", "overview", "summary", "record", "past"]):
            cond_names = [c.get("name", "Unknown") for c in conditions]
            lab_lines = [f"{l.get('name', 'Unknown')}: {l.get('value', '')} {l.get('unit', '')}" for l in labs[:5]]
            parts = [
                f"PHIG summary: {len(medications)} medication(s)",
                f"{len(conditions)} condition(s)",
                f"{len(labs)} lab value(s)",
                f"{len(interactions)} interaction alert(s)",
            ]
            if cond_names:
                parts.append("Conditions: " + ", ".join(cond_names))
            if lab_lines:
                parts.append("Recent labs: " + "; ".join(lab_lines))
            return ". ".join(parts) + "."

        if medications:
            return (
                f"Your PHIG profile currently has {len(medications)} medication(s), "
                f"{len(interactions)} interaction alert(s), and {len(care_gaps)} care gap(s). "
                "Ask for medications, interactions, care gaps, or a full history summary."
            )

        return "No PHIG clinical data is currently available for this profile yet."

    @staticmethod
    def _collect_grounding_terms(phig: dict) -> set[str]:
        terms: set[str] = set()

        for med in phig.get("medications", []) or []:
            name = str(med.get("name") or "").strip().lower()
            if name:
                terms.add(name)

        for condition in phig.get("conditions", []) or []:
            name = str(condition.get("name") or "").strip().lower()
            if name:
                terms.add(name)

        for lab in phig.get("labs", []) or []:
            name = str(lab.get("name") or "").strip().lower()
            if name:
                terms.add(name)

        for interaction in phig.get("interactions", []) or []:
            pair = str(interaction.get("drug_pair") or "").strip().lower()
            if pair:
                for token in pair.split("+"):
                    token = token.strip()
                    if token:
                        terms.add(token)

        return terms

    def _passes_grounding_verifier(self, query: str, ai_text: str, phig: dict) -> bool:
        if not ai_text or not ai_text.strip():
            return False

        clinical_query = bool(re.search(r"medication|medicine|drug|condition|diagnosis|lab|interaction|screening|care gap", query or "", re.I))
        if not clinical_query:
            return True

        grounding_terms = self._collect_grounding_terms(phig)
        if not grounding_terms:
            return False

        ai_text_lower = ai_text.lower()
        return any(term in ai_text_lower for term in grounding_terms)

    async def build_grounded_response(self, patient_id: str, message: str, language: str = "en") -> OrchestratorResponse:
        query = message or ""
        if language and language != "en":
            query = await self._translate_best_effort(message, "en", source_lang=language)

        agents_used = self._route_to_agents(query)
        phig = await self._collect_phig_context(patient_id)
        response_text = self._build_grounded_text(query, phig)

        if language and language != "en":
            response_text = await self._translate_best_effort(response_text, language)

        return OrchestratorResponse(
            message=response_text,
            language=language,
            agents_used=agents_used,
            alerts=phig.get("interactions", []),
            care_gaps=phig.get("care_gaps", []),
            confidence=0.72,
        )

    async def process_query(self, patient_id: str, message: str, language: str = "en") -> OrchestratorResponse:
        query = message or ""
        failures = []

        if language and language != "en":
            translated = await self._translate_best_effort(message, "en", source_lang=language)
            if translated == message and self._settings.CHAT_REQUIRE_TRANSLATOR_FOR_NON_EN:
                failures.append({
                    "service": "azure_translator",
                    "operation": "translate_to_english",
                    "reason": "Translator unavailable for non-English request",
                })
                self._raise_if_strict_failures(failures)
            query = translated

        agents_used = self._route_to_agents(query)

        agent_outputs = await self._run_selected_agents(patient_id=patient_id, agents_used=agents_used, language=language)

        phig = await self._collect_phig_context(patient_id)
        grounded_text = self._build_grounded_text(query, phig)

        guidelines = []
        interactions = list(phig.get("interactions", []))
        interactions.extend(agent_outputs.get("interactions", []))
        interactions = self._dedupe_interactions(interactions)
        computed_care_gaps = list(phig.get("care_gaps", []))
        computed_care_gaps.extend(agent_outputs.get("care_gaps", []))
        ai_response = None

        try:
            guidelines = await self._search.search_guidelines(query)
        except Exception as exc:
            logger.info(f"Guideline search unavailable: {exc}")
            if self._settings.CHAT_REQUIRE_SEARCH:
                failures.append({
                    "service": "azure_search",
                    "operation": "search_guidelines",
                    "reason": str(exc),
                })

        try:
            search_interactions = await self._search.search_drug_interactions(query)
            if isinstance(search_interactions, list):
                interactions.extend(search_interactions)
                interactions = self._dedupe_interactions(interactions)
        except Exception as exc:
            logger.info(f"Interaction search unavailable: {exc}")
            if self._settings.CHAT_REQUIRE_SEARCH:
                failures.append({
                    "service": "azure_search",
                    "operation": "search_drug_interactions",
                    "reason": str(exc),
                })

        try:
            ai_response = await self._openai.chat([
                {
                    "role": "system",
                    "content": (
                        "You are CareOrbit health assistant."
                        "Ground every answer in provided PHIG data."
                        "Do not invent medications, conditions, labs, or interactions."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"User query: {query}\n"
                        f"PHIG summary: {phig.get('summary', {})}\n"
                        f"Medications: {phig.get('medications', [])}\n"
                        f"Conditions: {phig.get('conditions', [])}\n"
                        f"Labs: {phig.get('labs', [])}\n"
                        f"Care gaps: {computed_care_gaps}\n"
                        f"History delta: {agent_outputs.get('history') or {}}\n"
                        f"Interaction alerts: {interactions}\n"
                        "Return concise, actionable guidance.")
                },
            ])
        except Exception as exc:
            logger.info(f"OpenAI chat unavailable; returning grounded PHIG response: {exc}")
            if self._settings.CHAT_REQUIRE_OPENAI:
                failures.append({
                    "service": "azure_openai",
                    "operation": "chat",
                    "reason": str(exc),
                })

        self._raise_if_strict_failures(failures)

        if ai_response:
            ai_text = ai_response if isinstance(ai_response, str) else str(ai_response)
            if self._passes_grounding_verifier(query=query, ai_text=ai_text, phig=phig):
                response_text = f"{grounded_text}\n\nAdditional guidance: {ai_text}"
                confidence = 0.84
            else:
                response_text = grounded_text
                confidence = 0.75
        else:
            response_text = grounded_text
            confidence = 0.72

        history = agent_outputs.get("history") or {}
        narrative = str(history.get("narrative_text") or "").strip()
        if narrative:
            response_text = f"{response_text}\n\nHistory narrative: {narrative}"

        if language and language != "en":
            response_text = await self._translate_best_effort(response_text, language)

        for failure in agent_outputs.get("failures", []):
            logger.info(f"Agent execution skipped: {failure}")

        return OrchestratorResponse(
            message=response_text,
            language=language,
            agents_used=agents_used,
            alerts=interactions if isinstance(interactions, list) else [],
            care_gaps=(guidelines if isinstance(guidelines, list) and guidelines else computed_care_gaps),
            confidence=confidence,
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
