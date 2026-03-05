class AzureOpenAIService:
    async def extract_structured_data(self, text, doc_type):
        raise NotImplementedError("Azure OpenAI not configured")

    async def chat(self, messages):
        raise NotImplementedError("Azure OpenAI not configured")

    async def chat_with_history(self, messages, context=None):
        raise NotImplementedError("Azure OpenAI not configured")
