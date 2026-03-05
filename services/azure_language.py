class AzureLanguageService:
    async def recognize_health_entities(self, text):
        raise NotImplementedError("Azure Language not configured")

    async def recognize_entities(self, text):
        raise NotImplementedError("Azure Language not configured")
