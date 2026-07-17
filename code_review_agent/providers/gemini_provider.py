from typing import Any
from providers.base_provider import BaseProviderAdapter
from langchain_google_genai import ChatGoogleGenerativeAI

class GeminiProviderAdapter(BaseProviderAdapter):
    """Adapter for Google Gemini via LangChain's ChatGoogleGenerativeAI client."""
    def __init__(self, api_key: str, model: str, temperature: float = 0.1, timeout: float = 30.0, **kwargs):
        # LangChain uses api_key (sometimes google_api_key is supported too)
        self.client = ChatGoogleGenerativeAI(
            model=model,
            api_key=api_key,
            temperature=temperature,
            timeout=timeout,
            **kwargs
        )

    def invoke(self, input_data: Any, **kwargs: Any) -> Any:
        # Support dynamic temperature overriding
        temp = kwargs.pop("temperature", None)
        if temp is not None:
            self.client.temperature = temp
        return self.client.invoke(input_data, **kwargs)

    async def ainvoke(self, input_data: Any, **kwargs: Any) -> Any:
        # Support dynamic temperature overriding
        temp = kwargs.pop("temperature", None)
        if temp is not None:
            self.client.temperature = temp
        return await self.client.ainvoke(input_data, **kwargs)
