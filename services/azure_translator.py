class AzureTranslatorService:
    async def translate(self, text, target_lang, source_lang=None):
        raise NotImplementedError("Azure Translator not configured")

    async def detect_language(self, text):
        raise NotImplementedError("Azure Translator not configured")
